"""Database engine and session management for the Supabase PostgreSQL database."""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


class DatabaseNotConfiguredError(RuntimeError):
    """Raised when a database operation is requested but DATABASE_URL is not set."""


@lru_cache
def get_engine() -> Engine:
    """Create the SQLAlchemy engine once per process, on first use."""
    database_url = get_settings().database_url
    if database_url is None:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not set. Add it to backend/.env (see .env.example)."
        )
    # pool_pre_ping replaces connections that the Supabase pooler closed while idle.
    return create_engine(database_url, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db_session() -> Iterator[Session]:
    """FastAPI dependency that provides one session per request and always closes it."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()
