"""Application configuration loaded from environment variables."""
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "cloud-ml-platform backend"
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://mlplatform:mlplatform@postgres:5432/mlplatform"
    )
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    experiment_queue: str = "experiments:queued"


@lru_cache
def get_settings() -> Settings:
    return Settings()
