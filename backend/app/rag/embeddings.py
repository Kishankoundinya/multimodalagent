import os
from typing import Optional, List
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

_embedding_instance: Optional[Embeddings] = None

def get_device() -> str:
    target = settings.DEVICE.lower()
    if target == "auto":
        try:
            import torch
            if torch.backends.mps.is_available():
                return "mps"
            elif torch.cuda.is_available():
                return "cuda"
        except Exception:
            pass
        return "cpu"
    elif target in ["mps", "cuda", "cpu"]:
        return target
    return "cpu"

class DirectSTEmbeddings(Embeddings):
    """Clean SentenceTransformer wrapper avoiding LangChain Community deprecations with query caching."""
    def __init__(self, model_name: str, device: str):
        self._query_cache = {}
        try:
            # Try loading cached model offline first
            self.model = SentenceTransformer(model_name, device=device, local_files_only=True)
        except Exception:
            self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            import torch
            with torch.inference_mode():
                embeddings = self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        except Exception:
            embeddings = self.model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        if text in self._query_cache:
            return self._query_cache[text]
        try:
            import torch
            with torch.inference_mode():
                embedding = self.model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0].tolist()
        except Exception:
            embedding = self.model.encode([text], normalize_embeddings=True, show_progress_bar=False)[0].tolist()
            
        if len(self._query_cache) > 500:
            self._query_cache.clear()
        self._query_cache[text] = embedding
        return embedding

def get_embeddings() -> Embeddings:
    """
    Get or lazily initialize the shared Sentence Transformers embedding model.
    Loads once into memory and reuses across calls.
    """
    global _embedding_instance
    if _embedding_instance is not None:
        return _embedding_instance

    model_name = settings.EMBEDDING_MODEL
    device = get_device()
    logger.info(f"Initializing embedding model: {model_name} on device: {device}")

    _embedding_instance = DirectSTEmbeddings(model_name=model_name, device=device)
    logger.info("Embedding model loaded successfully.")
    return _embedding_instance
