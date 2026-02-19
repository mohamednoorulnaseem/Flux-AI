# Flux AI – Production Dockerfile
# Runs the FastAPI backend (port 8000) and Streamlit UI (port 8501)

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy source ───────────────────────────────────────────────────────────────
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# ── Environment defaults ──────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1
ENV USE_LOCAL_MODEL=false
# Set OPENAI_API_KEY at runtime: docker run -e OPENAI_API_KEY=sk-...

# ── Ports ─────────────────────────────────────────────────────────────────────
EXPOSE 8000
EXPOSE 8501

# ── Startup script ────────────────────────────────────────────────────────────
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
