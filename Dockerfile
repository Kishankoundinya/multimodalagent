# ========================================================
# Stage 1: Build Frontend (Vite + React)
# ========================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ========================================================
# Stage 2: Python Backend & Production Runtime
# ========================================================
FROM python:3.12-slim AS runner

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install lightweight CPU-only PyTorch (saves ~800MB download and ~250MB RAM)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# 2. Install remaining Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# 3. Pre-download embedding model during build so container startup uses 0 network and loads instantly
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy Backend & Pre-loaded data (documents, vector store, SQLite DB)
COPY backend ./backend
COPY data ./data

# Copy built frontend from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure data directories exist
RUN mkdir -p /app/data/documents /app/data/chromadb /app/data/reports /app/data/seed

# Environment variables optimized for low RAM (<512MB) cloud instances
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    MALLOC_ARENA_MAX=2 \
    TOKENIZERS_PARALLELISM=false \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Start FastAPI server with 1 worker to conserve RAM
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
