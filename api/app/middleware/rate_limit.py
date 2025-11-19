"""
Rate limiting middleware for BACOWR API.

Prevents abuse by limiting the number of requests per user/IP.
Uses SlowAPI for Redis-backed rate limiting.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from typing import Callable
import os


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key from request.

    Prioritizes API key over IP address for authenticated requests.

    Args:
        request: FastAPI request object

    Returns:
        Rate limit key (API key or IP address)
    """
    # Check for API key in headers
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{api_key}"

    # Fall back to IP address
    return f"ip:{get_remote_address(request)}"


# Initialize limiter
# Storage backend: Redis if available, in-memory fallback
redis_url = os.getenv("REDIS_URL")
if redis_url:
    storage_uri = redis_url
else:
    storage_uri = "memory://"

limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=storage_uri,
    default_limits=["1000/day", "100/hour"],
    headers_enabled=True,  # Add rate limit info to response headers
    strategy="fixed-window"  # or "moving-window" for smoother limits
)


# Rate limit decorators for different endpoints

def rate_limit_strict(func: Callable) -> Callable:
    """
    Strict rate limit for expensive operations.

    Limits: 10 requests/minute, 100/hour
    Use for: Job creation, batch processing
    """
    return limiter.limit("10/minute;100/hour")(func)


def rate_limit_moderate(func: Callable) -> Callable:
    """
    Moderate rate limit for normal operations.

    Limits: 60 requests/minute, 1000/hour
    Use for: List endpoints, analytics
    """
    return limiter.limit("60/minute;1000/hour")(func)


def rate_limit_relaxed(func: Callable) -> Callable:
    """
    Relaxed rate limit for lightweight operations.

    Limits: 120 requests/minute, 2000/hour
    Use for: Health checks, status endpoints
    """
    return limiter.limit("120/minute;2000/hour")(func)


# Exception handler for rate limit exceeded
async def rate_limit_error_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom error handler for rate limit exceeded.

    Returns JSON response with retry information.
    """
    return {
        "error": "Rate limit exceeded",
        "detail": str(exc.detail),
        "retry_after": exc.headers.get("Retry-After", "unknown"),
        "limit": exc.headers.get("X-RateLimit-Limit", "unknown"),
        "remaining": exc.headers.get("X-RateLimit-Remaining", "0"),
        "reset": exc.headers.get("X-RateLimit-Reset", "unknown")
    }


def setup_rate_limiting(app):
    """
    Configure rate limiting for FastAPI app.

    Args:
        app: FastAPI application instance
    """
    # Add rate limiter to app state
    app.state.limiter = limiter

    # Add exception handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add middleware (optional - for automatic header injection)
    # app.add_middleware(SlowAPIMiddleware)

    return app


# Environment-specific rate limits
def get_rate_limit_for_env() -> str:
    """
    Get rate limit based on environment.

    Development: More lenient
    Production: Stricter

    Returns:
        Rate limit string
    """
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return "50/minute;500/hour;5000/day"
    else:
        # Development/staging - more lenient
        return "200/minute;2000/hour;20000/day"
