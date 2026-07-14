"""
Recommendation Prompt - Version V1
Purpose: Builds the combined user prompt for the full recommendation
Expected Inputs: UserProfile object
Output Contract: Produces all 6 section headers as specified in system prompt
Current Version: V1
"""

from typing import Any
from app.models.user_profile import UserProfile

def build_recommendation_prompt(profile: UserProfile) -> str:
    """Build the combined recommendation user prompt from a UserProfile."""
    # Sanitize fields (defense-in-depth against delimiter injection)
    sanitized_fields = _sanitize_profile_fields(profile)
    
    return f"""<profile>
Education: {sanitized_fields.education_level} in {sanitized_fields.field_of_study}
Current Skills: {sanitized_fields.current_skills_joined}
Interests: {sanitized_fields.interests_joined}
Experience Level: {sanitized_fields.experience_level}
Learning Preferences: {sanitized_fields.learning_preferences_joined}
Available Time: {sanitized_fields.available_hours_per_week} hours/week
Career Goals: {sanitized_fields.career_goals}
</profile>

Generate a personalized recommendation following the required section structure."""

def _sanitize_profile_fields(profile: UserProfile) -> dict[str, Any]:
    """Sanitize fields to prevent prompt injection via delimiter tags."""
    # Strip any occurrence of delimiter tags from user-supplied values
    def sanitize_string(value: str) -> str:
        if not value:
            return value
        return (
            value
            .replace("<profile>", "")
            .replace("</profile>", "")
            .replace("<profile", "")
            .replace("/profile>", "")
        )
    
    # Handle list fields
    def sanitize_list(items: list[str]) -> str:
        if not items:
            return "None"
        return ", ".join(sanitize_string(item) for item in items)
    
    return {
        "education_level": sanitize_string(profile.education_level or "Not specified"),
        "field_of_study": sanitize_string(profile.field_of_study or "Not specified"),
        "current_skills_joined": sanitize_list(profile.current_skills or []),
        "interests_joined": sanitize_list(profile.interests or []),
        "experience_level": sanitize_string(profile.experience_level or "Not specified"),
        "learning_preferences_joined": sanitize_list(profile.learning_preferences or []),
        "available_hours_per_week": profile.available_hours_per_week or 5,
        "career_goals": sanitize_string(profile.career_goals or "Not specified"),
    }

"""Recommendation prompt template."""

RECOMMENDATION_PROMPT_TEMPLATE = """Based on the user's profile, provide a personalized career recommendation.

{profile_data}

Please provide a comprehensive recommendation following the structure in the system prompt.

Important:
- Be specific and actionable
- Provide concrete resources (courses, books, projects)
- Consider the user's available hours per week
- Match recommendations to their experience level
- Suggest realistic timelines"""

