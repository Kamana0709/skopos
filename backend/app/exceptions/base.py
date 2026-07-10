"""Base exception classes."""

from typing import Optional


class AppException(Exception):
    """Base application exception."""
    code: str = "INTERNAL_ERROR"
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        self.message = message
        self.user_message = user_message or "An unexpected error occurred."
        super().__init__(message)