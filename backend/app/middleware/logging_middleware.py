"""Logging middleware with correlation ID."""

import time
import logging
from typing import Dict, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.utils.correlation import set_correlation_id, generate_correlation_id
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request/response logging with correlation IDs.
    
    Assigns a correlation ID to each request and logs structured events.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with logging."""
        # Generate and set correlation ID
        correlation_id = generate_correlation_id()
        set_correlation_id(correlation_id)
        
        # Log request received
        start_time = time.time()
        logger.info(
            "request_received",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "route": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            logger.error(
                "request_error",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise
        
        # Log request completed
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            "request_completed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "route": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
            }
        )
        
        return response