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
    campaigns = relationship("Campaign", cascade="all, delete-orphan")
    job_templates = relationship("JobTemplate", cascade="all, delete-orphan")
    scheduled_jobs = relationship("ScheduledJob", cascade="all, delete-orphan")


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


class Campaign(Base):
    """
    Campaign model for organizing jobs into logical groups.

    Campaigns allow users to group related jobs together for:
    - Publisher-specific campaigns (all backlinks to one publisher)
    - Topic-specific campaigns (all backlinks about one topic)
    - Time-based campaigns (Q1 2025 backlinks)
    - Client campaigns (all work for one client)
    """

    __tablename__ = "campaigns"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Campaign info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Campaign metadata
    status = Column(String, default="active")  # active, paused, completed, archived
    color = Column(String, nullable=True)  # Hex color for UI
    tags = Column(JSON, nullable=True)  # Array of tags

    # Campaign goals (optional tracking)
    target_job_count = Column(Integer, nullable=True)
    target_budget_usd = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    scheduled_jobs = relationship("ScheduledJob", back_populates="campaign")
    job_templates = relationship("JobTemplate", back_populates="campaign")

    __table_args__ = (
        Index('idx_campaign_user_status', 'user_id', 'status'),
        Index('idx_campaign_user_created', 'user_id', 'created_at'),
    )


class JobTemplate(Base):
    """
    Job template model for reusable job configurations.

    Templates allow users to save job configurations for reuse:
    - Publisher-specific settings
    - Common configurations (e.g., "High quality backlink")
    - Client-specific templates
    """

    __tablename__ = "job_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True, index=True)

    # Template info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Template configuration (same as Job inputs)
    publisher_domain = Column(String, nullable=True)  # Can be empty for generic templates
    llm_provider = Column(String, nullable=True)
    writing_strategy = Column(String, nullable=True)
    country = Column(String, nullable=True)
    use_ahrefs = Column(Boolean, default=True)
    enable_llm_profiling = Column(Boolean, default=True)

    # Template metadata
    use_count = Column(Integer, default=0)  # Track how many times it's been used
    is_favorite = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User")
    campaign = relationship("Campaign", back_populates="job_templates")
    scheduled_jobs = relationship("ScheduledJob", back_populates="template")

    __table_args__ = (
        Index('idx_template_user_favorite', 'user_id', 'is_favorite'),
        Index('idx_template_campaign', 'campaign_id'),
    )


class ScheduledJob(Base):
    """
    Scheduled job model for jobs that should run in the future.

    Supports:
    - One-time scheduled jobs (run once at specific time)
    - Recurring jobs (daily, weekly, monthly)
    - Cron-like scheduling
    """

    __tablename__ = "scheduled_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    campaign_id = Column(String, ForeignKey("campaigns.id"), nullable=True, index=True)
    template_id = Column(String, ForeignKey("job_templates.id"), nullable=True, index=True)

    # Schedule info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    # Scheduling configuration
    schedule_type = Column(String, nullable=False)  # once, daily, weekly, monthly, cron
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)  # Next run time

    # Recurring configuration
    recurrence_pattern = Column(String, nullable=True)  # e.g., "daily", "weekly:monday", "monthly:1"
    recurrence_end_date = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String, default="UTC")

    # Job configuration (can override template)
    job_config = Column(JSON, nullable=False)  # JobCreate-compatible config

    # Status
    status = Column(String, default="active")  # active, paused, completed, expired, error
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True, index=True)
    run_count = Column(Integer, default=0)
    max_runs = Column(Integer, nullable=True)  # Optional limit on recurring jobs

    # Related jobs
    last_job_id = Column(String, nullable=True)  # ID of last created job
    last_job_status = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Error tracking
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)

    # Relationships
    user = relationship("User")
    campaign = relationship("Campaign", back_populates="scheduled_jobs")
    template = relationship("JobTemplate", back_populates="scheduled_jobs")

    __table_args__ = (
        Index('idx_scheduled_user_status', 'user_id', 'status'),
        Index('idx_scheduled_next_run', 'next_run_at', 'status'),
        Index('idx_scheduled_campaign', 'campaign_id'),
    )


class PublisherMetrics(Base):
    """
    Publisher performance metrics model.

    Tracks aggregated performance data for each publisher domain to provide:
    - Historical success/failure rates
    - Average quality scores
    - Cost analytics
    - Performance trends over time
    - Publisher recommendations
    """

    __tablename__ = "publisher_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    publisher_domain = Column(String, nullable=False, index=True)

    # Job statistics
    total_jobs = Column(Integer, default=0)
    successful_jobs = Column(Integer, default=0)  # status = delivered
    failed_jobs = Column(Integer, default=0)  # status = blocked/aborted
    pending_jobs = Column(Integer, default=0)  # status = pending/processing

    # Success rate (0-100)
    success_rate = Column(Float, default=0.0)

    # Quality metrics
    avg_qc_score = Column(Float, nullable=True)  # Average QC score
    avg_issue_count = Column(Float, nullable=True)  # Average issues per job
    quality_trend = Column(String, nullable=True)  # improving, stable, declining

    # Cost metrics
    total_cost_usd = Column(Float, default=0.0)
    avg_cost_per_job = Column(Float, nullable=True)
    cost_trend = Column(String, nullable=True)  # increasing, stable, decreasing

    # Performance metrics
    avg_generation_time_seconds = Column(Float, nullable=True)
    avg_retry_count = Column(Float, nullable=True)

    # Provider analytics
    most_used_provider = Column(String, nullable=True)  # anthropic, openai, google
    most_used_strategy = Column(String, nullable=True)  # multi_stage, single_shot
    provider_distribution = Column(JSON, nullable=True)  # {"anthropic": 60, "openai": 40}

    # Recommendation score (0-100)
    # Based on success_rate, avg_qc_score, avg_cost, etc.
    recommendation_score = Column(Float, default=0.0)
    recommendation_reason = Column(Text, nullable=True)

    # Timestamps
    first_job_at = Column(DateTime(timezone=True), nullable=True)
    last_job_at = Column(DateTime(timezone=True), nullable=True)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index('idx_publisher_user_domain', 'user_id', 'publisher_domain', unique=True),
        Index('idx_publisher_recommendation', 'user_id', 'recommendation_score'),
        Index('idx_publisher_success_rate', 'user_id', 'success_rate'),
    )


class PublisherInsight(Base):
    """
    Publisher insights and recommendations.

    Stores AI-generated insights about publisher performance:
    - What works well for this publisher
    - Common failure patterns
    - Optimization suggestions
    - Competitive comparisons
    """

    __tablename__ = "publisher_insights"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    publisher_domain = Column(String, nullable=False, index=True)

    # Insight type
    insight_type = Column(String, nullable=False)  # recommendation, warning, success_pattern, failure_pattern
    priority = Column(String, default="medium")  # high, medium, low

    # Insight content
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    action_items = Column(JSON, nullable=True)  # Array of suggested actions

    # Supporting data
    confidence_score = Column(Float, default=0.0)  # 0-100, how confident is this insight
    sample_size = Column(Integer, default=0)  # Number of jobs this is based on
    evidence = Column(JSON, nullable=True)  # Supporting statistics/examples

    # Metadata
    is_active = Column(Boolean, default=True)  # Can be dismissed by user
    is_automated = Column(Boolean, default=True)  # AI-generated vs manual
    tags = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Insights can expire

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index('idx_insight_user_domain', 'user_id', 'publisher_domain'),
        Index('idx_insight_type', 'insight_type'),
        Index('idx_insight_priority', 'user_id', 'priority'),
        Index('idx_insight_active', 'user_id', 'is_active'),
    )
