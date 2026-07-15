"""
ClaudeClient
Purpose: Single Anthropic SDK integration point
Owns: All Claude API calls, retry policy, timeout handling, event translation
Dependencies: AsyncAnthropic SDK (import restricted to this file)
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional
import time

from anthropic import AsyncAnthropic
from anthropic import APIError, APITimeoutError, RateLimitError, APIStatusError

from app.exceptions.claude_exceptions import (
    ClaudeAPIError,
    ClaudeAuthError,
    ClaudeOverloadedError,
    ClaudeTimeoutError,
)
from app.config.settings import Settings



from anthropic.types import MessageStreamEvent
from app.models.claude_events import ClaudeStreamEvent
from app.exceptions.claude_exceptions import *
"""from app.core.settings import Settings  # from backend module"""
from app.core.clients.section_detector import SectionDetector

logger = logging.getLogger(__name__)

class ClaudeClient:
    """
    Sole entry point for Anthropic SDK interaction.
    Implements retry policy, timeout handling, and event translation.
    """
    
    def __init__(
        self, 
        client: AsyncAnthropic, 
        settings: Settings,
        correlation_id: Optional[str] = None
    ):
        """
        Args:
            client: Authenticated AsyncAnthropic singleton (DI-provided)
            settings: Backend Settings object (single source of truth)
            correlation_id: Request correlation ID for logging
        """
        self._client = client
        self._settings = settings
        self._correlation_id = correlation_id
        
        # Configuration from settings
        self._model = settings.CLAUDE_MODEL
        self._max_tokens = settings.CLAUDE_MAX_TOKENS
        self._temperature = settings.CLAUDE_TEMPERATURE
        self._connection_timeout = 10.0  # seconds
        self._stream_timeout = settings.STREAM_TIMEOUT_SECONDS
        
        # Retry configuration
        self._max_retries = 3
        self._base_delay = 0.5  # seconds
        
        # Section detector
        self._section_detector = SectionDetector()
        
    async def stream(
        self, 
        system_prompt: str, 
        user_prompt: str
    ) -> AsyncGenerator[ClaudeStreamEvent, None]:
        """
        Stream Claude's response with retry, timeout, and section detection.
        
        Args:
            system_prompt: System instruction
            user_prompt: User message content
            
        Yields:
            ClaudeStreamEvent: section, chunk, or done events
            
        Raises:
            ClaudeAuthError: Authentication failure (not retryable)
            ClaudeInvalidRequestError: Prompt construction bug (not retryable)
            ClaudeTimeoutError: Connection timeout (retryable)
            ClaudeStreamTimeoutError: Stream timeout (not retryable)
            ClaudeRetryExhaustedError: All retries failed
        """
        self._section_detector.reset()
        
        logger.info(
            "Claude stream started",
            extra={
                "event": "claude_stream_started",
                "correlation_id": self._correlation_id,
                "model": self._model,
                "max_tokens": self._max_tokens,
                "temperature": self._temperature,
            }
        )
        
        retry_count = 0
        last_error = None
        
        while retry_count < self._max_retries:
            try:
                async for event in self._stream_with_timeout(system_prompt, user_prompt):
                    yield event
                
                # Stream completed successfully
                await self._handle_stream_complete()
                return
                
            except (ClaudeOverloadedError, ClaudeRateLimitError, ClaudeServiceError, ClaudeTimeoutError) as e:
                # Retryable errors
                retry_count += 1
                last_error = e
                
                if retry_count >= self._max_retries:
                    logger.error(
                        "Claude retry exhausted",
                        extra={
                            "event": "claude_retry_exhausted",
                            "correlation_id": self._correlation_id,
                            "retry_count": retry_count,
                            "error_type": type(e).__name__,
                        }
                    )
                    raise ClaudeRetryExhaustedError(
                        f"All {self._max_retries} retry attempts failed: {e}"
                    ) from e
                
                # Exponential backoff with optional retry-after hint
                delay = self._calculate_backoff(e, retry_count)
                logger.warning(
                    "Claude retry attempt",
                    extra={
                        "event": "claude_retry",
                        "correlation_id": self._correlation_id,
                        "retry_count": retry_count,
                        "delay": delay,
                        "error_type": type(e).__name__,
                    }
                )
                await asyncio.sleep(delay)
                
            except (ClaudeAuthError, ClaudeInvalidRequestError, ClaudeStreamTimeoutError):
                # Non-retryable errors - raise immediately
                raise
                
            except Exception as e:
                # Unexpected error - log and re-raise
                logger.error(
                    "Unexpected Claude error",
                    extra={
                        "event": "claude_unexpected_error",
                        "correlation_id": self._correlation_id,
                        "error": str(e),
                    }
                )
                raise
    
    async def _stream_with_timeout(
        self, 
        system_prompt: str, 
        user_prompt: str
    ) -> AsyncGenerator[ClaudeStreamEvent, None]:
        """Execute stream with timeout protection."""
        try:
            # Connect with connection timeout (10s)
            stream = await asyncio.wait_for(
                self._client.messages.stream(
                    model=self._model,
                    max_tokens=self._max_tokens,
                    temperature=self._temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                ),
                timeout=self._connection_timeout,
            )
            
            # Process stream with total timeout (60s default)
            try:
                async with stream:
                    # Watchdog for total stream timeout
                    stream_task = asyncio.create_task(
                        self._process_stream_events(stream)
                    )
                    
                    try:
                        async for event in asyncio.wait_for(
                            stream_task,
                            timeout=self._stream_timeout,
                        ):
                            yield event
                    except asyncio.TimeoutError:
                        stream_task.cancel()
                        raise ClaudeStreamTimeoutError(
                            f"Stream exceeded timeout of {self._stream_timeout}s"
                        )
                        
            except asyncio.TimeoutError:
                raise ClaudeTimeoutError("Connection timed out")
                
        except asyncio.TimeoutError:
            raise ClaudeTimeoutError(f"Connection timeout after {self._connection_timeout}s")
    
    async def _process_stream_events(
        self, 
        stream
    ) -> AsyncGenerator[ClaudeStreamEvent, None]:
        """Process raw SDK events and translate to ClaudeStreamEvents."""
        current_section = None
        yielded_section = False
        
        async for event in stream:
            # Translate SDK event types
            if event.type == "content_block_delta":
                if event.delta.type == "text_delta":
                    text = event.delta.text
                    
                    # Section detection
                    section, text_to_forward = self._section_detector.process_chunk(text)
                    
                    # Handle section boundary
                    if section:
                        current_section = section
                        yielded_section = True
                        yield ClaudeStreamEvent(
                            type="section",
                            section=section,
                        )
                    
                    # Forward text chunk
                    if text_to_forward:
                        yield ClaudeStreamEvent(
                            type="chunk",
                            text=text_to_forward,
                        )
                        
            elif event.type == "message_stop":
                # Stream complete
                yield ClaudeStreamEvent(type="done")
                break
                
            elif event.type == "error":
                # Handle error events
                error_msg = getattr(event, "error", {}).get("message", "Unknown error")
                error_type = getattr(event, "error", {}).get("type", "unknown")
                self._handle_sdk_error(error_type, error_msg)
                
            else:
                # Unknown event type - log at DEBUG and skip
                logger.debug(
                    "Unknown SDK event type",
                    extra={
                        "event": "unknown_sdk_event",
                        "event_type": event.type,
                        "correlation_id": self._correlation_id,
                    }
                )
    
    def _handle_sdk_error(self, error_type: str, error_msg: str) -> None:
        """Map SDK error types to internal exceptions."""
        error_map = {
            "authentication_error": ClaudeAuthError,
            "permission_error": ClaudeAuthError,
            "invalid_request_error": ClaudeInvalidRequestError,
            "overloaded_error": ClaudeOverloadedError,
            "rate_limit_error": ClaudeRateLimitError,
            "api_error": ClaudeServiceError,
        }
        
        exc_class = error_map.get(error_type, ClaudeServiceError)
        raise exc_class(f"{error_type}: {error_msg}")
    
    def _calculate_backoff(self, error: Exception, retry_count: int) -> float:
        """Calculate backoff delay with optional retry-after hint."""
        # Check if error has retry-after hint
        if hasattr(error, "retry_after"):
            try:
                return float(error.retry_after)
            except (ValueError, TypeError):
                pass
        
        # Exponential backoff: 500ms, 1s, 2s
        return self._base_delay * (2 ** (retry_count - 1))
    
    async def _handle_stream_complete(self) -> None:
        """Log stream completion and check section completeness."""
        missing_sections = self._section_detector.get_missing_sections()
        is_complete = self._section_detector.is_complete()
        
        if not is_complete:
            logger.warning(
                "Incomplete section structure detected",
                extra={
                    "event": "incomplete_section_structure",
                    "correlation_id": self._correlation_id,
                    "missing_sections": missing_sections,
                    "detected_sections": self._section_detector._detected_sections,
                }
            )
        elif not self._section_detector.has_any_headers():
            logger.warning(
                "No section headers detected",
                extra={
                    "event": "no_section_headers_detected",
                    "correlation_id": self._correlation_id,
                }
            )
        
        logger.info(
            "Claude stream completed",
            extra={
                "event": "claude_stream_completed",
                "correlation_id": self._correlation_id,
                "is_complete": is_complete,
                "sections_detected": list(self._section_detector._detected_sections),
            }
        )


        """AsyncAnthropic wrapper - single entry point for Claude API calls."""





class ClaudeClient:
    """
    Wrapper for AsyncAnthropic client with retry logic and centralized configuration.
    
    This is the ONLY module that imports the Anthropic SDK.
    """
    
    def __init__(self, settings: Settings):
        """Initialize Claude client with settings."""
        self.settings = settings
        self._client: Optional[AsyncAnthropic] = None
        self._initialized = False
    
    def _ensure_client(self) -> None:
        """Lazy initialize the AsyncAnthropic client."""
        if not self._initialized:
            try:
                self._client = AsyncAnthropic(
                    api_key=self.settings.anthropic_api_key,
                    max_retries=0,  # We handle retries ourselves
                    timeout=self.settings.connection_timeout_seconds,
                )
                self._initialized = True
                logger.info("claude_client_initialized", extra={"model": self.settings.claude_model})
            except Exception as e:
                raise ClaudeAPIError(f"Failed to initialize Claude client: {e}") from e
    
    async def stream(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 3,
    ) -> AsyncGenerator[str, None]:
        """
        Stream Claude response with retry logic.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_retries: Maximum retry attempts
            
        Yields:
            Text deltas from Claude
            
        Raises:
            ClaudeAuthError: Invalid API key or authentication failure
            ClaudeOverloadedError: Claude service overloaded after retries
            ClaudeTimeoutError: Timeout waiting for response
            ClaudeAPIError: Other API errors
        """
        self._ensure_client()
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.debug(
                    "claude_stream_attempt",
                    extra={"attempt": attempt + 1, "max_retries": max_retries}
                )
                
                async with self._client.messages.stream(
                    model=self.settings.claude_model,
                    max_tokens=self.settings.claude_max_tokens,
                    temperature=self.settings.claude_temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                ) as stream:
                    async for delta in stream.text_stream:
                        yield delta
                    return  # Successful completion
                    
            except APIStatusError as e:
                status_code = e.status_code
                error_body = getattr(e, "body", {})
                error_type = error_body.get("error", {}).get("type", "")
                
                if status_code == 401:
                    # Authentication error - don't retry
                    logger.critical("claude_auth_error", extra={"status_code": status_code})
                    raise ClaudeAuthError("Invalid or missing Anthropic API key")
                elif status_code == 429:
                    # Rate limited - retry with backoff
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(
                            "claude_rate_limit_retry",
                            extra={"attempt": attempt + 1, "wait_time": wait_time}
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error("claude_overloaded", extra={"retries_exhausted": True})
                        raise ClaudeOverloadedError("Claude service is currently overloaded. Please try again later.")
                elif status_code == 500:
                    # Server error - retry with backoff
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise ClaudeAPIError(f"Claude API server error: {e}")
                else:
                    raise ClaudeAPIError(f"Claude API error: {e}")
                    
            except APITimeoutError as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise ClaudeTimeoutError("Timeout waiting for Claude response")
                    
            except RateLimitError as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise ClaudeOverloadedError("Rate limit exceeded. Please try again later.")
                    
            except Exception as e:
                raise ClaudeAPIError(f"Unexpected Claude API error: {e}") from e
        
        # If we exhausted retries
        if last_exception:
            raise ClaudeAPIError(f"Claude API error after {max_retries} retries: {last_exception}")