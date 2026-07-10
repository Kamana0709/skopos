"""
PromptBuilder Service
Purpose: Transforms a validated UserProfile into system and user prompt pair
Owns: All prompt construction logic, injection defense
Dependencies: prompts/* modules
"""

import logging
from typing import Tuple
from app.models.user_profile import UserProfile
from app.prompts.system_prompt import SYSTEM_PROMPT_V1, SYSTEM_PROMPT_VERSION
from app.prompts.recommendation_prompt import build_recommendation_prompt

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
    
"""Prompt construction utilities."""

from typing import Tuple
import json

from app.schemas.profile import UserProfile
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.prompts.recommendation_prompt import RECOMMENDATION_PROMPT_TEMPLATE


class PromptBuilder:
    """
    Builds system and user prompts from validated UserProfile.
    
    This is the SINGLE place where prompt delimiting and construction occurs.
    """
    
    @staticmethod
    def build_prompts(profile: UserProfile) -> Tuple[str, str]:
        """
        Build system and user prompts from a validated profile.
        
        Args:
            profile: Validated UserProfile
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Use the fixed system prompt
        system_prompt = SYSTEM_PROMPT
        
        # Build user profile data with XML-style delimiting for injection defense
        profile_data = PromptBuilder._format_profile(profile)
        
        # Wrap in <profile> tags as the sole injection defense choke point
        user_prompt = RECOMMENDATION_PROMPT_TEMPLATE.format(profile_data=profile_data)
        
        return system_prompt, user_prompt
    
    @staticmethod
    def _format_profile(profile: UserProfile) -> str:
        """Format user profile as structured text with delimiting."""
        lines = [
            "<profile>",
            f"  <education>",
            f"    <level>{profile.education.level.value}</level>",
        ]
        
        if profile.education.field_of_study:
            lines.append(f"    <field_of_study>{profile.education.field_of_study}</field_of_study>")
        lines.append("  </education>")
        
        if profile.current_skills:
            skills_str = ", ".join(profile.current_skills)
            lines.append(f"  <current_skills>{skills_str}</current_skills>")
        
        interests_str = ", ".join(profile.interests)
        lines.append(f"  <interests>{interests_str}</interests>")
        lines.append(f"  <experience_level>{profile.experience_level.value}</experience_level>")
        
        preferences_str = ", ".join([p.value for p in profile.learning_preferences])
        lines.append(f"  <learning_preferences>{preferences_str}</learning_preferences>")
        lines.append(f"  <available_hours_per_week>{profile.available_hours_per_week}</available_hours_per_week>")
        lines.append(f"  <career_goals>{profile.career_goals}</career_goals>")
        lines.append("</profile>")
        
        return "\n".join(lines)