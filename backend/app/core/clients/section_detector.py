"""
Section Detector
Purpose: Detects Markdown section boundaries in streaming Claude output
Owns: Header detection and canonical key mapping
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class SectionDetector:
    """
    Streaming-safe section boundary detector.
    Works on a rolling line buffer to handle headers split across SSE boundaries.
    """
    
    # Fixed header → canonical section key mapping
    HEADER_TO_SECTION: Dict[str, str] = {
        "## Roadmap": "roadmap",
        "## Skill Gap Analysis": "skill_gap_analysis",
        "## Certifications": "certifications",
        "## Projects": "projects",
        "## Learning Resources": "learning_resources",
        "## Career Guidance": "career_guidance",
    }
    
    # Reverse mapping for logging
    SECTION_TO_HEADER: Dict[str, str] = {
        v: k for k, v in HEADER_TO_SECTION.items()
    }
    
    # Expected section order
    EXPECTED_ORDER = [
        "roadmap",
        "skill_gap_analysis", 
        "certifications",
        "projects",
        "learning_resources",
        "career_guidance",
    ]
    
    def __init__(self):
        self._line_buffer = ""
        self._current_section = None
        self._detected_sections = set()
        self._has_any_header = False
        
    def process_chunk(self, text: str) -> Tuple[Optional[str], str]:
        """
        Process a text chunk from Claude's stream.
        
        Args:
            text: Text delta from Claude
            
        Returns:
            Tuple of (section_key_or_None, text_to_forward)
            - If a new section header is detected: returns (section_key, "")
            - If no header: returns (None, text)
        """
        # Append to line buffer (headers could be split across chunks)
        self._line_buffer += text
        
        # Process complete lines
        lines = self._line_buffer.split("\n")
        self._line_buffer = lines.pop() if lines else ""
        
        for line in lines:
            # Check for section header at start of line
            section = self._detect_header(line)
            if section:
                # This is a section boundary - don't forward the header text
                self._current_section = section
                self._detected_sections.add(section)
                self._has_any_header = True
                logger.debug(
                    "Section detected",
                    extra={
                        "event": "section_detected",
                        "section": section,
                        "header": line.strip(),
                    }
                )
                # Signal section change with empty text
                return section, ""
        
        # No header detected in this chunk - forward text
        return None, text
    
    def _detect_header(self, line: str) -> Optional[str]:
        """Check if a line starts with a known Markdown header."""
        # Match: starts with "## ", followed by text that exactly matches a known header
        # Using regex for streaming safety (^ line start)
        match = re.match(r"^##\s+(.+)$", line.strip())
        if not match:
            return None
        
        header_text = match.group(1)
        
        # Check against known headers
        for header, section in self.HEADER_TO_SECTION.items():
            if header_text == header.replace("## ", ""):
                return section
        
        # Unknown header - log and treat as regular text
        logger.warning(
            "Unknown section header detected",
            extra={
                "event": "unknown_header",
                "header": header_text,
                "line": line.strip(),
            }
        )
        return None
    
    def get_current_section(self) -> Optional[str]:
        """Get the most recently detected section."""
        return self._current_section
    
    def has_any_headers(self) -> bool:
        """Check if any headers were detected."""
        return self._has_any_header
    
    def get_missing_sections(self) -> list:
        """Check which expected sections were not detected."""
        return [s for s in self.EXPECTED_ORDER if s not in self._detected_sections]
    
    def is_complete(self) -> bool:
        """Check if all expected sections were detected."""
        return len(self._detected_sections) == len(self.EXPECTED_ORDER)
    
    def reset(self):
        """Reset detector state for a new stream."""
        self._line_buffer = ""
        self._current_section = None
        self._detected_sections = set()
        self._has_any_header = False