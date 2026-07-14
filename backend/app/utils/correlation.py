"""Correlation ID management using contextvars."""

import uuid
from contextvars import ContextVar

# Context variable for correlation ID
_correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="unknown")


def generate_correlation_id() -> str:
    """Generate a unique correlation ID."""
    return uuid.uuid4().hex[:16]


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context."""
    _correlation_id_var.set(correlation_id)


def get_correlation_id() -> str:
    """Get the correlation ID for the current context."""
    return _correlation_id_var.get()