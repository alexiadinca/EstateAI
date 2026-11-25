"""Entry point of the EstateAI backend.

Run locally with: uv run uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analyses, health, users
from app.core.config import get_settings
from app.db.session import DatabaseNotConfiguredError


def handle_database_not_configured(
    request: Request, error: DatabaseNotConfiguredError
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "The database is not configured. Set DATABASE_URL in backend/.env."},
    )


def create_app() -> FastAPI:
    """Build the FastAPI application with its middleware and routes."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Property valuation, offer comparison and investment analysis for EstateAI.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(DatabaseNotConfiguredError, handle_database_not_configured)

    app.include_router(health.router)
    app.include_router(users.router)
    app.include_router(analyses.router)

    return app


app = create_app()
