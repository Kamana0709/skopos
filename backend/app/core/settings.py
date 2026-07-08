from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings - single source of truth."""
    
    # ... existing settings ...
    
    # Claude/LLM Settings (from Master PRD §26)
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.4
    STREAM_TIMEOUT_SECONDS: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"