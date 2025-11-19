"""
Quota enforcement middleware for Wave 5.

Automatically checks and enforces usage quotas for authenticated users.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.database import User


class QuotaMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce usage quotas.

    Checks user quotas before allowing job creation or other quota-consuming operations.
    """

    def __init__(self, app):
        super().__init__(app)
        self.quota_protected_endpoints = [
            "/api/v1/jobs",  # Job creation
            "/api/v1/batches",  # Batch creation
        ]

    async def dispatch(self, request: Request, call_next):
        """Check quotas for protected endpoints."""

        # Only check POST requests to protected endpoints
        if request.method == "POST" and any(
            request.url.path.startswith(endpoint)
            for endpoint in self.quota_protected_endpoints
        ):
            # Try to get user from request state (set by auth middleware)
            user = getattr(request.state, "user", None)

            if user:
                # Check quota
                if not self._check_quota(user):
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail={
                            "error": "Quota exceeded",
                            "message": "You have exceeded your usage quota",
                            "jobs_used": user.jobs_created_count,
                            "jobs_quota": user.jobs_quota,
                            "tokens_used": user.tokens_used,
                            "tokens_quota": user.tokens_quota
                        }
                    )

        # Continue with request
        response = await call_next(request)
        return response

    def _check_quota(self, user: User) -> bool:
        """Check if user has remaining quota."""
        if user.jobs_created_count >= user.jobs_quota:
            return False
        if user.tokens_used >= user.tokens_quota:
            return False
        return True


def check_user_quota(user: User):
    """
    Dependency to check user quota.

    Usage:
        @router.post("/expensive-operation", dependencies=[Depends(check_user_quota)])
        async def expensive_op(user: User = Depends(get_current_user)):
            ...
    """
    if user.jobs_created_count >= user.jobs_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Job quota exceeded ({user.jobs_created_count}/{user.jobs_quota})"
        )

    if user.tokens_used >= user.tokens_quota:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Token quota exceeded ({user.tokens_used}/{user.tokens_quota})"
        )

    return True
