"""
Skill Gap Analysis Prompt - Version V1 (Reserved for Future Enhancement)
Purpose: Generates only the Skill Gap Analysis section
Expected Inputs: UserProfile object
Output Contract: Produces only the ## Skill Gap Analysis section
Current Version: V1
"""

from .recommendation_prompt import _sanitize_profile_fields

def build_skill_gap_prompt(profile) -> str:
    """Build a prompt focused narrowly on generating only the Skill Gap Analysis section."""
    sanitized = _sanitize_profile_fields(profile)
    
    return f"""<profile>
Current Skills: {sanitized['current_skills_joined']}
Career Goals: {sanitized['career_goals']}
Experience Level: {sanitized['experience_level']}
</profile>

Based on the profile above, generate ONLY the "## Skill Gap Analysis" section.
Explicitly separate skills already possessed from skills still needed to achieve the stated career goals.
Be specific about what's missing and why it matters."""