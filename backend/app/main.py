from fastapi import FastAPI, Depends
from anthropic import AsyncAnthropic
from core.settings import Settings
from core.clients.claude_client import ClaudeClient
from app.services.prompt_builder import PromptBuilder
from services.recommendation_service import RecommendationService
from core.sse.sse_formatter import SSEFormatter
from app.models.user_profile import UserProfile



import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.api.v1.router import api_router
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware
from app.exceptions.handlers import register_exception_handlers
from app.utils.logger import setup_logging, get_logger

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


"""FastAPI application composition root."""


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    settings = get_settings()
    setup_logging(settings)
    logger.info("app_startup", extra={"app_env": settings.app_env, "claude_model": settings.claude_model})
    yield
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="Skopos API",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.app_env == "local" else None,
        redoc_url="/redoc" if settings.app_env == "local" else None,
    )
    
    # Register exception handlers FIRST (they wrap everything)
    register_exception_handlers(app)
    
    # CORS middleware (starlette built-in)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware, settings=settings)
    
    # Logging middleware (add last for request path, but will be first in effective order)
    app.add_middleware(LoggingMiddleware)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Mount static frontend
    try:
        app.mount("/", StaticFiles(directory="static", html=True), name="static")
        logger.info("static_mounted", extra={"directory": "static"})
    except Exception as e:
        logger.warning("static_mount_failed", extra={"error": str(e)})
    
    return app


app = create_app()