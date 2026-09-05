from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Reality Reconstruction Engine"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "rre_insecure_development_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/rre.db"

    # Storage: "LOCAL" or "MINIO"
    STORAGE_BACKEND: Literal["LOCAL", "MINIO"] = "LOCAL"
    LOCAL_STORAGE_DIR: str = "./storage"

    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "rre-evidence"
    MINIO_SECURE: bool = False

    # LLM Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEYS: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_PROVIDER: Literal["GEMINI", "OPENAI", "LOCAL", "AUTO"] = "AUTO"

    def get_gemini_api_keys(self) -> list[str]:
        keys = []
        raw = f"{self.GEMINI_API_KEY},{self.GEMINI_API_KEYS}"
        for item in raw.split(","):
            cleaned = item.strip().strip('"').strip("'")
            if cleaned and cleaned not in keys:
                keys.append(cleaned)
        return keys

    @property
    def primary_gemini_api_key(self) -> str:
        keys = self.get_gemini_api_keys()
        return keys[0] if keys else ""

settings = Settings()
