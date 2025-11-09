"""
SQLAlchemy database models.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from ..database import Base


def generate_uuid():
    """Generate UUID for primary keys."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    api_key = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Optional for API key-only users
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    # Notification preferences
    notification_email = Column(String, nullable=True)  # Can be different from login email
    webhook_url = Column(String, nullable=True)
    enable_email_notifications = Column(Boolean, default=False)
    enable_webhook_notifications = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    backlinks = relationship("Backlink", back_populates="user", cascade="all, delete-orphan")


class Job(Base):
    """Job model for content generation jobs."""

    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Job inputs
    publisher_domain = Column(String, nullable=False, index=True)
    target_url = Column(Text, nullable=False)
    anchor_text = Column(String, nullable=False)

    # Job configuration
    llm_provider = Column(String, nullable=True)  # anthropic, openai, google, auto
    writing_strategy = Column(String, nullable=True)  # multi_stage, single_shot
    country = Column(String, default="se")
    use_ahrefs = Column(Boolean, default=True)
    enable_llm_profiling = Column(Boolean, default=True)

    # Job status
    status = Column(String, nullable=False, default="pending", index=True)
    # Statuses: pending, processing, delivered, blocked, aborted

    # Job outputs
    article_text = Column(Text, nullable=True)
    job_package = Column(JSON, nullable=True)  # Complete BacklinkJobPackage
    qc_report = Column(JSON, nullable=True)
    execution_log = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)

    # Cost tracking
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", back_populates="jobs")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_job_user_status', 'user_id', 'status'),
        Index('idx_job_user_created', 'user_id', 'created_at'),
        Index('idx_job_status_created', 'status', 'created_at'),
    )


class Backlink(Base):
    """Historical backlinks model."""

    __tablename__ = "backlinks"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Backlink data
    publisher_domain = Column(String, nullable=False, index=True)
    publisher_url = Column(Text, nullable=True)  # Full URL of article
    target_url = Column(Text, nullable=False)
    anchor_text = Column(String, nullable=False)

    # Metrics
    domain_authority = Column(Integer, nullable=True)
    page_authority = Column(Integer, nullable=True)
    traffic_estimate = Column(Integer, nullable=True)
    backlink_count = Column(Integer, nullable=True)

    # Metadata
    category = Column(String, nullable=True, index=True)
    language = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)  # Array of tags

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # Custom metrics (extensible JSON)
    custom_metrics = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="backlinks")

    # Indexes
    __table_args__ = (
        Index('idx_backlink_publisher_domain', 'publisher_domain'),
        Index('idx_backlink_category', 'category'),
        Index('idx_backlink_user_created', 'user_id', 'created_at'),
    )


class JobResult(Base):
    """
    Aggregated job results for analytics.

    This table stores processed analytics data separate from raw job data
    for performance optimization.
    """

    __tablename__ = "job_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, index=True, nullable=False)  # Not FK to allow job deletion
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Quality metrics
    qc_score = Column(Float, nullable=True)  # Overall QC score (0-100)
    qc_status = Column(String, nullable=True)  # PASS, WARNING, BLOCKED
    issue_count = Column(Integer, default=0)

    # Performance metrics
    generation_time_seconds = Column(Float, nullable=True)
    total_time_seconds = Column(Float, nullable=True)

    # Provider tracking
    provider_used = Column(String, nullable=True, index=True)
    model_used = Column(String, nullable=True)
    strategy_used = Column(String, nullable=True, index=True)

    # Cost tracking
    cost_actual = Column(Float, nullable=True)
    token_usage_input = Column(Integer, nullable=True)
    token_usage_output = Column(Integer, nullable=True)

    # Success tracking
    delivered = Column(Boolean, default=False, index=True)
    retry_needed = Column(Boolean, default=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User")

    # Indexes for analytics queries
    __table_args__ = (
        Index('idx_user_provider', 'user_id', 'provider_used'),
        Index('idx_user_strategy', 'user_id', 'strategy_used'),
        Index('idx_user_delivered', 'user_id', 'delivered'),
        Index('idx_created_delivered', 'created_at', 'delivered'),
    )
