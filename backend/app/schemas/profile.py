"""UserProfile request schema with validation."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum

from app.utils.sanitize import sanitize_text


class EducationLevel(str, Enum):
    """Education level enum."""
    HIGH_SCHOOL = "high-school"
    DIPLOMA = "diploma"
    BACHELORS = "bachelors"
    MASTERS = "masters"
    PHD = "phd"
    SELF_TAUGHT = "self-taught"


class ExperienceLevel(str, Enum):
    """Experience level enum."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningPreference(str, Enum):
    """Learning preference enum."""
    VIDEO = "video"
    TEXT = "text"
    INTERACTIVE = "interactive"
    HANDS_ON_PROJECTS = "hands-on-projects"
    MENTORSHIP = "mentorship"


class Education(BaseModel):
    """Education information."""
    level: EducationLevel = Field(..., description="Education level")
    field_of_study: Optional[str] = Field(None, description="Field of study", max_length=100)
    
    model_config = ConfigDict(extra="forbid")
    
    @field_validator("field_of_study")
    @classmethod
    def sanitize_field_of_study(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize field of study text."""
        if v is not None:
            v = sanitize_text(v)
            if len(v) > 0 and len(v) < 1:
                return None
        return v


class UserProfile(BaseModel):
    """User profile for AI recommendation."""
    education: Education = Field(..., description="Education information")
    current_skills: List[str] = Field(default_factory=list, description="Current skills", max_length=30)
    interests: List[str] = Field(..., description="Interests", min_length=1, max_length=15)
    experience_level: ExperienceLevel = Field(..., description="Experience level")
    learning_preferences: List[LearningPreference] = Field(..., description="Learning preferences")
    available_hours_per_week: int = Field(..., description="Available hours per week", ge=1, le=80)
    career_goals: str = Field(..., description="Career goals", min_length=10, max_length=500)
    
    model_config = ConfigDict(extra="forbid")
    
    @field_validator("current_skills")
    @classmethod
    def validate_skills(cls, v: List[str]) -> List[str]:
        """Validate and sanitize skills."""
        sanitized = []
        for skill in v:
            skill = skill.strip()
            skill = sanitize_text(skill)
            if skill and 1 <= len(skill) <= 50:
                sanitized.append(skill)
        return sanitized
    
    @field_validator("interests")
    @classmethod
    def validate_interests(cls, v: List[str]) -> List[str]:
        """Validate and sanitize interests."""
        sanitized = []
        for interest in v:
            interest = interest.strip()
            interest = sanitize_text(interest)
            if interest and 1 <= len(interest) <= 50:
                sanitized.append(interest)
        if not sanitized:
            raise ValueError("interests must contain at least 1 valid item")
        return sanitized
    
    @field_validator("career_goals")
    @classmethod
    def validate_career_goals(cls, v: str) -> str:
        """Validate and sanitize career goals."""
        v = v.strip()
        v = sanitize_text(v)
        if not v:
            raise ValueError("career_goals cannot be empty")
        if len(v) < 10:
            raise ValueError("career_goals must be at least 10 characters")
        return v
    
    @field_validator("learning_preferences")
    @classmethod
    def validate_learning_preferences(cls, v: List[LearningPreference]) -> List[LearningPreference]:
        """Ensure learning preferences is not empty."""
        if not v:
            raise ValueError("learning_preferences must contain at least 1 item")
        return v