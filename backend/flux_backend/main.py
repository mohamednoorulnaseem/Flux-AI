"""
Flux — Main FastAPI Application

Full SaaS API with:
  • JWT Authentication (signup/login/me)
  • Multi-Agent Code Review Pipeline (standard + SSE streaming)
  • Review History & Analytics
  • Dashboard Statistics
  • Health Check
"""
import json
import time
import queue
import threading
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .config import settings
from .auth import (
    SignupRequest, LoginRequest, TokenResponse,
    signup_user, login_user,
    get_current_user, get_optional_user,
)
from .orchestrator import run_orchestrator
from .database import (
    create_review, get_reviews_by_user, get_review_by_id,
    get_user_stats, update_user_reviews_used, delete_review,
    init_db,
)

# ─── App Setup ──────────────────────────────────────────

app = FastAPI(
    title="Flux – AI Code Reviewer",
    description="End-to-end Agentic AI Code Review SaaS Platform",
    version=settings.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Ensure DB is initialized
init_db()


# ─── Request/Response Models ───────────────────────────

class CodeReviewRequest(BaseModel):
    filename: str = "untitled"
    language: str = "python"
    code: str
    project_id: int | None = None


class ReviewResponse(BaseModel):
    id: int | None = None
    issues: list
    summary: str
    score: int
    grade: str = ""
    fixed_code: str = ""
    changes_made: list = []
    agent_results: dict = {}
    metrics: dict = {}
    quick_wins: list = []
    metadata: dict = {}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HEALTH & INFO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/")
def root():
    return {
        "service": "Flux AI Code Reviewer",
        "version": settings.APP_VERSION,
        "status": "operational",
        "agents": [
            "SecurityAgent", "PerformanceAgent",
            "StyleAgent", "BugDetectorAgent", "AutoFixAgent"
        ],
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTHENTICATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/auth/signup", response_model=TokenResponse)
def signup(req: SignupRequest):
    """Register a new user account."""
    return signup_user(req)


@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Login with email and password."""
    return login_user(req)


@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"],
        "full_name": user["full_name"],
        "plan": user["plan"],
        "reviews_used": user["reviews_used"],
        "reviews_limit": user["reviews_limit"],
        "created_at": user["created_at"],
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CODE REVIEW (Standard JSON endpoint)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/review")
def review_code(payload: CodeReviewRequest, user: dict | None = Depends(get_optional_user)):
    """
    Run the full multi-agent code review pipeline.
    Works for both authenticated and anonymous users.
    Authenticated users get their reviews saved to history.
    """
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    # Check rate limit for authenticated users
    if user and user["reviews_used"] >= user["reviews_limit"]:
        raise HTTPException(
            status_code=429,
            detail=f"Review limit reached ({user['reviews_limit']}). Upgrade your plan."
        )

    # Run the orchestrator pipeline
    result = run_orchestrator(payload.code, payload.language or "python")

    review_id = None

    # Save review for authenticated users
    if user:
        saved = create_review(
            user_id=user["id"],
            filename=payload.filename or "untitled",
            language=payload.language or "python",
            code=payload.code,
            issues=result["issues"],
            summary=result["summary"],
            score=result["score"],
            agent_results=result["agent_results"],
            fixed_code=result.get("fixed_code", ""),
            processing_time_ms=result["metadata"]["processing_time_ms"],
            project_id=payload.project_id,
        )
        review_id = saved["id"]
        update_user_reviews_used(user["id"])

    return {
        "id": review_id,
        **result,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CODE REVIEW (SSE Streaming endpoint)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/review/stream")
def review_code_stream(payload: CodeReviewRequest, user: dict | None = Depends(get_optional_user)):
    """
    Run the multi-agent pipeline with Server-Sent Events (SSE) streaming.
    Sends real-time progress updates as each agent starts/completes.

    SSE Event Types:
      - agent_start: An agent has started running
      - agent_complete: An agent has finished
      - agent_error: An agent encountered an error
      - result: The final complete result (JSON)
    """
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    if user and user["reviews_used"] >= user["reviews_limit"]:
        raise HTTPException(
            status_code=429,
            detail=f"Review limit reached ({user['reviews_limit']}). Upgrade your plan."
        )

    # Use a thread-safe queue for SSE events
    event_queue = queue.Queue()

    def progress_callback(event: dict):
        """Called by the orchestrator as agents progress."""
        event_queue.put(event)

    def run_pipeline():
        """Run the orchestrator in a background thread."""
        try:
            result = run_orchestrator(
                payload.code,
                payload.language or "python",
                progress_callback=progress_callback,
            )

            # Save for authenticated users
            review_id = None
            if user:
                saved = create_review(
                    user_id=user["id"],
                    filename=payload.filename or "untitled",
                    language=payload.language or "python",
                    code=payload.code,
                    issues=result["issues"],
                    summary=result["summary"],
                    score=result["score"],
                    agent_results=result["agent_results"],
                    fixed_code=result.get("fixed_code", ""),
                    processing_time_ms=result["metadata"]["processing_time_ms"],
                    project_id=payload.project_id,
                )
                review_id = saved["id"]
                update_user_reviews_used(user["id"])

            result["id"] = review_id
            event_queue.put({"type": "result", "data": result})
        except Exception as e:
            event_queue.put({"type": "error", "data": {"message": str(e)}})
        finally:
            event_queue.put(None)  # Sentinel to end stream

    # Start pipeline in background thread
    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    def event_generator():
        """Generate SSE events from the queue."""
        while True:
            try:
                event = event_queue.get(timeout=120)  # 2 min timeout
            except queue.Empty:
                yield "event: timeout\ndata: {}\n\n"
                break

            if event is None:
                break  # Pipeline finished

            # Format as SSE
            if event.get("type") == "result":
                yield f"event: result\ndata: {json.dumps(event['data'])}\n\n"
            elif event.get("type") == "error":
                yield f"event: error\ndata: {json.dumps(event['data'])}\n\n"
            else:
                # Agent progress events
                agent = event.get("agent", "unknown")
                status = event.get("status", "unknown")
                evt_type = f"agent_{status}"
                yield f"event: {evt_type}\ndata: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  REVIEW HISTORY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/reviews")
def list_reviews(limit: int = 20, offset: int = 0,
                 user: dict = Depends(get_current_user)):
    """Get paginated review history for authenticated user."""
    reviews = get_reviews_by_user(user["id"], limit=limit, offset=offset)
    return {
        "reviews": reviews,
        "total": len(reviews),
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/reviews/{review_id}")
def get_review(review_id: int, user: dict = Depends(get_current_user)):
    """Get a specific review by ID."""
    review = get_review_by_id(review_id, user["id"])
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


@app.delete("/api/reviews/{review_id}")
def remove_review(review_id: int, user: dict = Depends(get_current_user)):
    """Delete a review."""
    success = delete_review(review_id, user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Review not found")
    return {"message": "Review deleted successfully"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  DASHBOARD & ANALYTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    """Get dashboard statistics and analytics."""
    stats = get_user_stats(user["id"])
    return {
        "user": {
            "username": user["username"],
            "email": user["email"],
            "plan": user["plan"],
            "reviews_used": user["reviews_used"],
            "reviews_limit": user["reviews_limit"],
        },
        "stats": stats,
    }
