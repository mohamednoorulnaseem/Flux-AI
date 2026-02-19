"""
Flux Agents — Specialized AI agents for multi-agent code review pipeline.

Each agent is an expert in a specific domain:
  • SecurityAgent    — Detects vulnerabilities (SQL injection, XSS, secrets, etc.)
  • PerformanceAgent — Finds bottlenecks, complexity, memory issues
  • StyleAgent       — Enforces coding standards & best practices
  • BugDetectorAgent — Finds logic errors, edge cases, type issues
  • AutoFixAgent     — Generates corrected code with all fixes applied
"""
import os
import json
import re
import time
import logging
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

# Load .env from project root (two levels up from this file: backend/flux_backend/ → project root)
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

AI_MODEL = os.getenv("AI_MODEL", "gpt-4.1-mini")

logger = logging.getLogger(__name__)


def _use_local_model() -> bool:
    """Read USE_LOCAL_MODEL at call time so .env changes take effect after restart."""
    return os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"

# ── OpenAI client (lazy-init) ────────────────────────────────────────────────
_openai_client = None


def _get_openai_client():
    """Get or create the OpenAI client (lazy init)."""
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Set it in a .env file or use the local model (USE_LOCAL_MODEL=true)."
            )
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI API and return raw text response."""
    try:
        client = _get_openai_client()
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        text = response.choices[0].message.content or ""
        fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()
        return text
    except Exception as e:
        logger.error(f"OpenAI call failed: {e}")
        return json.dumps({"error": str(e)})


def _str_to_issues(text: str, fix_key: str = "fix") -> list:
    """Convert a freeform string from the local model into a list of issue dicts."""
    if not text or text.strip().lower() in ("none", "none detected.", "none detected", "n/a", ""):
        return []
    # Already a list
    if isinstance(text, list):
        return text
    # Split on sentence boundaries / severity keywords to get individual issues
    parts = re.split(r"\.\s+(?=[A-Z])|(?<=\.)\s+(?=CRITICAL|HIGH|MEDIUM|LOW|WARNING)", text)
    issues = []
    for part in parts:
        part = part.strip().rstrip(".")
        if not part:
            continue
        sev = "medium"
        for s in ("critical", "high", "medium", "low"):
            if s in part.lower():
                sev = s
                break
        issues.append({"line": 0, "severity": sev, "description": part, fix_key: "See description"})
    return issues


def _call_local(system_prompt: str, user_prompt: str) -> str:
    """
    Call the local fine-tuned model.
    The model outputs its natural review format: {bugs, improvements, performance, security, score}.
    We detect which agent is calling and remap the output to the expected schema.
    """
    try:
        from .local_llm import LocalLLM
        llm = LocalLLM.get_instance()

        # Extract just the code from the user_prompt (between ``` fences)
        code_match = re.search(r"```[a-z]*\n(.*?)```", user_prompt, re.DOTALL)
        code = code_match.group(1).strip() if code_match else user_prompt

        instruction = (
            "Review this code. Identify bugs, security vulnerabilities, performance issues, "
            "and style problems. Return a JSON object with keys: "
            "bugs (list of {line, description, severity, fix}), "
            "security (list of {line, type, severity, description, fix}), "
            "performance (list of {line, description, severity, optimization}), "
            "style (list of {line, description, severity, suggestion}), "
            "score (0-100 integer, higher is better)."
        )
        raw = llm.generate(instruction=instruction, code=code, max_new_tokens=768)

        fence_match = re.search(r"```(?:json)?\s*(.*?)```", raw, re.DOTALL)
        if fence_match:
            raw = fence_match.group(1).strip()

        parsed = json.loads(raw)

        # Detect which agent is calling based on the system_prompt keyword
        sp = system_prompt.lower()
        if "security" in sp or "vulnerabilit" in sp:
            items = _str_to_issues(parsed.get("security", []), "fix")
            return json.dumps({
                "vulnerabilities": [{"line": v.get("line", 0), "severity": v.get("severity", "medium"),
                    "type": v.get("type", "vulnerability"), "cwe": "", "description": v.get("description", ""),
                    "impact": "", "fix": v.get("fix", "")} for v in items],
                "security_score": max(0, 100 - len(items) * 15),
                "risk_level": "high" if items else "none",
                "summary": f"Found {len(items)} security issue(s)." if items else "No security issues found."
            })
        elif "performance" in sp or "bottleneck" in sp or "complexity" in sp:
            items = _str_to_issues(parsed.get("performance", []), "optimization")
            return json.dumps({
                "issues": [{"line": v.get("line", 0), "severity": v.get("severity", "medium"),
                    "type": "performance", "description": v.get("description", ""),
                    "optimization": v.get("optimization", ""), "estimated_improvement": ""} for v in items],
                "performance_score": max(0, 100 - len(items) * 15),
                "overall_complexity": "O(n)",
                "summary": f"Found {len(items)} performance issue(s)." if items else "No performance issues."
            })
        elif "style" in sp or "maintainab" in sp or "naming" in sp:
            items = _str_to_issues(parsed.get("style", []), "suggestion")
            return json.dumps({
                "issues": [{"line": v.get("line", 0), "severity": v.get("severity", "low"),
                    "category": "style", "description": v.get("description", ""),
                    "suggestion": v.get("suggestion", ""), "standard": ""} for v in items],
                "style_score": max(0, 100 - len(items) * 10),
                "maintainability_index": "medium",
                "summary": f"Found {len(items)} style issue(s)." if items else "No style issues."
            })
        elif "bug" in sp or "logic" in sp or "reliability" in sp:
            items = _str_to_issues(parsed.get("bugs", []), "fix")
            return json.dumps({
                "bugs": [{"line": v.get("line", 0), "severity": v.get("severity", "high"),
                    "type": v.get("type", "logic error"), "description": v.get("description", ""),
                    "impact": "", "fix": v.get("fix", ""), "test_case": ""} for v in items],
                "reliability_score": max(0, 100 - len(items) * 20),
                "confidence": "medium",
                "summary": f"Found {len(items)} bug(s)." if items else "No bugs found."
            })
        else:
            # AutoFix agent
            score = parsed.get("score", 50)
            all_issues = (list(parsed.get("bugs", [])) + list(parsed.get("security", [])) +
                          list(parsed.get("performance", [])))
            return json.dumps({
                "fixed_code": code,
                "changes_made": [{"line": 0, "type": "fix", "description": str(i)} for i in all_issues[:5]],
                "improvement_summary": f"Score: {score}/100."
            })
    except Exception as e:
        logger.error(f"Local model call failed: {e}", exc_info=True)
        return json.dumps({"error": str(e)})


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Route LLM call to local model or OpenAI based on USE_LOCAL_MODEL env var."""
    if _use_local_model():
        return _call_local(system_prompt, user_prompt)
    return _call_openai(system_prompt, user_prompt)


def _parse_json_safe(text: str, fallback: Any = None) -> Any:
    """Safely parse JSON with fallback."""
    try:
        return json.loads(text)
    except Exception:
        return fallback if fallback is not None else {"error": "Failed to parse agent response", "raw": text[:500]}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SECURITY AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SECURITY_SYSTEM_PROMPT = """You are a senior security engineer specializing in code security auditing.
Analyze the given code for security vulnerabilities including but not limited to:
- SQL Injection
- Cross-Site Scripting (XSS)
- Command Injection
- Path Traversal
- Hardcoded secrets/credentials
- Insecure cryptography
- Missing input validation
- Authentication/authorization flaws
- Insecure deserialization
- Server-Side Request Forgery (SSRF)

Return a JSON object with this exact structure:
{
  "vulnerabilities": [
    {
      "line": <int>,
      "severity": "critical|high|medium|low",
      "type": "<vulnerability type>",
      "cwe": "<CWE ID if applicable>",
      "description": "<clear description>",
      "impact": "<what could happen>",
      "fix": "<how to fix it>"
    }
  ],
  "security_score": <0-100, higher is more secure>,
  "risk_level": "critical|high|medium|low|none",
  "summary": "<brief security assessment>"
}

Only return valid JSON. No other text."""


def run_security_agent(code: str, language: str) -> dict:
    """Run the Security Agent to detect vulnerabilities."""
    start = time.time()
    user_prompt = f"Language: {language}\n\nAnalyze this code for security vulnerabilities:\n```{language}\n{code}\n```"
    result_text = _call_llm(SECURITY_SYSTEM_PROMPT, user_prompt)
    if "error" in result_text:
        logger.error(f"Security agent error: {result_text}")
    result = _parse_json_safe(result_text, {
        "vulnerabilities": [],
        "security_score": 0,
        "risk_level": "unknown",
        "summary": f"Analysis failed — {_parse_json_safe(result_text, {}).get('error', 'parse error')}"
    })
    result["_duration_ms"] = int((time.time() - start) * 1000)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PERFORMANCE AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PERFORMANCE_SYSTEM_PROMPT = """You are a senior performance engineer specializing in code optimization.
Analyze the given code for performance issues including:
- Time complexity problems (inefficient algorithms)
- Space complexity issues (memory leaks, excessive allocation)
- Unnecessary iterations or redundant operations
- N+1 query patterns
- Missing caching opportunities
- Blocking operations in async contexts
- Resource leaks (unclosed files, connections)
- Inefficient data structures

Return a JSON object with this exact structure:
{
  "issues": [
    {
      "line": <int>,
      "severity": "critical|high|medium|low",
      "type": "<issue type>",
      "current_complexity": "<O(n²) etc if applicable>",
      "description": "<clear description of the bottleneck>",
      "optimization": "<specific optimization suggestion>",
      "estimated_improvement": "<how much faster/better>"
    }
  ],
  "performance_score": <0-100, higher is better performing>,
  "overall_complexity": "<dominant time complexity>",
  "summary": "<brief performance assessment>"
}

Only return valid JSON. No other text."""


def run_performance_agent(code: str, language: str) -> dict:
    """Run the Performance Agent to find bottlenecks."""
    start = time.time()
    user_prompt = f"Language: {language}\n\nAnalyze this code for performance issues:\n```{language}\n{code}\n```"
    result_text = _call_llm(PERFORMANCE_SYSTEM_PROMPT, user_prompt)
    if "error" in result_text:
        logger.error(f"Performance agent error: {result_text}")
    result = _parse_json_safe(result_text, {
        "issues": [],
        "performance_score": 0,
        "overall_complexity": "unknown",
        "summary": f"Analysis failed — {_parse_json_safe(result_text, {}).get('error', 'parse error')}"
    })
    result["_duration_ms"] = int((time.time() - start) * 1000)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STYLE AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STYLE_SYSTEM_PROMPT = """You are a senior code quality engineer who enforces best practices and coding standards.
Analyze the given code for style and maintainability issues including:
- Naming conventions (variables, functions, classes)
- Code formatting and consistency
- Documentation (missing docstrings, comments)
- Code duplication / DRY violations
- Function/class design (Single Responsibility, cohesion)
- Error handling patterns
- Import organization
- Magic numbers / hardcoded values
- Dead code / unused variables
- Type annotations (for Python/TypeScript)

Return a JSON object with this exact structure:
{
  "issues": [
    {
      "line": <int>,
      "severity": "critical|high|medium|low",
      "category": "naming|formatting|documentation|design|error_handling|imports|types|other",
      "description": "<clear description>",
      "suggestion": "<specific improvement>",
      "standard": "<which standard/guideline this violates>"
    }
  ],
  "style_score": <0-100, higher is better>,
  "maintainability_index": "<low|medium|high>",
  "summary": "<brief style assessment>"
}

Only return valid JSON. No other text."""


def run_style_agent(code: str, language: str) -> dict:
    """Run the Style Agent to enforce best practices."""
    start = time.time()
    user_prompt = f"Language: {language}\n\nAnalyze this code for style and maintainability:\n```{language}\n{code}\n```"
    result_text = _call_llm(STYLE_SYSTEM_PROMPT, user_prompt)
    if "error" in result_text:
        logger.error(f"Style agent error: {result_text}")
    result = _parse_json_safe(result_text, {
        "issues": [],
        "style_score": 0,
        "maintainability_index": "unknown",
        "summary": f"Analysis failed — {_parse_json_safe(result_text, {}).get('error', 'parse error')}"
    })
    result["_duration_ms"] = int((time.time() - start) * 1000)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BUG DETECTOR AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BUG_DETECTOR_SYSTEM_PROMPT = """You are a senior QA engineer and bug hunter specializing in finding logic errors.
Analyze the given code for bugs including:
- Logic errors and incorrect conditionals
- Off-by-one errors
- Null/undefined reference potential
- Race conditions
- Unhandled edge cases
- Type mismatches
- Incorrect return values
- Missing break/return statements
- Infinite loops potential
- Integer overflow/underflow

Return a JSON object with this exact structure:
{
  "bugs": [
    {
      "line": <int>,
      "severity": "critical|high|medium|low",
      "type": "<bug type>",
      "description": "<clear description of the bug>",
      "impact": "<what could go wrong>",
      "fix": "<how to fix it>",
      "test_case": "<a test case that would expose this bug>"
    }
  ],
  "reliability_score": <0-100, higher means fewer bugs>,
  "confidence": "<how confident the agent is in findings>",
  "summary": "<brief bug assessment>"
}

Only return valid JSON. No other text."""


def run_bug_detector_agent(code: str, language: str) -> dict:
    """Run the Bug Detector Agent to find logic errors."""
    start = time.time()
    user_prompt = f"Language: {language}\n\nAnalyze this code for bugs and logic errors:\n```{language}\n{code}\n```"
    result_text = _call_llm(BUG_DETECTOR_SYSTEM_PROMPT, user_prompt)
    if "error" in result_text:
        logger.error(f"Bug detector agent error: {result_text}")
    result = _parse_json_safe(result_text, {
        "bugs": [],
        "reliability_score": 0,
        "confidence": "unknown",
        "summary": f"Analysis failed — {_parse_json_safe(result_text, {}).get('error', 'parse error')}"
    })
    result["_duration_ms"] = int((time.time() - start) * 1000)
    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTO-FIX AGENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUTOFIX_SYSTEM_PROMPT = """You are a senior software engineer who specializes in refactoring and fixing code.
Given the original code AND a list of identified issues, generate the FIXED version of the code.

Requirements:
- Apply ALL fixes for bugs, security issues, performance problems, and style issues
- Keep the same overall structure and logic intent
- Add proper error handling where missing
- Add type annotations where applicable
- Add documentation where missing
- Ensure the fixed code is production-ready

Return a JSON object with this exact structure:
{
  "fixed_code": "<the complete fixed code>",
  "changes_made": [
    {
      "line": <int>,
      "type": "fix|refactor|optimization|documentation",
      "description": "<what was changed and why>"
    }
  ],
  "improvement_summary": "<what was improved overall>"
}

Only return valid JSON. No other text."""


def run_autofix_agent(code: str, language: str, issues_summary: str) -> dict:
    """Run the Auto-Fix Agent to generate corrected code."""
    start = time.time()
    user_prompt = f"""Language: {language}

Original code:
```{language}
{code}
```

Issues found by other agents:
{issues_summary}

Generate the fixed version of this code addressing ALL issues above."""

    result_text = _call_llm(AUTOFIX_SYSTEM_PROMPT, user_prompt)
    result = _parse_json_safe(result_text, {
        "fixed_code": code,
        "changes_made": [],
        "improvement_summary": "Unable to generate fixes"
    })
    result["_duration_ms"] = int((time.time() - start) * 1000)
    return result
