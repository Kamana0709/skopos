import asyncio
import os
from anthropic import AsyncAnthropic
from app.core.settings import Settings
from app.core.clients.claude_client import ClaudeClient
from app.services.prompt_builder import PromptBuilder
from app.models.user_profile import UserProfile

async def test_real_claude():
    # Load settings
    settings = Settings()
    
    # Create real Anthropic client
    anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    
    # Create Claude client
    claude_client = ClaudeClient(
        client=anthropic_client,
        settings=settings,
        correlation_id="test-123"
    )
    
    # Create a test profile
    profile = UserProfile(
        education_level="Bachelor's",
        field_of_study="Computer Science",
        current_skills=["Python", "JavaScript", "SQL"],
        interests=["Machine Learning", "Web Development"],
        experience_level="mid",
        learning_preferences=["video", "hands-on-projects"],
        available_hours_per_week=10,
        career_goals="Become a Machine Learning Engineer in 2 years"
    )
    
    # Build prompts
    builder = PromptBuilder()
    system_prompt, user_prompt = builder.build(profile)
    
    # Test the stream
    print("Starting Claude stream...")
    async for event in claude_client.stream(system_prompt, user_prompt):
        if event.type == "section":
            print(f"\n--- SECTION: {event.section} ---\n")
        elif event.type == "chunk":
            print(event.text, end="", flush=True)
        elif event.type == "done":
            print("\n\n--- STREAM COMPLETE ---")
    
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_real_claude())