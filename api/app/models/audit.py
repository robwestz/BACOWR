"""
Audit logging models.

Tracks all user actions for security, compliance, and debugging.
"""

from sqlalchemy import Column, String, DateTime, JSON, Text, Index
from sqlalchemy.sql import func
from .database import Base, generate_uuid


class AuditLog(Base):
    """
    Audit log entry for tracking user actions.

    Captures: Who did what, when, from where, and what was the result.
    """
    __tablename__ = "audit_logs"

    # Primary identification
    id = Column(String, primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Actor (who)
    user_id = Column(String, nullable=True, index=True)  # Nullable for unauthenticated actions
    user_email = Column(String, nullable=True)
    api_key = Column(String, nullable=True)  # Truncated/hashed for security

    # Action (what)
    action = Column(String, nullable=False, index=True)  # e.g., "job.create", "batch.approve"
    resource_type = Column(String, nullable=False, index=True)  # e.g., "job", "batch", "user"
    resource_id = Column(String, nullable=True, index=True)  # ID of affected resource

    # Context (how/where)
    method = Column(String, nullable=True)  # HTTP method: GET, POST, PUT, DELETE
    endpoint = Column(String, nullable=True)  # API endpoint path
    ip_address = Column(String, nullable=True, index=True)
    user_agent = Column(String, nullable=True)

    # Result (outcome)
    status = Column(String, nullable=False, index=True)  # success, failure, error
    status_code = Column(String, nullable=True)  # HTTP status code
    error_message = Column(Text, nullable=True)

    # Additional data
    request_data = Column(JSON, nullable=True)  # Request payload (sanitized)
    response_data = Column(JSON, nullable=True)  # Response data (sanitized)
    extra_data = Column(JSON, nullable=True)  # Additional context (renamed from metadata to avoid SQLAlchemy conflict)

    # Performance
    duration_ms = Column(String, nullable=True)  # Request duration in milliseconds

    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_action_timestamp', 'action', 'timestamp'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_ip_timestamp', 'ip_address', 'timestamp'),
    )

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_email or 'anonymous'} at {self.timestamp}>"
