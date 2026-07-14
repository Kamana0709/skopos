"""Input sanitization utilities."""

import re
import html


def sanitize_text(text: str) -> str:
    """
    Sanitize free-text input.
    
    Strips HTML/script tags and normalizes whitespace.
    
    Args:
        text: Raw text input
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    
    # Escape HTML entities
    text = html.escape(text)
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    
    return text