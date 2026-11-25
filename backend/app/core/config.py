"""Application settings loaded from environment variables and the local .env file."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# SQLAlchemy needs the driver name in the URL. Supabase shows plain "postgresql://" URLs,
# so both common spellings are rewritten to use the psycopg 3 driver.
_POSTGRES_URL_PREFIXES = ("postgresql://", "postgres://")
_PSYCOPG_URL_PREFIX = "postgresql+psycopg://"


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

    # Supabase PostgreSQL connection string (Session pooler). Optional so that the API
    # and its tests can start without a database; database operations fail clearly if missing.
    database_url: str | None = None

    # Supabase project URL, used to verify user access tokens against the project's public keys.
    supabase_url: str | None = None

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip()
        for prefix in _POSTGRES_URL_PREFIXES:
            if value.startswith(prefix):
                return _PSYCOPG_URL_PREFIX + value.removeprefix(prefix)
        return value


@lru_cache
def get_settings() -> Settings:
    """Return a single cached Settings instance for the running process."""
    return Settings()
