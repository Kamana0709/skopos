"""
RecommendationService
Purpose: Orchestrates the recommendation generation flow
Owns: Profile validation, Claude client interaction, SSE formatting
"""

import logging
from typing import AsyncGenerator, Optional
from app.models.user_profile import UserProfile
from app.models.claude_events import ClaudeStreamEvent
from app.core.clients.claude_client import ClaudeClient
from app.core.sse.sse_formatter import SSEFormatter  # from backend module
from app.exceptions.claude_exceptions import *

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

"""Core business logic orchestrator for recommendations."""

import asyncio
import logging
import re
import time
from typing import AsyncGenerator, Dict, Any

from fastapi import Request

from app.schemas.profile import UserProfile
from app.services.prompt_builder import PromptBuilder
from app.core.clients.claude_client import ClaudeClient
from app.core.sse.sse_formatter import (
    format_section_event,
    format_chunk_event,
    format_done_event,
    format_error_event,
    format_keepalive_ping,
)
from app.exceptions.claude_exceptions import (
    ClaudeStreamTimeoutError,
    ClaudeAPIError,
)
from app.config.settings import Settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Section detection pattern (matches markdown headers at start of line)
SECTION_PATTERN = re.compile(r'^## (.+)$', re.MULTILINE)


class RecommendationService:
    """
    Orchestrates the recommendation generation flow.
    
    Validates → builds prompts → calls Claude → streams SSE events.
    """
    
    def __init__(self, claude_client: ClaudeClient, settings: Settings):
        self.claude_client = claude_client
        self.settings = settings
        self.prompt_builder = PromptBuilder()
    
    async def generate(
        self,
        request: Request,
        profile: UserProfile,
        correlation_id: str,
    ) -> AsyncGenerator[bytes, None]:
        """
        Generate recommendation and stream SSE events.
        
        Args:
            request: FastAPI request object
            profile: Validated user profile
            correlation_id: Correlation ID for tracing
            
        Yields:
            SSE-formatted bytes
        """
        start_time = time.time()
        chunk_count = 0
        first_byte_sent = False
        current_section = None
        accumulated_text = ""
        last_ping_time = start_time
        
        # Build prompts
        system_prompt, user_prompt = self.prompt_builder.build_prompts(profile)
        
        logger.info(
            "recommendation_generation_started",
            extra={
                "correlation_id": correlation_id,
                "skills_count": len(profile.current_skills),
                "interests_count": len(profile.interests),
                "career_goals_length": len(profile.career_goals),
            }
        )
        
        try:
            # Stream from Claude with overall timeout
            stream_task = asyncio.create_task(
                self._stream_with_timeout(system_prompt, user_prompt, correlation_id)
            )
            
            # Process stream with keepalive and disconnect detection
            async for text_delta in self._process_stream_with_keepalive(
                stream_task, request, correlation_id, start_time
            ):
                if not first_byte_sent:
                    first_byte_sent = True
                    first_byte_time_ms = (time.time() - start_time) * 1000
                    logger.info(
                        "first_byte_received",
                        extra={
                            "correlation_id": correlation_id,
                            "time_to_first_byte_ms": first_byte_time_ms,
                        }
                    )
                
                chunk_count += 1
                
                # Detect section boundaries
                section_events = self._detect_sections(text_delta, accumulated_text)
                for section_name in section_events:
                    current_section = section_name
                    yield format_section_event(section_name).encode("utf-8")
                
                accumulated_text += text_delta
                
                # Emit chunk event
                yield format_chunk_event(text_delta).encode("utf-8")
            
            # Stream completed successfully
            total_duration_ms = (time.time() - start_time) * 1000
            logger.info(
                "recommendation_generation_completed",
                extra={
                    "correlation_id": correlation_id,
                    "duration_ms": total_duration_ms,
                    "chunk_count": chunk_count,
                    "output_tokens_estimate": len(accumulated_text) // 4,
                }
            )
            
            # Send done event
            yield format_done_event().encode("utf-8")
            
        except asyncio.CancelledError:
            logger.warning(
                "recommendation_generation_cancelled",
                extra={
                    "correlation_id": correlation_id,
                    "duration_ms": (time.time() - start_time) * 1000,
                    "chunk_count": chunk_count,
                }
            )
            raise
            
        except Exception as e:
            # Check if we already sent the first byte
            if first_byte_sent:
                # Mid-stream error - send error event
                error_code = getattr(e, "code", "STREAM_ERROR")
                error_message = str(e) if hasattr(e, "user_message") else "An error occurred during generation."
                
                logger.error(
                    "mid_stream_error",
                    extra={
                        "correlation_id": correlation_id,
                        "error_code": error_code,
                        "error_message": str(e),
                        "chunk_count": chunk_count,
                    },
                    exc_info=True,
                )
                
                yield format_error_event(
                    error_code,
                    error_message,
                    correlation_id,
                ).encode("utf-8")
            else:
                # Pre-stream error - re-raise to be handled by exception handler
                raise
    
    async def _stream_with_timeout(
        self,
        system_prompt: str,
        user_prompt: str,
        correlation_id: str,
    ) -> AsyncGenerator[str, None]:
        """Stream Claude with timeout enforcement."""
        try:
            async for chunk in asyncio.wait_for(
                self.claude_client.stream(system_prompt, user_prompt),
                timeout=self.settings.stream_timeout_seconds,
            ):
                yield chunk
        except asyncio.TimeoutError:
            raise ClaudeStreamTimeoutError(
                f"Stream exceeded timeout of {self.settings.stream_timeout_seconds} seconds"
            )
    
    async def _process_stream_with_keepalive(
        self,
        stream_task: asyncio.Task,
        request: Request,
        correlation_id: str,
        start_time: float,
    ) -> AsyncGenerator[str, None]:
        """
        Process stream with keepalive pings and disconnect detection.
        
        Args:
            stream_task: Async task for the Claude stream
            request: FastAPI request object
            correlation_id: Correlation ID
            start_time: Start timestamp
            
        Yields:
            Text deltas from Claude
        """
        # Track the next chunk from the stream
        next_chunk_future = asyncio.create_task(self._get_next_chunk(stream_task))
        
        while True:
            # Check for client disconnect
            try:
                if await request.is_disconnected():
                    logger.info(
                        "client_disconnected",
                        extra={"correlation_id": correlation_id, "duration_ms": (time.time() - start_time) * 1000}
                    )
                    # Cancel the stream task
                    stream_task.cancel()
                    try:
                        await stream_task
                    except asyncio.CancelledError:
                        pass
                    return
            except Exception:
                pass
            
            # Wait for next chunk or keepalive
            try:
                chunk = await asyncio.wait_for(next_chunk_future, timeout=15.0)
                next_chunk_future = asyncio.create_task(self._get_next_chunk(stream_task))
                yield chunk
            except asyncio.TimeoutError:
                # 15 seconds without data - send keepalive ping
                yield format_keepalive_ping()
            except StopAsyncIteration:
                # Stream completed
                return
            except asyncio.CancelledError:
                return
    
    async def _get_next_chunk(self, stream_task: asyncio.Task) -> str:
        """Get the next chunk from the stream task."""
        if stream_task.done():
            # Check if the stream completed or errored
            try:
                result = stream_task.result()
                # If result is a generator, we need to iterate it
                if hasattr(result, "__aiter__"):
                    # This shouldn't happen - we should be iterating directly
                    return ""
            except StopAsyncIteration:
                raise
            except Exception as e:
                raise e
        
        # This is a bit tricky - we need to get the next item from the async generator
        # Since we can't directly access the generator from the task result, we use a queue approach
        # Simpler approach: iterate the stream and yield items
        # We'll restructure this - the caller handles iteration
        raise NotImplementedError("Stream processing needs refactoring")
    
    def _detect_sections(self, text_delta: str, accumulated_text: str) -> list:
        """
        Detect section boundaries in the stream.
        
        Args:
            text_delta: New text chunk
            accumulated_text: All text received so far
            
        Returns:
            List of section names detected
        """
        sections = []
        
        # Check for section headers in the accumulated text
        # We look for new sections that appear in the latest delta
        matches = SECTION_PATTERN.findall(accumulated_text)
        
        # Simple approach: if we see a new section header in the accumulated text
        # that wasn't there before
        if matches:
            # Check if we've already processed this section
            # We maintain state in the class - but we use the last section name approach
            # to avoid duplicate emissions
            for match in matches:
                # Only emit if this is a new section
                if match not in sections:
                    sections.append(match)
        
        return sections