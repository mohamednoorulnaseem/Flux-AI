"""
Flux AI – Streamlit Frontend
Multi-agent code review powered by OpenAI agents.
"""
import requests
import streamlit as st

API_URL = "http://localhost:8000"

# ─── Page Config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Flux AI – Code Reviewer",
    page_icon="⚡",
    layout="wide",
)

# ─── Styles ──────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #7C3AED;
    }
    .subtitle {
        color: #6B7280;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    .score-box {
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        font-size: 2rem;
        font-weight: 800;
    }
    .badge-critical { background: #FEE2E2; color: #B91C1C; border-radius:6px; padding:2px 8px; font-size:0.8rem; font-weight:600; }
    .badge-high     { background: #FEF3C7; color: #B45309; border-radius:6px; padding:2px 8px; font-size:0.8rem; font-weight:600; }
    .badge-medium   { background: #DBEAFE; color: #1D4ED8; border-radius:6px; padding:2px 8px; font-size:0.8rem; font-weight:600; }
    .badge-low      { background: #D1FAE5; color: #065F46; border-radius:6px; padding:2px 8px; font-size:0.8rem; font-weight:600; }
    .category-icon  { font-size:1.1rem; margin-right:6px; }
</style>
""", unsafe_allow_html=True)

# ─── Header ──────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">⚡ Flux AI – Code Reviewer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Multi-agent AI analysis: Security · Performance · Style · Bug Detection · Auto-Fix</div>', unsafe_allow_html=True)
st.divider()

# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Settings")

    language = st.selectbox(
        "Language",
        ["python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "php", "ruby"],
        index=0,
    )

    filename = st.text_input("Filename (optional)", value="untitled")

    st.divider()
    st.markdown("**Agents**")
    st.markdown("🔐 SecurityAgent")
    st.markdown("⚡ PerformanceAgent")
    st.markdown("🎨 StyleAgent")
    st.markdown("🐛 BugDetectorAgent")
    st.markdown("🔧 AutoFixAgent")

    st.divider()
    st.caption(f"Backend: `{API_URL}`")

# ─── Input ───────────────────────────────────────────────────────────────────

code_input = st.text_area(
    "Paste your code here",
    height=320,
    placeholder="# Paste your code here...\ndef example():\n    pass",
    label_visibility="collapsed",
)

col_btn, col_spacer = st.columns([1, 5])
with col_btn:
    run = st.button("🔍 Review Code", type="primary", use_container_width=True)

# ─── Review ──────────────────────────────────────────────────────────────────

CATEGORY_ICONS = {
    "security": "🔐",
    "performance": "⚡",
    "style": "🎨",
    "bug": "🐛",
}

GRADE_COLORS = {
    "A+": "#166534", "A": "#15803D", "A-": "#16A34A",
    "B+": "#1D4ED8", "B": "#2563EB", "B-": "#3B82F6",
    "C+": "#92400E", "C": "#B45309", "C-": "#D97706",
    "D":  "#B91C1C", "F": "#7F1D1D",
}


def render_score(score: int, grade: str):
    color = GRADE_COLORS.get(grade, "#6B7280")
    st.markdown(f"""
    <div class="score-box" style="background:{color}22; border: 2px solid {color};">
        <div style="color:{color}; font-size:3rem;">{grade}</div>
        <div style="color:{color}; font-size:1.2rem;">{score} / 100</div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(metrics: dict):
    cols = st.columns(4)
    labels = {
        "security": ("🔐", "Security"),
        "performance": ("⚡", "Performance"),
        "maintainability": ("🔧", "Maintainability"),
        "readability": ("📖", "Readability"),
    }
    for i, (key, (icon, label)) in enumerate(labels.items()):
        val = metrics.get(key, 0)
        color = "#16A34A" if val >= 80 else "#D97706" if val >= 60 else "#B91C1C"
        with cols[i]:
            st.markdown(f"**{icon} {label}**")
            st.markdown(f"<span style='font-size:1.5rem;font-weight:700;color:{color}'>{val}</span>", unsafe_allow_html=True)
            st.progress(val / 100)


def severity_badge(severity: str) -> str:
    return f'<span class="badge-{severity}">{severity.upper()}</span>'


def render_issues(issues: list):
    if not issues:
        st.success("✅ No issues found!")
        return

    categories = {}
    for issue in issues:
        cat = issue.get("category", "other")
        categories.setdefault(cat, []).append(issue)

    for cat, cat_issues in categories.items():
        icon = CATEGORY_ICONS.get(cat, "🔍")
        with st.expander(f"{icon} {cat.capitalize()} ({len(cat_issues)} issues)", expanded=True):
            for issue in cat_issues:
                line = issue.get("line", 0)
                severity = issue.get("severity", "low")
                desc = issue.get("description", "")
                suggestion = issue.get("suggestion", "")
                impact = issue.get("impact", "")

                col1, col2 = st.columns([1, 8])
                with col1:
                    st.markdown(severity_badge(severity), unsafe_allow_html=True)
                    if line:
                        st.caption(f"Line {line}")
                with col2:
                    st.markdown(f"**{desc}**")
                    if suggestion:
                        st.markdown(f"💡 *{suggestion}*")
                    if impact:
                        st.caption(f"Impact: {impact}")
                st.divider()


if run:
    if not code_input.strip():
        st.warning("Please enter some code before reviewing.")
    else:
        with st.spinner("Running multi-agent review pipeline..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/review",
                    json={
                        "code": code_input,
                        "language": language,
                        "filename": filename or "untitled",
                    },
                    timeout=120,
                )
                response.raise_for_status()
                result = response.json()
            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to the backend at `{API_URL}`. Make sure the FastAPI server is running.")
                st.stop()
            except requests.exceptions.Timeout:
                st.error("The review timed out after 120 seconds. Try with a smaller code snippet.")
                st.stop()
            except requests.exceptions.HTTPError as e:
                st.error(f"API error: {e.response.text}")
                st.stop()

        st.success("Review complete!")
        st.divider()

        # ── Score & Grade ──
        score = result.get("score", 0)
        grade = result.get("grade", "")
        metrics = result.get("metrics", {})

        col_score, col_metrics = st.columns([1, 3])
        with col_score:
            st.subheader("Overall Score")
            render_score(score, grade)
        with col_metrics:
            st.subheader("Sub-scores")
            render_metrics(metrics)

        st.divider()

        # ── Summary ──
        summary = result.get("summary", "")
        if summary:
            st.subheader("📋 Summary")
            st.info(summary)

        # ── Quick Wins ──
        quick_wins = result.get("quick_wins", [])
        if quick_wins:
            st.subheader("⚡ Quick Wins")
            for win in quick_wins:
                st.markdown(f"- {win}")

        st.divider()

        # ── Issues ──
        issues = result.get("issues", [])
        st.subheader(f"🔍 Issues Found ({len(issues)})")
        render_issues(issues)

        # ── Fixed Code ──
        fixed_code = result.get("fixed_code", "")
        if fixed_code:
            st.divider()
            st.subheader("🔧 Auto-Fixed Code")
            changes = result.get("changes_made", [])
            if changes:
                with st.expander("Changes made"):
                    for change in changes:
                        st.markdown(f"- {change}")
            st.code(fixed_code, language=language)

        # ── Metadata ──
        meta = result.get("metadata", {})
        if meta:
            st.divider()
            proc_ms = meta.get("processing_time_ms", 0)
            total_agents = meta.get("agents_run", 0)
            st.caption(
                f"⏱ Processed in {proc_ms / 1000:.1f}s — "
                f"{total_agents} agents — "
                f"{len(issues)} issues found"
            )
