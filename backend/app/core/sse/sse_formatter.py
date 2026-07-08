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