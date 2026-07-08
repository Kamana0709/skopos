"""
PromptBuilder Service
Purpose: Transforms a validated UserProfile into system and user prompt pair
Owns: All prompt construction logic, injection defense
Dependencies: prompts/* modules
"""

import logging
from typing import Tuple
from ..models.user_profile import UserProfile
from ..prompts.system_prompt import SYSTEM_PROMPT_V1, SYSTEM_PROMPT_VERSION
from ..prompts.recommendation_prompt import build_recommendation_prompt

logger = logging.getLogger(__name__)

class PromptBuilder:
    """
    Builds system and user prompts from a validated UserProfile.
    Implements three layers of prompt injection defense:
    1. Delimiting: All user content inside <profile> tags
    2. Model-level instruction: System prompt explicitly treats <profile> as data
    3. Sanitization: Strips delimiter tags from user-supplied values
    """
    
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPT_V1
        self.system_prompt_version = SYSTEM_PROMPT_VERSION
    
    def build(self, profile: UserProfile) -> Tuple[str, str]:
        """
        Build the full prompt pair for a recommendation call.
        
        Args:
            profile: Validated UserProfile object (already sanitized upstream)
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        user_prompt = build_recommendation_prompt(profile)
        
        # Log prompt version for traceability
        logger.debug(
            "Built recommendation prompt",
            extra={
                "event": "prompt_built",
                "system_prompt_version": self.system_prompt_version,
                "profile_id": getattr(profile, "id", "unknown"),
            }
        )
        
        return self.system_prompt, user_prompt
    
    def build_single_section_prompt(
        self, 
        profile: UserProfile, 
        section: str
    ) -> Tuple[str, str]:
        """
        Build prompts for individual section regeneration (future enhancement).
        
        Args:
            profile: Validated UserProfile object
            section: Section name ('roadmap', 'skill_gap_analysis', etc.)
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        section_builders = {
            "roadmap": lambda p: build_roadmap_prompt(p),
            "skill_gap_analysis": lambda p: build_skill_gap_prompt(p),
            "career_guidance": lambda p: build_career_guidance_prompt(p),
        }
        
        if section not in section_builders:
            raise ValueError(f"Unknown section: {section}")
        
        user_prompt = section_builders[section](profile)
        
        # Use the same system prompt but with instruction to focus on one section
        system_prompt = (
            SYSTEM_PROMPT_V1 + 
            f" For this request, focus exclusively on the '{section}' section."
        )
        
        return system_prompt, user_prompt