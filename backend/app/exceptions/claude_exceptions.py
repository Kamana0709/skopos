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