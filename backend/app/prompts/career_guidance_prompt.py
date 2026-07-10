"""
Career Guidance Prompt - Version V1 (Reserved for Future Enhancement)
Purpose: Generates only the Career Guidance section
Expected Inputs: UserProfile object
Output Contract: Produces only the ## Career Guidance section
Current Version: V1
"""

from app.prompts.recommendation_prompt import _sanitize_profile_fields

def build_career_guidance_prompt(profile) -> str:
    """Build a prompt focused narrowly on generating only the Career Guidance section."""
    sanitized = _sanitize_profile_fields(profile)
    
    return f"""<profile>
Education: {sanitized['education_level']} in {sanitized['field_of_study']}
Current Skills: {sanitized['current_skills_joined']}
Career Goals: {sanitized['career_goals']}
Experience Level: {sanitized['experience_level']}
</profile>

Based on the profile above, generate ONLY the "## Career Guidance" section.
Provide realistic, encouraging next-step guidance and an approximate overall timeline.
Tailor the framing to match the {sanitized['experience_level']} experience level."""