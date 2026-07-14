"""Configuration management - single source for all environment variables."""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Anthropic Configuration
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    claude_model: str = Field(default="claude-sonnet-4-6", description="Claude model name")
    claude_max_tokens: int = Field(default=4096, description="Max tokens for Claude response")
    claude_temperature: float = Field(default=0.4, description="Temperature for Claude generation")
    
    # Server Configuration
    app_env: str = Field(default="local", description="Application environment")
    app_version: str = Field(default="1.0.0", description="Application version")
    port: int = Field(default=8000, description="Server port")
    allowed_origins: List[str] = Field(default=["http://localhost:5500", "http://localhost:8000"], description="CORS allowed origins")
    
    # Rate Limiting
    rate_limit_per_window: int = Field(default=10, description="Requests allowed per window")
    rate_limit_window_seconds: int = Field(default=900, description="Rate limiting window in seconds")
    
    # Timeouts
    stream_timeout_seconds: int = Field(default=60, description="Total stream timeout in seconds")
    connection_timeout_seconds: int = Field(default=10, description="Connection timeout in seconds")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"
    
    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse comma-separated origins from environment."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    @field_validator("claude_temperature")
    @classmethod
    def validate_temperature(cls, v):
        """Ensure temperature is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("claude_temperature must be between 0 and 1")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()