from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from .ai_reviewer import ai_code_review


# Create FastAPI app
app = FastAPI(title="Codexa – AI Code Reviewer")

# ---- CORS middleware (for React frontend on port 5173) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeInput(BaseModel):
    filename: str | None = None
    language: str = "python"
    code: str


@app.get("/")
def root():
    return {"message": "Codexa backend is running ⚡"}


@app.post("/api/review")
def review(payload: CodeInput):
    result = ai_code_review(payload.code, payload.language or "python")
    return result
