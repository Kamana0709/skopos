class ClaudeError(Exception):
    """Base exception for all Claude-related errors"""
    pass

class ClaudeAuthError(ClaudeError):
    """Authentication/permission errors"""
    pass

class ClaudeInvalidRequestError(ClaudeError):
    """Invalid request (prompt construction bug)"""
    pass

class ClaudeOverloadedError(ClaudeError):
    """Anthropic overloaded_error - retryable"""
    pass

class ClaudeRateLimitError(ClaudeError):
    """Anthropic rate limit - retryable"""
    pass

class ClaudeServiceError(ClaudeError):
    """Anthropic 5xx/api_error - retryable"""
    pass

class ClaudeTimeoutError(ClaudeError):
    """Connection/first-byte timeout - retryable"""
    pass

class ClaudeStreamTimeoutError(ClaudeError):
    """Total stream timeout - NOT retryable"""
    pass

class ClaudeRetryExhaustedError(ClaudeError):
    """All retry attempts exhausted"""
    pass

"""Claude API related exceptions."""

from app.exceptions.base import AppException


class ClaudeAPIError(AppException):
    """General Claude API error."""
    code = "CLAUDE_API_ERROR"


class ClaudeAuthError(ClaudeAPIError):
    """Authentication error (invalid API key)."""
    code = "CLAUDE_CONFIG_ERROR"
    
    def __init__(self, message: str):
        super().__init__(message, "Our AI service is currently unavailable. Please try again later.")


class ClaudeOverloadedError(ClaudeAPIError):
    """Claude service overloaded."""
    code = "CLAUDE_OVERLOADED"
    
    def __init__(self, message: str):
        super().__init__(message, "Our AI service is busy - please try again in a moment.")


class ClaudeTimeoutError(ClaudeAPIError):
    """Timeout waiting for Claude response."""
    code = "CLAUDE_TIMEOUT"
    
    def __init__(self, message: str):
        super().__init__(message, "The AI service is taking too long to respond. Please try again.")


class ClaudeStreamTimeoutError(ClaudeAPIError):
    """Stream exceeded total timeout."""
    code = "STREAM_TIMEOUT"
    
    def __init__(self, message: str):
        super().__init__(message, "The recommendation is taking too long to generate. Please try again.")