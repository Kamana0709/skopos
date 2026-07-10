"""Response schemas."""

from typing import List, Optional, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Individual validation error detail."""
    field: str = Field(..., description="Field name")
    error: str = Field(..., description="Error message")


class ErrorResponse(BaseModel):
    """Standard error response envelope."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="User-friendly error message")
    correlation_id: str = Field(..., description="Correlation ID for tracing")
    details: Optional[List[ErrorDetail]] = Field(None, description="Additional error details")


class VersionResponse(BaseModel):
    """Version response."""
    version: str = Field(..., description="Application version")
    model: str = Field(..., description="Claude model name")


class SSESectionEvent(BaseModel):
    """SSE section event payload."""
    section: str = Field(..., description="Section name")


class SSEChunkEvent(BaseModel):
    """SSE chunk event payload."""
    text: str = Field(..., description="Text chunk")


class SSEDoneEvent(BaseModel):
    """SSE done event payload."""
    status: str = Field(default="complete", description="Completion status")


class SSEErrorEvent(BaseModel):
    """SSE error event payload."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    correlation_id: str = Field(..., description="Correlation ID")