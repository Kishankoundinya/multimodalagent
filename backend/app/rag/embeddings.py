import os
import json
import time
import urllib.request
import urllib.error
from typing import Optional, List
from langchain_core.embeddings import Embeddings
from backend.app.utils.config import settings
from backend.app.utils.logging import logger

_embedding_instance: Optional[Embeddings] = None

class GeminiCloudEmbeddings(Embeddings):
    """
    Ultra-lightweight cloud embeddings using Google Gemini API.
    Zero local PyTorch RAM overhead (~0MB vs 420MB), perfectly fitting 512MB hosting limit.
    Configured to 384 dimensions matching all-MiniLM-L6-v2 and Chroma DB.
    """
    def __init__(self, api_key: str, dimension: int = 384):
        self.api_key = api_key
        self.dimension = dimension
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001"
        self._query_cache = {}

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        
        all_embeddings: List[List[float]] = []
        batch_size = 50  # Up to 100 supported per batchEmbedContents request

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            requests = [
                {
                    "model": "models/gemini-embedding-001",
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": self.dimension
                }
                for t in batch
            ]
            payload = json.dumps({"requests": requests}).encode("utf-8")
            url = f"{self.base_url}:batchEmbedContents?key={self.api_key}"
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

            max_retries = 6
            for attempt in range(max_retries):
                try:
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        res = json.loads(resp.read().decode())
                        embs = [item["values"] for item in res.get("embeddings", [])]
                        all_embeddings.extend(embs)
                        break
                except urllib.error.HTTPError as e:
                    if e.code == 429 and attempt < max_retries - 1:
                        sleep_s = 5 * (attempt + 1) + 2
                        logger.warning(f"Gemini embedding rate limit hit (429), waiting {sleep_s}s before retry {attempt + 1}/{max_retries}...")
                        time.sleep(sleep_s)
                    else:
                        logger.error(f"Error fetching Gemini batch embeddings: {e}")
                        raise e
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        raise e

            if i + batch_size < len(texts):
                time.sleep(1.0)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        if text in self._query_cache:
            return self._query_cache[text]

        payload = json.dumps({
            "model": "models/gemini-embedding-001",
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": self.dimension
        }).encode("utf-8")
        url = f"{self.base_url}:embedContent?key={self.api_key}"
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})

        with urllib.request.urlopen(req, timeout=15) as resp:
            res = json.loads(resp.read().decode())
            embedding = res["embedding"]["values"]

        if len(self._query_cache) > 500:
            self._query_cache.clear()
        self._query_cache[text] = embedding
        return embedding


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
    """Lazy fallback SentenceTransformer wrapper when no Gemini API key is configured."""
    def __init__(self, model_name: str, device: str):
        self._query_cache = {}
        from sentence_transformers import SentenceTransformer
        try:
            self.model = SentenceTransformer(model_name, device=device, local_files_only=True)
        except Exception:
            self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        import gc
        all_embeddings: List[List[float]] = []
        batch_size = 16
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i + batch_size]
            try:
                import torch
                with torch.inference_mode():
                    embs = self.model.encode(chunk, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)
            except Exception:
                embs = self.model.encode(chunk, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)
            all_embeddings.extend(embs.tolist())
            gc.collect()
        return all_embeddings

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


def reset_embeddings():
    """Reset cached embedding model instance."""
    global _embedding_instance
    _embedding_instance = None


def get_embeddings() -> Embeddings:
    """
    Get or lazily initialize the shared embeddings instance.
    Prefers GeminiCloudEmbeddings (0 MB RAM overhead) if GEMINI_API_KEY is available,
    falling back to local SentenceTransformers.
    """
    global _embedding_instance
    if _embedding_instance is not None:
        return _embedding_instance

    gemini_key = (
        settings.GEMINI_API_KEY
        or os.environ.get("GEMINI_API_KEY", "")
        or os.environ.get("GOOGLE_API_KEY", "")
    ).strip()

    if gemini_key:
        logger.info("Using GeminiCloudEmbeddings (models/gemini-embedding-001, 384d) - 0MB local RAM overhead.")
        _embedding_instance = GeminiCloudEmbeddings(api_key=gemini_key, dimension=384)
        return _embedding_instance

    # Fallback to local SentenceTransformer only if no Gemini API key is configured
    model_name = settings.EMBEDDING_MODEL
    device = get_device()
    logger.info(f"Fallback: Initializing local embedding model {model_name} on device {device}")
    _embedding_instance = DirectSTEmbeddings(model_name=model_name, device=device)
    logger.info("Local embedding model loaded successfully.")
    return _embedding_instance
