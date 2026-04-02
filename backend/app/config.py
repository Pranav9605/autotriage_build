from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/autotriage"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    DEFAULT_TENANT_ID: str = "patil_group"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
    # CORS — comma-separated origins via env, e.g. CORS_ORIGINS="http://localhost:3000,https://app.example.com"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
