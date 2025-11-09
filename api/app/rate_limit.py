"""
Rate limiting configuration and utilities.

Prevents API abuse and ensures fair usage across users.
Uses SlowAPI with Redis backend for distributed rate limiting.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
import os

# Rate limit configuration
RATE_LIMITS = {
    # Authentication endpoints
    "login": "5/minute",
    "register": "3/hour",
    "refresh": "10/minute",
    "password_change": "3/hour",

    # Job endpoints
    "create_job": "30/minute",
    "list_jobs": "100/minute",
    "get_job": "100/minute",

    # Analytics endpoints
    "analytics": "60/minute",
    "export": "10/minute",

    # Admin endpoints
    "admin": "100/minute",

    # Default
    "default": "100/minute"
}


def get_user_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Uses user ID if authenticated, otherwise falls back to IP address.
    This ensures authenticated users get their own rate limits.

    Args:
        request: FastAPI request object

    Returns:
        User identifier string
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"

    # Fall back to IP address for unauthenticated requests
    return f"ip:{get_remote_address(request)}"


# Initialize limiter
# In production with Redis: storage_uri="redis://localhost:6379"
# In development: uses in-memory storage
limiter = Limiter(
    key_func=get_user_identifier,
    default_limits=[RATE_LIMITS["default"]],
    storage_uri=os.getenv("REDIS_URL", "memory://"),
    strategy="fixed-window"
)


# Rate limit decorators for specific use cases
def rate_limit_auth(func):
    """Rate limit decorator for authentication endpoints."""
    return limiter.limit(RATE_LIMITS["login"])(func)


def rate_limit_create_job(func):
    """Rate limit decorator for job creation."""
    return limiter.limit(RATE_LIMITS["create_job"])(func)


def rate_limit_export(func):
    """Rate limit decorator for data export endpoints."""
    return limiter.limit(RATE_LIMITS["export"])(func)


def rate_limit_admin(func):
    """Rate limit decorator for admin endpoints."""
    return limiter.limit(RATE_LIMITS["admin"])(func)
