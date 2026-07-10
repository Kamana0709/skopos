"""Internal domain models."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedSection:
    """Represents a parsed section from the recommendation."""
    name: str
    content: str = ""
    is_complete: bool = False


@dataclass
class StreamMetrics:
    """Metrics for a streaming session."""
    chunk_count: int = 0
    first_byte_time_ms: Optional[float] = None
    start_time_ms: float = 0.0
    output_tokens_estimate: int = 0