"""Recommendation streaming endpoint."""

import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.schemas.profile import UserProfile
from app.api.v1.controllers.recommendation_controller import RecommendationController
from app.core.clients.claude_client import ClaudeClient
from app.utils.correlation import get_correlation_id
from app.config.settings import get_settings, Settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/recommendations/stream")
async def stream_recommendation(
    request: Request,
    profile: UserProfile,
    claude_client: ClaudeClient = Depends(lambda: ClaudeClient(get_settings())),
    correlation_id: str = Depends(get_correlation_id),
    settings: Settings = Depends(get_settings),
):
    """
    Accept user profile and stream personalized AI recommendation via SSE.
    
    Args:
        request: FastAPI request object
        profile: Validated UserProfile
        claude_client: Claude client instance
        correlation_id: Correlation ID for tracing
        settings: Application settings
        
    Returns:
        StreamingResponse with SSE stream
    """
    controller = RecommendationController(claude_client, settings)
    return await controller.handle(request, profile, correlation_id)