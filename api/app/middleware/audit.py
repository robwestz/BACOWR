"""
Audit logging middleware.

Automatically logs all API requests for audit trail.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from sqlalchemy.orm import Session
from typing import Callable
import time
import json

from ..database import SessionLocal
from ..services.audit_service import AuditService


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log API requests to audit log.

    Captures: method, endpoint, user, duration, status, errors.
    """

    # Endpoints to exclude from audit logging (to avoid noise)
    EXCLUDED_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico"
    }

    # Map HTTP methods + paths to audit actions
    ACTION_MAPPING = {
        ("POST", "/api/v1/jobs"): ("job.create", "job"),
        ("GET", "/api/v1/jobs"): ("job.list", "job"),
        ("POST", "/api/v1/batches"): ("batch.create", "batch"),
        ("GET", "/api/v1/batches"): ("batch.list", "batch"),
        ("POST", "/api/v1/backlinks"): ("backlink.create", "backlink"),
        ("POST", "/api/v1/backlinks/bulk"): ("backlink.bulk_import", "backlink"),
    }

    def __init__(self, app: ASGIApp):
        """Initialize middleware."""
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log to audit trail.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response
        """
        # Skip excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Skip static files
        if request.url.path.startswith("/static"):
            return await call_next(request)

        # Start timer
        start_time = time.time()

        # Store original body for logging (if needed)
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                # Reset stream so route can read it
                async def receive():
                    return {"type": "http.request", "body": body}

                request._receive = receive

                # Try to parse as JSON
                try:
                    request.state.request_body = json.loads(body.decode("utf-8"))
                except:
                    request.state.request_body = {"_raw": body.decode("utf-8", errors="ignore")[:1000]}
            except:
                pass

        # Process request
        response = None
        error_message = None
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error_message = str(e)
            # Re-raise to let global error handler deal with it
            raise
        finally:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Determine audit action
            action, resource_type = self._determine_action(request)

            # Only log if we have an action
            if action:
                # Extract resource ID from path if present
                resource_id = self._extract_resource_id(request.url.path)

                # Determine status
                if error_message:
                    status = "error"
                elif status_code >= 400:
                    status = "failure"
                else:
                    status = "success"

                # Log to audit trail
                try:
                    db = SessionLocal()
                    try:
                        audit_service = AuditService(db)
                        audit_service.log_from_request(
                            request=request,
                            action=action,
                            resource_type=resource_type,
                            resource_id=resource_id,
                            status=status,
                            status_code=status_code,
                            error_message=error_message,
                            duration_ms=duration_ms
                        )
                    finally:
                        db.close()
                except Exception as audit_error:
                    # Don't fail request if audit logging fails
                    print(f"Audit logging error: {audit_error}")

        return response

    def _determine_action(self, request: Request) -> tuple[str, str]:
        """
        Determine audit action from request.

        Args:
            request: Request object

        Returns:
            Tuple of (action, resource_type)
        """
        method = request.method
        path = request.url.path

        # Check exact match first
        key = (method, path)
        if key in self.ACTION_MAPPING:
            return self.ACTION_MAPPING[key]

        # Check pattern matches
        if path.startswith("/api/v1/jobs/"):
            if method == "GET":
                return ("job.view", "job")
            elif method == "DELETE":
                return ("job.delete", "job")
        elif path.startswith("/api/v1/batches/"):
            if "/items/" in path and "/review" in path:
                return ("batch.review_item", "batch")
            elif "/items/" in path and "/regenerate" in path:
                return ("batch.regenerate_item", "batch")
            elif "/export" in path:
                return ("batch.export", "batch")
            elif method == "GET":
                return ("batch.view", "batch")
        elif path.startswith("/api/v1/backlinks/"):
            if method == "DELETE":
                return ("backlink.delete", "backlink")
            elif method == "GET":
                return ("backlink.view", "backlink")

        # Default: generic action
        return (f"api.{method.lower()}", "api")

    def _extract_resource_id(self, path: str) -> str | None:
        """
        Extract resource ID from URL path.

        Args:
            path: URL path

        Returns:
            Resource ID if found
        """
        # Pattern: /api/v1/{resource}/{id}
        parts = path.split("/")

        # Look for UUID-like patterns
        for part in reversed(parts):
            if part and len(part) >= 32 and "-" in part:
                return part

        return None


def setup_audit_middleware(app):
    """
    Configure audit middleware for FastAPI app.

    Args:
        app: FastAPI application instance

    Returns:
        Configured app
    """
    app.add_middleware(AuditMiddleware)
    return app
