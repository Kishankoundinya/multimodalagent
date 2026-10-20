import os
import threading
from typing import Optional, List, Dict, Any
import httpx
from backend.app.utils.config import settings
from backend.app.utils.logging import logger
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

class SharedLLM:
    """
    Singleton LLM manager backed by Google Gemini API (Free Tier).
    Replaces the local TinyLlama model to eliminate local model downloads,
    RAM footprint, and slow CPU thread inference.
    """
    _instance: Optional["SharedLLM"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.model_name = settings.LLM_MODEL
        self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
        self._gen_cache: Dict[str, str] = {}
        self._is_loaded = False
        self._load_lock = threading.Lock()
        self.load_model()

    @classmethod
    def get_instance(cls) -> "SharedLLM":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def update_credentials(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Update API key and/or model name at runtime."""
        with self._load_lock:
            if api_key is not None:
                self.api_key = api_key.strip()
            if model_name is not None:
                self.model_name = model_name.strip()
            self._is_loaded = False
            self._gen_cache.clear()
            self.load_model()

    def is_loaded(self) -> bool:
        return self._is_loaded

    def load_model(self):
        with self._load_lock:
            if not self.api_key:
                self.api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""

            if not self.api_key:
                logger.warning(
                    "[SharedLLM] Google Gemini API Key is not set. Generation calls will require a key. "
                    "Configure GEMINI_API_KEY in .env or the Settings tab (free tier: https://aistudio.google.com/app/apikey)."
                )
                self._is_loaded = False
                return

            self._is_loaded = True
            logger.info(f"[SharedLLM] Google Gemini configured for model '{self.model_name}' (Free tier).")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate grounded text using Google Gemini REST API with automatic multi-model fallback and in-memory caching.
        """
        if not self._is_loaded:
            self.load_model()

        if not self.api_key:
            error_msg = (
                "GEMINI_API_KEY is not configured. Please add your free Google Gemini API Key "
                "in .env or via the Settings page in the UI (obtain a free key from https://aistudio.google.com/app/apikey)."
            )
            logger.error(f"[SharedLLM] {error_msg}")
            raise RuntimeError(error_msg)

        max_tokens = max_new_tokens or settings.MAX_NEW_TOKENS
        temp = temperature if temperature is not None else settings.TEMPERATURE
        sys_msg = system_prompt or "You are a financial document analysis assistant. Use only the supplied source context. Do not use unsupported knowledge."

        cache_key = f"{self.model_name}_{sys_msg}_{prompt}_{max_tokens}_{temp}"
        if cache_key in self._gen_cache:
            logger.info("Serving LLM output from in-memory inference cache (0ms).")
            return self._gen_cache[cache_key]

        # Determine candidate models to try in order of availability & resilience
        clean_model = self.model_name.replace("models/", "")
        candidate_models = [clean_model]
        fallbacks = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash",
            "gemini-2.5-flash",
        ]
        for fb in fallbacks:
            if fb not in candidate_models:
                candidate_models.append(fb)

        last_error = None

        for current_model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent?key={self.api_key}"
            payload: Dict[str, Any] = {
                "system_instruction": {
                    "parts": [{"text": sys_msg}]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": float(temp),
                    "maxOutputTokens": int(max_tokens)
                }
            }

            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                result = parts[0]["text"].strip()
                                if len(self._gen_cache) > 256:
                                    self._gen_cache.clear()
                                self._gen_cache[cache_key] = result
                                return result
                    else:
                        logger.warning(f"[SharedLLM] Model '{current_model}' HTTP {resp.status_code}: {resp.text[:120]}")
                        last_error = RuntimeError(f"Gemini API {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                logger.warning(f"[SharedLLM] Model '{current_model}' request error: {e}")
                last_error = e
                # Fail fast if there is no internet connection or host resolution fails
                err_str = str(e).lower()
                if "connect" in err_str or "nodename" in err_str or "servname" in err_str or "timed out" in err_str:
                    logger.warning("[SharedLLM] Network unreachable or timed out; stopping model cascade.")
                    break

        logger.error(f"[SharedLLM] All Gemini candidate models failed. Last error: {last_error}")
        raise last_error or RuntimeError("Gemini API generation failed.")

    def get_langchain_llm(self) -> "GeminiLLM":
        return GeminiLLM()


class GeminiLLM(LLM):
    """LangChain-native LLM wrapper for Shared Gemini instance."""
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        shared = SharedLLM.get_instance()
        return shared.generate(prompt=prompt, **kwargs)

    @property
    def _llm_type(self) -> str:
        return "gemini"


# Backwards compatibility alias
LocalTinyLlamaLLM = GeminiLLM

def get_shared_llm() -> SharedLLM:
    return SharedLLM.get_instance()

def get_langchain_llm() -> GeminiLLM:
    return GeminiLLM()
