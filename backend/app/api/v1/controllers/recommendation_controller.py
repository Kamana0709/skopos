"""Thin orchestration between route and service."""

import logging
from fastapi import Request
from fastapi.responses import StreamingResponse

from app.schemas.profile import UserProfile
from app.services.recommendation_service import RecommendationService
from app.core.clients.claude_client import ClaudeClient
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class RecommendationController:
    """Controller for recommendation endpoint orchestration."""
    
    def __init__(self, claude_client: ClaudeClient, settings: Settings):
        self.claude_client = claude_client
        self.settings = settings
        self.service = RecommendationService(claude_client, settings)
    
    async def handle(self, request: Request, profile: UserProfile, correlation_id: str):
        """
        Handle recommendation request and return streaming response.
        
        Args:
            request: FastAPI request
            profile: Validated user profile
            correlation_id: Correlation ID
            
        Returns:
            StreamingResponse with SSE stream
        """
        # Generate streaming response via service
        async def stream_generator():
            async for chunk in self.service.generate(request, profile, correlation_id):
                yield chunk
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable proxy buffering
            }
        )