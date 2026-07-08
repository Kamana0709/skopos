"""
RecommendationService
Purpose: Orchestrates the recommendation generation flow
Owns: Profile validation, Claude client interaction, SSE formatting
"""

import logging
from typing import AsyncGenerator, Optional
from ..models.user_profile import UserProfile
from ..models.claude_events import ClaudeStreamEvent
from ..core.clients.claude_client import ClaudeClient
from ..core.sse.sse_formatter import SSEFormatter  # from backend module
from ..exceptions.claude_exceptions import *

logger = logging.getLogger(__name__)

class RecommendationService:
    """
    Service layer that orchestrates recommendation generation.
    Called by FastAPI route handlers.
    """
    
    def __init__(
        self,
        claude_client: ClaudeClient,
        sse_formatter: SSEFormatter,
        prompt_builder,  # PromptBuilder instance
    ):
        self._claude_client = claude_client
        self._sse_formatter = sse_formatter
        self._prompt_builder = prompt_builder
    
    async def generate_recommendation(
        self,
        profile: UserProfile,
        correlation_id: str,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a personalized recommendation as SSE-formatted events.
        
        Args:
            profile: Validated UserProfile (already sanitized upstream)
            correlation_id: Request correlation ID for logging
            
        Yields:
            SSE-formatted event strings (ready for HTTP response)
        """
        try:
            # Build prompts
            system_prompt, user_prompt = self._prompt_builder.build(profile)
            
            # Stream from Claude
            async for event in self._claude_client.stream(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            ):
                # Translate internal event to SSE event
                if event.type == "section":
                    yield self._sse_formatter.section_event(event.section)
                elif event.type == "chunk":
                    yield self._sse_formatter.chunk_event(event.text)
                elif event.type == "done":
                    yield self._sse_formatter.done_event()
                    
        except ClaudeRetryExhaustedError as e:
            logger.error(
                "Recommendation generation failed after retries",
                extra={
                    "event": "recommendation_failed",
                    "correlation_id": correlation_id,
                    "error": str(e),
                }
            )
            yield self._sse_formatter.error_event(
                code="CLAUDE_UNREACHABLE",
                message="The AI service is currently unavailable. Please try again later."
            )
            
        except ClaudeAuthError as e:
            logger.critical(
                "Claude authentication failure - check API key",
                extra={
                    "event": "claude_auth_error",
                    "correlation_id": correlation_id,
                    "error": str(e),
                }
            )
            yield self._sse_formatter.error_event(
                code="CLAUDE_AUTH_ERROR",
                message="A configuration error occurred. Please contact support."
            )
            
        except ClaudeStreamTimeoutError as e:
            logger.warning(
                "Claude stream timeout",
                extra={
                    "event": "claude_stream_timeout",
                    "correlation_id": correlation_id,
                    "error": str(e),
                }
            )
            yield self._sse_formatter.error_event(
                code="STREAM_TIMEOUT",
                message="The recommendation is taking longer than expected. Please try again."
            )
            
        except Exception as e:
            logger.error(
                "Unexpected error in recommendation generation",
                extra={
                    "event": "recommendation_error",
                    "correlation_id": correlation_id,
                    "error": str(e),
                }
            )
            yield self._sse_formatter.error_event(
                code="INTERNAL_ERROR",
                message="An unexpected error occurred. Please try again."
            )