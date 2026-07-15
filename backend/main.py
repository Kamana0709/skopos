"""FastAPI application composition root."""

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

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, settings=settings)
    app.add_middleware(LoggingMiddleware)

    app.include_router(api_router, prefix="/api/v1")

    try:
        app.mount("/", StaticFiles(directory="static", html=True), name="static")
        logger.info("static_mounted", extra={"directory": "static"})
    except Exception as e:
        logger.warning("static_mount_failed", extra={"error": str(e)})

    return app


app = create_app()