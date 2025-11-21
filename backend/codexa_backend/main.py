from fastapi import FastAPI
from pydantic import BaseModel
from .ai_reviewer import ai_code_review   # ← this line

app = FastAPI(title="Codexa - AI Code Reviewer")

class CodeInput(BaseModel):
    filename: str | None = None
    language: str | None = "python"
    code: str

@app.get("/")
def root():
    return {"message": "Codexa backend is running 🎉"}

@app.post("/api/review")
def review(payload: CodeInput):
    result = ai_code_review(payload.code, payload.language or "python")
    return result
