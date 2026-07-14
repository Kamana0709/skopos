"""
Learning Roadmap Prompt - Version V1 (Reserved for Future Enhancement)
Purpose: Generates only the Roadmap section content
Expected Inputs: UserProfile object
Output Contract: Produces only the ## Roadmap section with phased timeline
Current Version: V1
"""

from app.prompts.recommendation_prompt import _sanitize_profile_fields

def build_roadmap_prompt(profile) -> str:
    """
    Build a prompt focused narrowly on generating only the Roadmap section.
    NOT called in MVP flow - reserved for per-section regeneration.
    """
    sanitized = _sanitize_profile_fields(profile)
    
    return f"""<profile>
Education: {sanitized['education_level']} in {sanitized['field_of_study']}
Current Skills: {sanitized['current_skills_joined']}
Interests: {sanitized['interests_joined']}
Experience Level: {sanitized['experience_level']}
Learning Preferences: {sanitized['learning_preferences_joined']}
Available Time: {sanitized['available_hours_per_week']} hours/week
Career Goals: {sanitized['career_goals']}
</profile>

Based on the profile above, generate ONLY the "## Roadmap" section of a personalized career/learning recommendation.
Focus on a phased, time-boxed roadmap with specific phases, week-by-week breakdowns, and concrete milestones.
The total time commitment should be realistic given {sanitized['available_hours_per_week']} hours/week available."""