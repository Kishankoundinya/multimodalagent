import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.utils.config import settings
from backend.app.utils.logging import logger
from backend.app.database.database import init_db, get_all_documents
from backend.app.rag.vector_store import get_vector_store_count
from backend.app.models.schemas import HealthResponse

# Routers
from backend.app.api.documents import router as documents_router
from backend.app.api.research import router as research_router
from backend.app.api.metrics import router as metrics_router
from backend.app.api.comparison import router as comparison_router
from backend.app.api.reports import router as reports_router
from backend.app.api.settings import router as settings_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    settings.ensure_directories()
    init_db()
    logger.info("Application startup sequence completed.")
    yield
    # Shutdown
    logger.info("Application shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent AI Analysis System for Financial Research and Business Insights",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(documents_router)
app.include_router(research_router)
app.include_router(metrics_router)
app.include_router(comparison_router)
app.include_router(reports_router)
app.include_router(settings_router)

@app.get("/api/health", response_model=HealthResponse)
def health_check():
    """System health check and diagnostic status."""
    try:
        docs = get_all_documents()
        doc_count = len(docs)
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
        doc_count = 0

    try:
        chunk_count = get_vector_store_count()
        chroma_status = f"connected ({chunk_count} chunks indexed)"
    except Exception as e:
        chroma_status = f"error: {e}"

    return HealthResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        llm_model=settings.LLM_MODEL,
        device=settings.DEVICE,
        embedding_model=settings.EMBEDDING_MODEL,
        database_status=db_status,
        chromadb_status=chroma_status,
        indexed_documents_count=doc_count,
    )

# Production Unified Hosting: Serve built React frontend if dist exists
frontend_dist_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
    "dist"
)
if os.path.exists(frontend_dist_path):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="static")
    logger.info(f"Mounted frontend static build from {frontend_dist_path}")
