import os
from pathlib import Path
from fastapi import APIRouter
from backend.app.models.schemas import SettingsResponse, SettingsUpdateRequest
from backend.app.utils.config import settings
from backend.app.llm.llm_provider import get_shared_llm
from backend.app.utils.logging import logger

from backend.app.rag.vector_store import get_chroma_mode, reset_chroma_client

router = APIRouter(prefix="/api/settings", tags=["Settings"])

def _persist_env_var(key: str, value: str):
    """Safely update or add an environment variable in the root .env file."""
    try:
        env_file = Path(settings.BASE_DIR) / ".env"
        if not env_file.exists():
            # Create if missing
            env_file.write_text(f"{key}={value}\n", encoding="utf-8")
            return

        lines = env_file.read_text(encoding="utf-8").splitlines()
        found = False
        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"{key}={value}")

        env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except Exception as e:
        logger.warning(f"Could not persist {key} to .env: {e}")

@router.get("", response_model=SettingsResponse)
def get_current_settings():
    has_key = bool(
        settings.GEMINI_API_KEY
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    has_chroma_key = bool(
        settings.CHROMA_DB_API_KEY
        or settings.CHROMA_API_KEY
        or os.environ.get("CHROMA_DB_API_KEY")
        or os.environ.get("CHROMA_API_KEY")
    )
    return SettingsResponse(
        app_name=settings.APP_NAME,
        llm_model=settings.LLM_MODEL,
        gemini_api_key_configured=has_key,
        chroma_db_api_key_configured=has_chroma_key,
        chroma_mode=get_chroma_mode(),
        device=settings.DEVICE,
        temperature=settings.TEMPERATURE,
        max_new_tokens=settings.MAX_NEW_TOKENS,
        embedding_model=settings.EMBEDDING_MODEL,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        top_k=settings.TOP_K,
        max_retrieval_steps=settings.MAX_RETRIEVAL_STEPS,
        max_file_size_mb=settings.MAX_FILE_SIZE_MB,
    )

@router.post("", response_model=SettingsResponse)
def update_settings(update: SettingsUpdateRequest):
    shared = get_shared_llm()

    if update.gemini_api_key is not None and update.gemini_api_key.strip():
        cleaned_key = update.gemini_api_key.strip()
        settings.GEMINI_API_KEY = cleaned_key
        os.environ["GEMINI_API_KEY"] = cleaned_key
        _persist_env_var("GEMINI_API_KEY", cleaned_key)
        shared.update_credentials(api_key=cleaned_key)
        logger.info("Updated GEMINI_API_KEY successfully.")

    if update.llm_model is not None and update.llm_model.strip():
        cleaned_model = update.llm_model.strip()
        settings.LLM_MODEL = cleaned_model
        os.environ["LLM_MODEL"] = cleaned_model
        _persist_env_var("LLM_MODEL", cleaned_model)
        shared.update_credentials(model_name=cleaned_model)
        logger.info(f"Updated LLM_MODEL to '{cleaned_model}'.")

    if update.chroma_db_api_key is not None and update.chroma_db_api_key.strip():
        cleaned_key = update.chroma_db_api_key.strip()
        settings.CHROMA_DB_API_KEY = cleaned_key
        os.environ["CHROMA_DB_API_KEY"] = cleaned_key
        _persist_env_var("CHROMA_DB_API_KEY", cleaned_key)
        reset_chroma_client()
        logger.info("Updated CHROMA_DB_API_KEY and reset Chroma client successfully.")

    if update.chroma_server_host is not None:
        cleaned_host = update.chroma_server_host.strip()
        settings.CHROMA_SERVER_HOST = cleaned_host
        os.environ["CHROMA_SERVER_HOST"] = cleaned_host
        _persist_env_var("CHROMA_SERVER_HOST", cleaned_host)
        reset_chroma_client()
        logger.info(f"Updated CHROMA_SERVER_HOST to '{cleaned_host}'.")

    if update.temperature is not None:
        settings.TEMPERATURE = update.temperature
    if update.max_new_tokens is not None:
        settings.MAX_NEW_TOKENS = update.max_new_tokens
    if update.chunk_size is not None:
        settings.CHUNK_SIZE = update.chunk_size
    if update.chunk_overlap is not None:
        settings.CHUNK_OVERLAP = update.chunk_overlap
    if update.top_k is not None:
        settings.TOP_K = update.top_k
    if update.max_retrieval_steps is not None:
        settings.MAX_RETRIEVAL_STEPS = update.max_retrieval_steps

    return get_current_settings()
