"""
Flux Orchestrator — The master agent that coordinates the multi-agent pipeline.

Pipeline Flow:
  1. SecurityAgent    → runs in parallel with...
  2. PerformanceAgent → runs in parallel with...
  3. StyleAgent       → runs in parallel with...
  4. BugDetectorAgent → runs in parallel
  5. Orchestrator merges all results
  6. AutoFixAgent     → generates corrected code using all findings
  7. Final scoring, metrics, and report generation

Enhanced with:
  • Sub-score metrics (security, performance, maintainability, readability)
  • Quick-wins generation
  • Impact assessment per issue
  • Grade letter system (A+ through F)
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

from .agents import (
    run_security_agent,
    run_performance_agent,
    run_style_agent,
    run_bug_detector_agent,
    run_autofix_agent,
)


def _merge_issues(agent_results: dict) -> list[dict]:
    """Merge all issues from all agents into a unified list with impact."""
    merged = []

    # Security vulnerabilities
    security = agent_results.get("security", {})
    for vuln in security.get("vulnerabilities", []):
        merged.append({
            "line": vuln.get("line", 0),
            "severity": vuln.get("severity", "medium"),
            "category": "security",
            "type": vuln.get("type", "vulnerability"),
            "description": vuln.get("description", ""),
            "suggestion": vuln.get("fix", ""),
            "impact": vuln.get("impact", "Could compromise application security."),
        })

    # Performance issues
    performance = agent_results.get("performance", {})
    for issue in performance.get("issues", []):
        merged.append({
            "line": issue.get("line", 0),
            "severity": issue.get("severity", "medium"),
            "category": "performance",
            "type": issue.get("type", "bottleneck"),
            "description": issue.get("description", ""),
            "suggestion": issue.get("optimization", ""),
            "impact": issue.get("impact", "May degrade application performance."),
        })

    # Style issues
    style = agent_results.get("style", {})
    for issue in style.get("issues", []):
        merged.append({
            "line": issue.get("line", 0),
            "severity": issue.get("severity", "low"),
            "category": "style",
            "type": issue.get("category", "style"),
            "description": issue.get("description", ""),
            "suggestion": issue.get("suggestion", ""),
            "impact": issue.get("impact", "Reduces code readability and maintainability."),
        })

    # Bugs
    bugs = agent_results.get("bugs", {})
    for bug in bugs.get("bugs", []):
        merged.append({
            "line": bug.get("line", 0),
            "severity": bug.get("severity", "high"),
            "category": "bug",
            "type": bug.get("type", "logic_error"),
            "description": bug.get("description", ""),
            "suggestion": bug.get("fix", ""),
            "impact": bug.get("impact", "Could cause unexpected behavior or crashes."),
        })

    # Sort by severity (critical first) then by line number
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    merged.sort(key=lambda x: (severity_order.get(x["severity"], 4), x["line"]))

    return merged


def _compute_final_score(agent_results: dict) -> int:
    """Compute a weighted final score from all agent scores."""
    weights = {
        "security": 0.30,
        "performance": 0.20,
        "style": 0.15,
        "bugs": 0.35,
    }

    scores = {
        "security": agent_results.get("security", {}).get("security_score", 100),
        "performance": agent_results.get("performance", {}).get("performance_score", 100),
        "style": agent_results.get("style", {}).get("style_score", 100),
        "bugs": agent_results.get("bugs", {}).get("reliability_score", 100),
    }

    weighted = sum(scores[k] * weights[k] for k in weights)
    return max(0, min(100, int(round(weighted))))


def _compute_metrics(agent_results: dict) -> dict:
    """Compute detailed sub-score metrics."""
    sec_score = agent_results.get("security", {}).get("security_score", 100)
    perf_score = agent_results.get("performance", {}).get("performance_score", 100)
    style_score = agent_results.get("style", {}).get("style_score", 100)
    bug_score = agent_results.get("bugs", {}).get("reliability_score", 100)

    # Maintainability combines style + bug detection
    maintainability = int((style_score * 0.6 + bug_score * 0.4))
    # Readability is primarily style
    readability = int(style_score * 0.8 + perf_score * 0.2)

    return {
        "security": min(100, max(0, sec_score)),
        "performance": min(100, max(0, perf_score)),
        "maintainability": min(100, max(0, maintainability)),
        "readability": min(100, max(0, readability)),
    }


def _compute_grade(score: int) -> str:
    """Compute a letter grade from a numeric score."""
    if score >= 95:
        return "A+"
    elif score >= 88:
        return "A"
    elif score >= 80:
        return "A-"
    elif score >= 75:
        return "B+"
    elif score >= 70:
        return "B"
    elif score >= 65:
        return "B-"
    elif score >= 60:
        return "C+"
    elif score >= 55:
        return "C"
    elif score >= 50:
        return "C-"
    elif score >= 40:
        return "D"
    else:
        return "F"


def _generate_quick_wins(merged_issues: list) -> list[str]:
    """Generate actionable quick-win tips from the issues."""
    quick_wins = []

    # Group by category
    categories = {}
    for issue in merged_issues:
        cat = issue.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(issue)

    # Generate tips per category
    sec_issues = categories.get("security", [])
    if sec_issues:
        crit_sec = [i for i in sec_issues if i["severity"] in ("critical", "high")]
        if crit_sec:
            quick_wins.append(f"Fix {len(crit_sec)} critical/high security issue{'s' if len(crit_sec) > 1 else ''} — hardcoded credentials and injection risks are easy wins.")
        elif sec_issues:
            quick_wins.append("Address minor security warnings to harden your code against future vulnerabilities.")

    perf_issues = categories.get("performance", [])
    if perf_issues:
        quick_wins.append(f"Optimize {len(perf_issues)} performance hotspot{'s' if len(perf_issues) > 1 else ''} — look for O(n²) loops and unnecessary allocations.")

    bug_issues = categories.get("bug", [])
    if bug_issues:
        quick_wins.append(f"Fix {len(bug_issues)} bug{'s' if len(bug_issues) > 1 else ''} — logic errors and off-by-one mistakes cause silent failures.")

    style_issues = categories.get("style", [])
    if style_issues:
        quick_wins.append(f"Clean up {len(style_issues)} style issue{'s' if len(style_issues) > 1 else ''} — consistent naming and formatting improve team velocity.")

    # Add general tips if not many issues
    if len(quick_wins) < 3:
        if not sec_issues:
            quick_wins.append("Add input validation and sanitization for all user-facing inputs.")
        quick_wins.append("Consider adding unit tests for edge cases to prevent regressions.")
        quick_wins.append("Use type hints and docstrings for better IDE support and documentation.")

    return quick_wins[:5]  # Max 5 quick wins


def _generate_summary(agent_results: dict, merged_issues: list, score: int) -> str:
    """Generate a comprehensive summary from all agent results."""
    parts = []

    total = len(merged_issues)
    critical = sum(1 for i in merged_issues if i["severity"] == "critical")
    high = sum(1 for i in merged_issues if i["severity"] == "high")

    if total == 0:
        parts.append("✅ Excellent! No issues detected across all analysis domains.")
    else:
        parts.append(f"Found {total} issue{'s' if total != 1 else ''} across security, performance, style, and bug detection.")

    if critical > 0:
        parts.append(f"🚨 {critical} critical issue{'s' if critical != 1 else ''} require immediate attention.")
    if high > 0:
        parts.append(f"⚠️ {high} high-severity issue{'s' if high != 1 else ''} should be addressed soon.")

    # Agent summaries
    sec = agent_results.get("security", {})
    if sec.get("summary"):
        parts.append(f"Security: {sec['summary']}")

    perf = agent_results.get("performance", {})
    if perf.get("summary"):
        parts.append(f"Performance: {perf['summary']}")

    parts.append(f"Overall Quality Score: {score}/100 (Grade: {_compute_grade(score)})")

    return " ".join(parts)


def _build_issues_summary_for_autofix(agent_results: dict) -> str:
    """Build a text summary of all issues for the AutoFix agent."""
    lines = []

    for vuln in agent_results.get("security", {}).get("vulnerabilities", []):
        lines.append(f"[SECURITY] Line {vuln.get('line', '?')}: {vuln.get('description', '')} → Fix: {vuln.get('fix', '')}")

    for issue in agent_results.get("performance", {}).get("issues", []):
        lines.append(f"[PERFORMANCE] Line {issue.get('line', '?')}: {issue.get('description', '')} → Fix: {issue.get('optimization', '')}")

    for issue in agent_results.get("style", {}).get("issues", []):
        lines.append(f"[STYLE] Line {issue.get('line', '?')}: {issue.get('description', '')} → Fix: {issue.get('suggestion', '')}")

    for bug in agent_results.get("bugs", {}).get("bugs", []):
        lines.append(f"[BUG] Line {bug.get('line', '?')}: {bug.get('description', '')} → Fix: {bug.get('fix', '')}")

    return "\n".join(lines) if lines else "No issues found."


def run_orchestrator(code: str, language: str = "python",
                     progress_callback: Callable | None = None) -> dict:
    """
    Run the full multi-agent orchestration pipeline.

    Args:
        code: Source code to review
        language: Programming language
        progress_callback: Optional callback for real-time progress updates

    Returns:
        Complete review result with all agent outputs, metrics, grades, and quick wins
    """
    pipeline_start = time.time()
    agent_results = {}

    def notify(agent_name: str, status: str, data: dict = None):
        if progress_callback:
            progress_callback({
                "agent": agent_name,
                "status": status,
                "data": data or {},
                "timestamp": time.time()
            })

    # ── Phase 1: Run analysis agents in parallel ────────
    notify("orchestrator", "started", {"phase": "analysis", "total_agents": 4})

    analysis_agents = {
        "security": (run_security_agent, "🔐 Security Agent"),
        "performance": (run_performance_agent, "⚡ Performance Agent"),
        "style": (run_style_agent, "🎨 Style Agent"),
        "bugs": (run_bug_detector_agent, "🐛 Bug Detector Agent"),
    }

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        for name, (func, label) in analysis_agents.items():
            notify(name, "running", {"label": label})
            futures[executor.submit(func, code, language)] = name

        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                agent_results[name] = result
                notify(name, "completed", {
                    "label": analysis_agents[name][1],
                    "duration_ms": result.get("_duration_ms", 0)
                })
            except Exception as e:
                agent_results[name] = {"error": str(e)}
                notify(name, "failed", {"error": str(e)})

    # ── Phase 2: Merge & score ──────────────────────────
    notify("orchestrator", "merging")

    merged_issues = _merge_issues(agent_results)
    final_score = _compute_final_score(agent_results)
    metrics = _compute_metrics(agent_results)
    grade = _compute_grade(final_score)
    quick_wins = _generate_quick_wins(merged_issues)
    summary = _generate_summary(agent_results, merged_issues, final_score)

    # ── Phase 3: Auto-Fix Agent ─────────────────────────
    notify("autofix", "running", {"label": "🔧 Auto-Fix Agent"})

    issues_text = _build_issues_summary_for_autofix(agent_results)
    autofix_result = run_autofix_agent(code, language, issues_text)
    agent_results["autofix"] = autofix_result

    notify("autofix", "completed", {
        "duration_ms": autofix_result.get("_duration_ms", 0)
    })

    # ── Phase 4: Final assembly ─────────────────────────
    total_time_ms = int((time.time() - pipeline_start) * 1000)
    notify("orchestrator", "completed", {"total_time_ms": total_time_ms})

    return {
        "issues": merged_issues,
        "summary": summary,
        "score": final_score,
        "grade": grade,
        "fixed_code": autofix_result.get("fixed_code", ""),
        "changes_made": autofix_result.get("changes_made", []),
        "metrics": metrics,
        "quick_wins": quick_wins,
        "agent_results": {
            "security": {
                "score": agent_results.get("security", {}).get("security_score", 0),
                "risk_level": agent_results.get("security", {}).get("risk_level", "unknown"),
                "vulnerability_count": len(agent_results.get("security", {}).get("vulnerabilities", [])),
                "summary": agent_results.get("security", {}).get("summary", ""),
                "duration_ms": agent_results.get("security", {}).get("_duration_ms", 0),
            },
            "performance": {
                "score": agent_results.get("performance", {}).get("performance_score", 0),
                "complexity": agent_results.get("performance", {}).get("overall_complexity", "N/A"),
                "issue_count": len(agent_results.get("performance", {}).get("issues", [])),
                "summary": agent_results.get("performance", {}).get("summary", ""),
                "duration_ms": agent_results.get("performance", {}).get("_duration_ms", 0),
            },
            "style": {
                "score": agent_results.get("style", {}).get("style_score", 0),
                "maintainability": agent_results.get("style", {}).get("maintainability_index", "unknown"),
                "issue_count": len(agent_results.get("style", {}).get("issues", [])),
                "summary": agent_results.get("style", {}).get("summary", ""),
                "duration_ms": agent_results.get("style", {}).get("_duration_ms", 0),
            },
            "bugs": {
                "score": agent_results.get("bugs", {}).get("reliability_score", 0),
                "confidence": agent_results.get("bugs", {}).get("confidence", "unknown"),
                "bug_count": len(agent_results.get("bugs", {}).get("bugs", [])),
                "summary": agent_results.get("bugs", {}).get("summary", ""),
                "duration_ms": agent_results.get("bugs", {}).get("_duration_ms", 0),
            },
            "autofix": {
                "changes_count": len(autofix_result.get("changes_made", [])),
                "summary": autofix_result.get("improvement_summary", ""),
                "duration_ms": autofix_result.get("_duration_ms", 0),
            },
        },
        "metadata": {
            "total_issues": len(merged_issues),
            "critical_count": sum(1 for i in merged_issues if i["severity"] == "critical"),
            "high_count": sum(1 for i in merged_issues if i["severity"] == "high"),
            "medium_count": sum(1 for i in merged_issues if i["severity"] == "medium"),
            "low_count": sum(1 for i in merged_issues if i["severity"] == "low"),
            "processing_time_ms": total_time_ms,
            "agents_used": 5,
        }
    }
