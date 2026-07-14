"""Prompt construction utilities."""

from typing import Tuple

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
            profile: Validated UserProfile schema
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = SYSTEM_PROMPT
        
        # Format profile data directly from schema
        profile_data = PromptBuilder._format_profile(profile)
        user_prompt = RECOMMENDATION_PROMPT_TEMPLATE.format(profile_data=profile_data)
        
        return system_prompt, user_prompt
    
    @staticmethod
    def _format_profile(profile: UserProfile) -> str:
        """Format user profile as structured text with XML delimiting."""
        lines = [
            "<profile>",
            "  <education>",
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
    
# backend/app/models/user_profile.py
from typing import Optional, List
from pydantic import BaseModel
from enum import Enum

# Define Education model if it's a separate class
class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    current: bool = False

# Define Experience model if needed
class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    current: bool = False
    description: Optional[str] = None

# Define Skill model if needed
class Skill(BaseModel):
    name: str
    level: Optional[str] = None  # e.g., "beginner", "intermediate", "expert"

# Define Interest model if needed
class Interest(BaseModel):
    name: str
    category: Optional[str] = None

# Main UserProfile model
class UserProfile(BaseModel):
    """User profile model for storing user preferences and information"""
    
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    
    # Lists of objects
    interests: List[Interest] = []
    skills: List[Skill] = []
    experience: List[Experience] = []  # Changed from Optional[int] to List[Experience]
    education: List[Education] = []    # Add this field
    
    # Other fields
    goals: List[str] = []
    preferred_languages: List[str] = []
    
    # Career related
    current_role: Optional[str] = None
    years_of_experience: Optional[int] = None
    desired_roles: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "age": 25,
                "interests": [{"name": "technology"}, {"name": "sports"}],
                "skills": [{"name": "Python", "level": "expert"}, {"name": "React", "level": "intermediate"}],
                "education": [{"degree": "B.S. Computer Science", "institution": "MIT", "current": False}],
                "goals": ["Become a full-stack developer"],
                "years_of_experience": 3
            }
        }