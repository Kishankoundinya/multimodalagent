#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting Financial Research AI (Multi-Agent System)      "
echo "=========================================================="

# 1. Check Python
PYTHON_BIN=""
if [ -d ".venv" ]; then
    PYTHON_BIN=".venv/bin/python"
elif command -v python3.12 &> /dev/null; then
    PYTHON_BIN="python3.12"
elif command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
else
    echo "Error: Python 3 is required but was not found."
    exit 1
fi

echo "Using Python: $($PYTHON_BIN --version)"

# 2. Check Node & NPM
if ! command -v npm &> /dev/null; then
    echo "Warning: npm was not found. Frontend will not start automatically."
fi

# 3. Create .env if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Ensure data directories exist
mkdir -p data/documents data/chromadb data/reports data/seed

# Generate seed sample document if seed folder is empty
if [ -z "$(ls -A data/seed/*.pdf 2>/dev/null)" ]; then
    echo "Generating verified sample seed report (data/seed/Acme_Annual_Report_2024.pdf)..."
    $PYTHON_BIN backend/tests/create_sample_pdf.py data/seed/Acme_Annual_Report_2024.pdf || true
fi

# 4. Ensure ports 8000 and 5173 are free
OLD_PID_8000=$(lsof -ti :8000 2>/dev/null || true)
if [ -n "$OLD_PID_8000" ]; then
    echo "Releasing existing process on port 8000 (PID: $OLD_PID_8000)..."
    kill -9 $OLD_PID_8000 2>/dev/null || true
    sleep 1
fi

OLD_PID_5173=$(lsof -ti :5173 2>/dev/null || true)
if [ -n "$OLD_PID_5173" ]; then
    echo "Releasing existing process on port 5173 (PID: $OLD_PID_5173)..."
    kill -9 $OLD_PID_5173 2>/dev/null || true
    sleep 1
fi

# 5. Start Backend
echo "Starting FastAPI Backend on http://127.0.0.1:8000..."
$PYTHON_BIN -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# 6. Start Frontend if npm is available
if [ -d "frontend" ] && command -v npm &> /dev/null; then
    echo "Starting Vite Frontend on http://localhost:5173..."
    (cd frontend && npm run dev) &
    FRONTEND_PID=$!
fi

# Cleanup on exit
trap "echo 'Stopping services...'; kill $BACKEND_PID 2>/dev/null || true; kill $FRONTEND_PID 2>/dev/null || true" EXIT

echo "Both services are running!"
echo "Backend:  http://127.0.0.1:8000"
echo "Frontend: http://localhost:5173"
echo "Press Ctrl+C to terminate."

wait
