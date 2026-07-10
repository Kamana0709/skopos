"""Rate limiting middleware."""

import time
import logging
from typing import Dict, Tuple
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import Settings
from app.exceptions.base import AppException

logger = logging.getLogger(__name__)


class RateLimitExceeded(AppException):
    """Rate limit exceeded exception."""
    code = "RATE_LIMITED"
    
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__("Too many requests - please wait before trying again.")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Per-IP token-bucket rate limiter.
    
    Only applies to POST /api/v1/recommendations/stream endpoint.
    """
    
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.limit = settings.rate_limit_per_window
        self.window_seconds = settings.rate_limit_window_seconds
        
        # In-memory token bucket state
        self._buckets: Dict[str, Tuple[int, float]] = defaultdict(lambda: (settings.rate_limit_per_window, time.time()))
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Only rate limit the recommendation endpoint
        if request.url.path != "/api/v1/recommendations/stream" or request.method != "POST":
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self._allow_request(client_ip):
            retry_after = self.window_seconds
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "client_ip": client_ip,
                    "retry_after": retry_after,
                }
            )
            
            response = JSONResponse(
                status_code=429,
                content={
                    "code": "RATE_LIMITED",
                    "message": "You've made too many requests - please wait before trying again.",
                    "correlation_id": request.headers.get("x-correlation-id", "unknown"),
                },
                headers={"Retry-After": str(retry_after)},
            )
            return response
        
        return await call_next(request)
    
    def _allow_request(self, client_ip: str) -> bool:
        """Check if a request from this IP is allowed."""
        now = time.time()
        tokens, last_refill = self._buckets[client_ip]
        
        # Calculate tokens to refill based on time elapsed
        time_elapsed = now - last_refill
        refill_amount = (time_elapsed / self.window_seconds) * self.limit
        
        # Refill tokens
        tokens = min(self.limit, tokens + refill_amount)
        self._buckets[client_ip] = (tokens, now)
        
        # Check if we have tokens
        if tokens >= 1:
            # Use one token
            self._buckets[client_ip] = (tokens - 1, now)
            return True
        
        return False