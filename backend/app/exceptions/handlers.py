"""Global exception handlers."""

import logging
from typing import Any, Dict

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.exceptions.base import AppException
from app.exceptions.claude_exceptions import (
    ClaudeAPIError,
    ClaudeAuthError,
    ClaudeOverloadedError,
    ClaudeTimeoutError,
    ClaudeStreamTimeoutError,
)
from app.middleware.rate_limit_middleware import RateLimitExceeded
from app.schemas.responses import ErrorResponse, ErrorDetail
from app.utils.correlation import get_correlation_id

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """Register all exception handlers."""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        correlation_id = get_correlation_id()
        
        details = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            details.append(ErrorDetail(field=field, error=error["msg"]))
        
        logger.warning(
            "validation_error",
            extra={
                "correlation_id": correlation_id,
                "error_count": len(details),
            }
        )
        
        response = ErrorResponse(
            code="VALIDATION_ERROR",
            message="One or more fields are invalid.",
            correlation_id=correlation_id,
            details=details,
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=response.model_dump(exclude_none=True),
        )
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded):
        """Handle rate limit exceeded errors."""
        correlation_id = get_correlation_id()
        
        response = ErrorResponse(
            code=exc.code,
            message=exc.user_message,
            correlation_id=correlation_id,
        )
        
        headers = {"Retry-After": str(exc.retry_after)}
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=response.model_dump(),
            headers=headers,
        )
    
    @app.exception_handler(ClaudeAuthError)
    async def claude_auth_error_handler(request: Request, exc: ClaudeAuthError):
        """Handle Claude authentication errors."""
        correlation_id = get_correlation_id()
        
        logger.critical(
            "claude_auth_error",
            extra={
                "correlation_id": correlation_id,
                "error": str(exc),
            }
        )
        
        response = ErrorResponse(
            code=exc.code,
            message=exc.user_message,
            correlation_id=correlation_id,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(),
        )
    
    @app.exception_handler((ClaudeOverloadedError, ClaudeTimeoutError, ClaudeStreamTimeoutError))
    async def claude_service_error_handler(request: Request, exc: ClaudeAPIError):
        """Handle Claude service errors."""
        correlation_id = get_correlation_id()
        
        logger.error(
            "claude_service_error",
            extra={
                "correlation_id": correlation_id,
                "error_code": exc.code,
                "error": str(exc),
            }
        )
        
        response = ErrorResponse(
            code=exc.code,
            message=exc.user_message,
            correlation_id=correlation_id,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(),
        )
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """Handle general application exceptions."""
        correlation_id = get_correlation_id()
        
        logger.error(
            "app_exception",
            extra={
                "correlation_id": correlation_id,
                "exception_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        
        response = ErrorResponse(
            code=exc.code,
            message=exc.user_message,
            correlation_id=correlation_id,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Handle unhandled exceptions."""
        correlation_id = get_correlation_id()
        
        logger.exception(
            "unhandled_exception",
            extra={
                "correlation_id": correlation_id,
                "exception_type": type(exc).__name__,
                "error": str(exc),
            }
        )
        
        response = ErrorResponse(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
            correlation_id=correlation_id,
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response.model_dump(),
        )