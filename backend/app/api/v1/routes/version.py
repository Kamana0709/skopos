"""Version endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.settings import get_settings

router = APIRouter()


class VersionResponse(BaseModel):
    """Version response."""
    version: str
    model: str


@router.get("/version", response_model=VersionResponse, tags=["System"])
async def version() -> VersionResponse:
    """
    Return backend build/version metadata.
    
    Returns:
        VersionResponse with version and model information
    """
    settings = get_settings()
    return VersionResponse(version=settings.app_version, model=settings.claude_model)