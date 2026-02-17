"""
Flux Database — SQLite with async support for SaaS persistence.
Stores users, reviews, projects, and agent run history.
"""
import sqlite3
import json
import os
from datetime import datetime, timezone


DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "flux.db"))


def get_db():
    """Get a database connection with row_factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the database schema."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            avatar_url TEXT DEFAULT '',
            plan TEXT DEFAULT 'free',
            reviews_used INTEGER DEFAULT 0,
            reviews_limit INTEGER DEFAULT 50,
            api_key TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            github_repo TEXT DEFAULT '',
            language TEXT DEFAULT 'python',
            total_reviews INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_id INTEGER,
            filename TEXT DEFAULT 'untitled',
            language TEXT DEFAULT 'python',
            code TEXT NOT NULL,
            issues TEXT DEFAULT '[]',
            summary TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            agent_results TEXT DEFAULT '{}',
            fixed_code TEXT DEFAULT '',
            total_issues INTEGER DEFAULT 0,
            critical_count INTEGER DEFAULT 0,
            high_count INTEGER DEFAULT 0,
            medium_count INTEGER DEFAULT 0,
            low_count INTEGER DEFAULT 0,
            processing_time_ms INTEGER DEFAULT 0,
            status TEXT DEFAULT 'completed',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS agent_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT DEFAULT '{}',
            started_at TEXT,
            completed_at TEXT,
            duration_ms INTEGER DEFAULT 0,
            FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);
        CREATE INDEX IF NOT EXISTS idx_reviews_created ON reviews(created_at);
        CREATE INDEX IF NOT EXISTS idx_agent_runs_review ON agent_runs(review_id);
        CREATE INDEX IF NOT EXISTS idx_projects_user ON projects(user_id);
    """)

    conn.commit()
    conn.close()


# ─── User Operations ────────────────────────────────────

def create_user(email: str, username: str, hashed_password: str, full_name: str = "") -> dict:
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (email, username, hashed_password, full_name) VALUES (?, ?, ?, ?)",
            (email, username, hashed_password, full_name)
        )
        conn.commit()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(user)
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_user_reviews_used(user_id: int):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE users SET reviews_used = reviews_used + 1, updated_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), user_id)
        )
        conn.commit()
    finally:
        conn.close()


# ─── Review Operations ──────────────────────────────────

def create_review(user_id: int, filename: str, language: str, code: str,
                  issues: list, summary: str, score: int, agent_results: dict,
                  fixed_code: str, processing_time_ms: int,
                  project_id: int | None = None) -> dict:
    """Save a completed review."""
    total_issues = len(issues)
    critical = sum(1 for i in issues if i.get("severity") == "critical")
    high = sum(1 for i in issues if i.get("severity") == "high")
    medium = sum(1 for i in issues if i.get("severity") == "medium")
    low = sum(1 for i in issues if i.get("severity") == "low")

    conn = get_db()
    try:
        cursor = conn.execute(
            """INSERT INTO reviews
               (user_id, project_id, filename, language, code, issues, summary,
                score, agent_results, fixed_code, total_issues,
                critical_count, high_count, medium_count, low_count,
                processing_time_ms, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')""",
            (user_id, project_id, filename, language, code,
             json.dumps(issues), summary, score, json.dumps(agent_results),
             fixed_code, total_issues, critical, high, medium, low,
             processing_time_ms)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM reviews WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_reviews_by_user(user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM reviews WHERE user_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset)
        ).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            d["issues"] = json.loads(d.get("issues", "[]"))
            d["agent_results"] = json.loads(d.get("agent_results", "{}"))
            results.append(d)
        return results
    finally:
        conn.close()


def get_review_by_id(review_id: int, user_id: int) -> dict | None:
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT * FROM reviews WHERE id = ? AND user_id = ?",
            (review_id, user_id)
        ).fetchone()
        if row:
            d = dict(row)
            d["issues"] = json.loads(d.get("issues", "[]"))
            d["agent_results"] = json.loads(d.get("agent_results", "{}"))
            return d
        return None
    finally:
        conn.close()


def get_user_stats(user_id: int) -> dict:
    """Get aggregated stats for a user's dashboard."""
    conn = get_db()
    try:
        total = conn.execute(
            "SELECT COUNT(*) as cnt FROM reviews WHERE user_id = ?", (user_id,)
        ).fetchone()["cnt"]

        avg_score = conn.execute(
            "SELECT COALESCE(AVG(score), 0) as avg FROM reviews WHERE user_id = ?", (user_id,)
        ).fetchone()["avg"]

        total_issues = conn.execute(
            "SELECT COALESCE(SUM(total_issues), 0) as total FROM reviews WHERE user_id = ?",
            (user_id,)
        ).fetchone()["total"]

        severity_counts = conn.execute(
            """SELECT
                COALESCE(SUM(critical_count), 0) as critical,
                COALESCE(SUM(high_count), 0) as high,
                COALESCE(SUM(medium_count), 0) as medium,
                COALESCE(SUM(low_count), 0) as low
               FROM reviews WHERE user_id = ?""",
            (user_id,)
        ).fetchone()

        # Recent score trend (last 10 reviews)
        trend_rows = conn.execute(
            "SELECT score, created_at FROM reviews WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        ).fetchall()
        score_trend = [{"score": r["score"], "date": r["created_at"]} for r in trend_rows]

        # Language distribution
        lang_rows = conn.execute(
            "SELECT language, COUNT(*) as cnt FROM reviews WHERE user_id = ? GROUP BY language",
            (user_id,)
        ).fetchall()
        languages = {r["language"]: r["cnt"] for r in lang_rows}

        return {
            "total_reviews": total,
            "avg_score": round(avg_score, 1),
            "total_issues_found": total_issues,
            "severity_breakdown": {
                "critical": severity_counts["critical"],
                "high": severity_counts["high"],
                "medium": severity_counts["medium"],
                "low": severity_counts["low"]
            },
            "score_trend": score_trend,
            "languages": languages
        }
    finally:
        conn.close()


def delete_review(review_id: int, user_id: int) -> bool:
    conn = get_db()
    try:
        cursor = conn.execute(
            "DELETE FROM reviews WHERE id = ? AND user_id = ?",
            (review_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# Initialize on import
init_db()
