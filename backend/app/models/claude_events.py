from dataclasses import dataclass
from typing import Literal, Optional

@dataclass
class ClaudeStreamEvent:
    """Internal event contract yielded by ClaudeClient.stream()"""
    type: Literal["section", "chunk", "done"]
    section: Optional[str] = None  # populated only when type == "section"
    text: Optional[str] = None     # populated only when type == "chunk"
    
    def __post_init__(self):
        if self.type == "section" and self.section is None:
            raise ValueError("section event must have a section value")
        if self.type == "chunk" and self.text is None:
            raise ValueError("chunk event must have a text value")