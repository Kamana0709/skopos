from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List

class Settings(BaseSettings):
    """Application settings - single source of truth."""
    
    # ... existing settings ...
    
    # Claude/LLM Settings (from Master PRD §26)
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.4
    STREAM_TIMEOUT_SECONDS: int = 60
        # Ensure this block is indented cleanly inside your Settings class:
    app_env: str = "local"
    app_version: str = "1.0.0"
    allowed_origins: any = ["http://localhost:5500", "http://localhost:8000"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: any) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return list(v) if v else []
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # This prevents crashing if extra keys exist
    )