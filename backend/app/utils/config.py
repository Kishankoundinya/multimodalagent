import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Financial Research AI"
    LLM_MODEL: str = "gemini-flash-lite-latest"
    GEMINI_API_KEY: str = ""
    DEVICE: str = "auto"  # auto, cpu, mps for embeddings
    TEMPERATURE: float = 0.2
    MAX_NEW_TOKENS: int = 1024
    MAX_REPORT_TOKENS: int = 2048
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 15
    MAX_RETRIEVAL_STEPS: int = 2
    MAX_FILE_SIZE_MB: int = 50

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    CHROMA_PERSIST_DIR: str = str(BASE_DIR / "data" / "chromadb")
    SQLITE_DB_PATH: str = str(BASE_DIR / "data" / "financial_research.db")
    SEED_DIR: str = str(BASE_DIR / "data" / "seed")
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "documents")
    REPORT_DIR: str = str(BASE_DIR / "data" / "reports")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def ensure_directories(self):
        for path_str in [
            self.CHROMA_PERSIST_DIR,
            self.SEED_DIR,
            self.UPLOAD_DIR,
            self.REPORT_DIR,
            str(Path(self.SQLITE_DB_PATH).parent),
        ]:
            Path(path_str).mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
