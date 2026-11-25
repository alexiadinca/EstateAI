"""Application settings loaded from environment variables and the local .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration values shared by the whole backend.

    Values are read from environment variables first, then from backend/.env.
    Secrets such as database URLs and Supabase keys must never be hard-coded here.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "EstateAI API"
    app_version: str = "0.1.0"
    environment: str = "development"

    # Browser origins allowed to call the API. The Angular dev server runs on port 4200.
    cors_allowed_origins: list[str] = ["http://localhost:4200"]


@lru_cache
def get_settings() -> Settings:
    """Return a single cached Settings instance for the running process."""
    return Settings()
