"""
Flux — Main FastAPI Application

Multi-Agent Code Review Pipeline with:
  • Standard JSON review endpoint
  • SSE streaming review endpoint
  • Health check
"""
import json
import queue
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .config import settings
from .orchestrator import run_orchestrator

# ─── App Setup ──────────────────────────────────────────

app = FastAPI(
    title="Flux – AI Code Reviewer",
    description="Multi-agent AI code review pipeline",
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


# ─── Request/Response Models ───────────────────────────

class CodeReviewRequest(BaseModel):
    filename: str = "untitled"
    language: str = "python"
    code: str


class ReviewResponse(BaseModel):
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
#  CODE REVIEW (Standard JSON endpoint)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/review", response_model=ReviewResponse)
def review_code(payload: CodeReviewRequest):
    """Run the full multi-agent code review pipeline."""
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty")

    result = run_orchestrator(payload.code, payload.language or "python")
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  CODE REVIEW (SSE Streaming endpoint)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/review/stream")
def review_code_stream(payload: CodeReviewRequest):
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

    event_queue = queue.Queue()

    def progress_callback(event: dict):
        event_queue.put(event)

    def run_pipeline():
        try:
            result = run_orchestrator(
                payload.code,
                payload.language or "python",
                progress_callback=progress_callback,
            )
            event_queue.put({"type": "result", "data": result})
        except Exception as e:
            event_queue.put({"type": "error", "data": {"message": str(e)}})
        finally:
            event_queue.put(None)  # Sentinel to end stream

    thread = threading.Thread(target=run_pipeline, daemon=True)
    thread.start()

    def event_generator():
        while True:
            try:
                event = event_queue.get(timeout=120)
            except queue.Empty:
                yield "event: timeout\ndata: {}\n\n"
                break

            if event is None:
                break

            if event.get("type") == "result":
                yield f"event: result\ndata: {json.dumps(event['data'])}\n\n"
            elif event.get("type") == "error":
                yield f"event: error\ndata: {json.dumps(event['data'])}\n\n"
            else:
                evt_type = f"agent_{event.get('status', 'unknown')}"
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
