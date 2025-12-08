from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    database_url: str
    openai_api_key: Optional[str] = None  # Para embeddings y RAG
    openrouter_api_key: Optional[str] = None  # Para generacion de SQL con LLM
    redis_url: str = "redis://localhost:6379"  # Redis para caché de stats
    redis_cache_ttl: int = 86400  # 24 horas en segundos
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()


