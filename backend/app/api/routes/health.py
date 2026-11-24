"""Health check endpoint used to confirm that the API is running."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
def read_health() -> HealthResponse:
    """Report that the service is up, with its name and version."""
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)
