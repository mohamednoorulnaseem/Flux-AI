"""
Flux AI Reviewer — Legacy compatibility module.
Now powered by the multi-agent orchestrator pipeline.
"""
from .orchestrator import run_orchestrator


def ai_code_review(code: str, language: str = "python") -> dict:
    """
    Legacy function maintained for backward compatibility.
    Now delegates to the full multi-agent orchestrator.
    """
    result = run_orchestrator(code, language)
    return {
        "issues": result["issues"],
        "summary": result["summary"],
        "score": result["score"],
        "fixed_code": result.get("fixed_code", ""),
        "agent_results": result.get("agent_results", {}),
        "metadata": result.get("metadata", {}),
    }
