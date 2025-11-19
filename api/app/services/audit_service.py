"""
Audit logging service.

Provides high-level API for logging user actions and system events.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from ..models.audit import AuditLog
from fastapi import Request
import json


class AuditService:
    """Service for managing audit logs."""

    # Actions that should be audited
    AUDITABLE_ACTIONS = {
        # Job actions
        "job.create": "Job created",
        "job.view": "Job viewed",
        "job.list": "Jobs listed",
        "job.delete": "Job deleted",

        # Batch actions
        "batch.create": "Batch created",
        "batch.view": "Batch viewed",
        "batch.list": "Batches listed",
        "batch.approve_item": "Batch item approved",
        "batch.reject_item": "Batch item rejected",
        "batch.regenerate_item": "Batch item regeneration requested",
        "batch.export": "Batch exported",

        # User actions
        "user.login": "User logged in",
        "user.logout": "User logged out",
        "user.create": "User created",
        "user.update": "User updated",
        "user.delete": "User deleted",

        # Backlink actions
        "backlink.create": "Backlink created",
        "backlink.bulk_import": "Backlinks bulk imported",
        "backlink.delete": "Backlink deleted",

        # Security actions
        "auth.failed": "Authentication failed",
        "auth.rate_limited": "Request rate limited",
        "auth.invalid_key": "Invalid API key used",

        # System actions
        "system.startup": "System started",
        "system.shutdown": "System shutdown",
        "system.error": "System error occurred"
    }

    def __init__(self, db: Session):
        """
        Initialize audit service.

        Args:
            db: Database session
        """
        self.db = db

    def log_action(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_id: Optional[str] = None,
        status: str = "success",
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            action: Action identifier (e.g., "job.create")
            resource_type: Type of resource (e.g., "job")
            user_id: ID of user performing action
            user_email: Email of user
            resource_id: ID of affected resource
            status: Action status (success/failure/error)
            status_code: HTTP status code
            error_message: Error message if failed
            request_data: Request payload (will be sanitized)
            response_data: Response data (will be sanitized)
            extra_data: Additional context
            method: HTTP method
            endpoint: API endpoint
            ip_address: Client IP address
            user_agent: User agent string
            duration_ms: Request duration

        Returns:
            Created AuditLog entry
        """
        # Sanitize sensitive data
        sanitized_request = self._sanitize_data(request_data)
        sanitized_response = self._sanitize_data(response_data)

        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            method=method,
            endpoint=endpoint,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            status_code=str(status_code) if status_code else None,
            error_message=error_message,
            request_data=sanitized_request,
            response_data=sanitized_response,
            extra_data=extra_data,
            duration_ms=str(duration_ms) if duration_ms else None
        )

        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)

        return audit_log

    def log_from_request(
        self,
        request: Request,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        status: str = "success",
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None
    ) -> AuditLog:
        """
        Log an audit event from a FastAPI Request object.

        Automatically extracts user info, IP, user agent, etc.

        Args:
            request: FastAPI Request object
            action: Action identifier
            resource_type: Resource type
            resource_id: Resource ID
            status: Action status
            status_code: HTTP status code
            error_message: Error message
            response_data: Response data
            metadata: Additional metadata
            duration_ms: Request duration

        Returns:
            Created AuditLog entry
        """
        # Extract user info from request state
        user_id = getattr(request.state, "user_id", None)
        user_email = getattr(request.state, "user_email", None)

        # Extract client info
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Extract request data (for POST/PUT)
        request_data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # Note: This might not work if body was already read
                # Consider storing in middleware
                request_data = getattr(request.state, "request_body", None)
            except:
                pass

        return self.log_action(
            action=action,
            resource_type=resource_type,
            user_id=user_id,
            user_email=user_email,
            resource_id=resource_id,
            status=status,
            status_code=status_code,
            error_message=error_message,
            request_data=request_data,
            response_data=response_data,
            extra_data=extra_data,
            method=request.method,
            endpoint=str(request.url.path),
            ip_address=ip_address,
            user_agent=user_agent,
            duration_ms=duration_ms
        )

    def get_user_activity(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        action_filter: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.

        Args:
            user_id: User ID
            limit: Max results
            offset: Offset for pagination
            action_filter: Filter by action (e.g., "job.create")
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of audit log entries
        """
        query = self.db.query(AuditLog).filter(AuditLog.user_id == user_id)

        if action_filter:
            query = query.filter(AuditLog.action == action_filter)

        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)

        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)

        return query.order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).offset(offset).all()

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit history for a specific resource.

        Args:
            resource_type: Type of resource
            resource_id: Resource ID
            limit: Max results

        Returns:
            List of audit log entries
        """
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()

    def get_security_events(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get recent security-related events.

        Args:
            hours: Look back N hours
            limit: Max results

        Returns:
            List of security event audit logs
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        security_actions = [
            "auth.failed",
            "auth.rate_limited",
            "auth.invalid_key"
        ]

        return self.db.query(AuditLog).filter(
            AuditLog.action.in_(security_actions),
            AuditLog.timestamp >= since
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()

    def get_failed_actions(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get recent failed actions.

        Args:
            hours: Look back N hours
            limit: Max results

        Returns:
            List of failed action audit logs
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        return self.db.query(AuditLog).filter(
            AuditLog.status.in_(["failure", "error"]),
            AuditLog.timestamp >= since
        ).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).all()

    def _sanitize_data(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Sanitize sensitive data from request/response.

        Removes passwords, API keys, tokens, etc.

        Args:
            data: Data to sanitize

        Returns:
            Sanitized data
        """
        if not data:
            return None

        # Fields to redact
        sensitive_fields = {
            "password", "api_key", "token", "secret",
            "anthropic_api_key", "openai_api_key", "google_api_key",
            "ahrefs_api_key", "authorization"
        }

        sanitized = {}
        for key, value in data.items():
            key_lower = key.lower()

            # Redact sensitive fields
            if any(field in key_lower for field in sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = self._sanitize_data(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Sanitize list of dicts
                sanitized[key] = [self._sanitize_data(item) for item in value]
            else:
                sanitized[key] = value

        return sanitized

    def _get_client_ip(self, request: Request) -> Optional[str]:
        """
        Get client IP address from request.

        Handles proxies and load balancers.

        Args:
            request: FastAPI Request

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (proxy)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Take first IP if multiple
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client
        if request.client:
            return request.client.host

        return None
