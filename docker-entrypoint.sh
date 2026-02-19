#!/bin/bash
# Flux AI – Docker Entrypoint
# Starts both the FastAPI backend and the Streamlit frontend

set -e

echo "🚀 Starting Flux AI..."

# Start FastAPI backend in background
echo "  ▶ Starting backend on port 8000..."
uvicorn backend.flux_backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "  ⏳ Waiting for backend..."
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    sleep 1
done
echo "  ✅ Backend ready"

# Start Streamlit frontend
echo "  ▶ Starting Streamlit UI on port 8501..."
streamlit run frontend/app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false &
FRONTEND_PID=$!

echo ""
echo "✅ Flux AI is running:"
echo "   API:      http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo "   Streamlit: http://localhost:8501"
echo ""

# Keep container alive and handle signals
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" SIGTERM SIGINT
wait $BACKEND_PID $FRONTEND_PID
