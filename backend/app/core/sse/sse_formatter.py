class SSEFormatter:
    """Formats events for Server-Sent Events (SSE) streaming."""
    
    def section_event(self, section: str) -> str:
        """Format a section boundary event."""
        return f"event: section\ndata: {{\"section\": \"{section}\"}}\n\n"
    
    def chunk_event(self, text: str) -> str:
        """Format a text chunk event."""
        # Escape JSON string properly
        import json
        text = json.dumps(text)[1:-1]  # Remove quotes
        return f"event: chunk\ndata: {{\"text\": \"{text}\"}}\n\n"
    
    def done_event(self) -> str:
        """Format a completion event."""
        return "event: done\ndata: {\"status\": \"complete\"}\n\n"
    
    def error_event(self, code: str, message: str) -> str:
        """Format an error event."""
        return f"event: error\ndata: {{\"code\": \"{code}\", \"message\": \"{message}\"}}\n\n"
    
"""SSE event formatting utilities."""

import json
from typing import Any, Dict, Optional


def format_sse_event(event_type: str, data: Dict[str, Any]) -> str:
    """
    Format an SSE event according to the specification.
    
    Args:
        event_type: Event type (e.g., "section", "chunk", "done", "error")
        data: Data payload
        
    Returns:
        Formatted SSE event string
    """
    # Ensure data is JSON serializable
    data_str = json.dumps(data, ensure_ascii=False)
    
    # Format: event: {type}\ndata: {json}\n\n
    return f"event: {event_type}\ndata: {data_str}\n\n"


def format_keepalive_ping() -> str:
    """Format a keepalive ping (comment frame)."""
    return ": ping\n\n"


def format_section_event(section: str) -> str:
    """Format a section event."""
    return format_sse_event("section", {"section": section})


def format_chunk_event(text: str) -> str:
    """Format a chunk event."""
    return format_sse_event("chunk", {"text": text})


def format_done_event() -> str:
    """Format a done event."""
    return format_sse_event("done", {"status": "complete"})


def format_error_event(code: str, message: str, correlation_id: str) -> str:
    """Format an error event."""
    return format_sse_event(
        "error",
        {
            "code": code,
            "message": message,
            "correlation_id": correlation_id,
        }
    )