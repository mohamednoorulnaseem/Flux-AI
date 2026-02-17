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
from typing import Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

AI_MODEL = os.getenv("AI_MODEL", "gpt-4.1-mini")

# Lazy-init client — don't crash at import if no API key
_client = None


def _get_client() -> OpenAI:
    """Get or create the OpenAI client (lazy init)."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Create a .env file in the backend directory with: OPENAI_API_KEY=sk-..."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    """Shared helper to call OpenAI and extract text."""
    try:
        client = _get_client()
        response = client.responses.create(
            model=AI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )
        text = response.output_text

        fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()
        return text
    except Exception as e:
        return json.dumps({"error": str(e)})


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
    result_text = _call_openai(SECURITY_SYSTEM_PROMPT, user_prompt)
    result = _parse_json_safe(result_text, {
        "vulnerabilities": [],
        "security_score": 100,
        "risk_level": "none",
        "summary": "Unable to analyze"
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
    result_text = _call_openai(PERFORMANCE_SYSTEM_PROMPT, user_prompt)
    result = _parse_json_safe(result_text, {
        "issues": [],
        "performance_score": 100,
        "overall_complexity": "N/A",
        "summary": "Unable to analyze"
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
    result_text = _call_openai(STYLE_SYSTEM_PROMPT, user_prompt)
    result = _parse_json_safe(result_text, {
        "issues": [],
        "style_score": 100,
        "maintainability_index": "unknown",
        "summary": "Unable to analyze"
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
    result_text = _call_openai(BUG_DETECTOR_SYSTEM_PROMPT, user_prompt)
    result = _parse_json_safe(result_text, {
        "bugs": [],
        "reliability_score": 100,
        "confidence": "unknown",
        "summary": "Unable to analyze"
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

    result_text = _call_openai(AUTOFIX_SYSTEM_PROMPT, user_prompt)
    result = _parse_json_safe(result_text, {
        "fixed_code": code,
        "changes_made": [],
        "improvement_summary": "Unable to generate fixes"
    })
    result["_duration_ms"] = int((time.time() - start) * 1000)
    return result
