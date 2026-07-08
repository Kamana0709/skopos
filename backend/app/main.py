from fastapi import FastAPI, Depends
from anthropic import AsyncAnthropic
from core.settings import Settings
from core.clients.claude_client import ClaudeClient
from services.prompt_builder import PromptBuilder
from services.recommendation_service import RecommendationService
from core.sse.sse_formatter import SSEFormatter

app = FastAPI()

# Singleton dependencies
def get_settings():
    return Settings()

def get_anthropic_client(settings: Settings = Depends(get_settings)):
    return AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

def get_claude_client(
    anthropic_client: AsyncAnthropic = Depends(get_anthropic_client),
    settings: Settings = Depends(get_settings),
):
    return ClaudeClient(
        client=anthropic_client,
        settings=settings,
    )

def get_prompt_builder():
    return PromptBuilder()

def get_sse_formatter():
    return SSEFormatter()

def get_recommendation_service(
    claude_client: ClaudeClient = Depends(get_claude_client),
    sse_formatter: SSEFormatter = Depends(get_sse_formatter),
    prompt_builder: PromptBuilder = Depends(get_prompt_builder),
):
    return RecommendationService(
        claude_client=claude_client,
        sse_formatter=sse_formatter,
        prompt_builder=prompt_builder,
    )

# Route handlers
@app.post("/api/v1/recommendations/stream")
async def stream_recommendation(
    profile: UserProfile,
    recommendation_service: RecommendationService = Depends(get_recommendation_service),
):
    """Stream a personalized recommendation as SSE."""
    from fastapi.responses import StreamingResponse
    
    async def event_generator():
        correlation_id = str(uuid.uuid4())
        async for event in recommendation_service.generate_recommendation(
            profile=profile,
            correlation_id=correlation_id,
        ):
            yield event
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )