"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.settings import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """
    Liveness/readiness probe for AWS App Runner.
    
    Returns:
        HealthResponse with status and version
    """
    settings = get_settings()
    return HealthResponse(status="ok", version=settings.app_version)