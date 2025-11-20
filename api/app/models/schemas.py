"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# Enums

class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    DELIVERED = "delivered"
    BLOCKED = "blocked"
    ABORTED = "aborted"


class LLMProvider(str, Enum):
    """LLM provider enumeration."""
    AUTO = "auto"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class WritingStrategy(str, Enum):
    """Writing strategy enumeration."""
    MULTI_STAGE = "multi_stage"
    SINGLE_SHOT = "single_shot"


class BatchStatus(str, Enum):
    """Batch status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY_FOR_REVIEW = "ready_for_review"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewStatus(str, Enum):
    """Review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REGENERATION = "needs_regeneration"
    REGENERATING = "regenerating"
    REGENERATED = "regenerated"


# Job Schemas

class JobCreate(BaseModel):
    """Schema for creating a new job."""
    publisher_domain: str = Field(..., min_length=3, max_length=255)
    target_url: str = Field(..., min_length=10, max_length=2048)
    anchor_text: str = Field(..., min_length=1, max_length=500)

    llm_provider: Optional[LLMProvider] = LLMProvider.AUTO
    writing_strategy: Optional[WritingStrategy] = WritingStrategy.MULTI_STAGE
    country: Optional[str] = Field(default="se", min_length=2, max_length=2)
    use_ahrefs: Optional[bool] = True
    enable_llm_profiling: Optional[bool] = True

    @field_validator('publisher_domain')
    @classmethod
    def validate_publisher_domain(cls, v: str) -> str:
        """Ensure publisher domain doesn't include protocol."""
        if v.startswith('http://') or v.startswith('https://'):
            raise ValueError('Publisher domain should not include protocol (http:// or https://)')
        return v.lower()

    @field_validator('target_url')
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        """Ensure target URL includes protocol."""
        if not v.startswith('http://') and not v.startswith('https://'):
            raise ValueError('Target URL must include protocol (http:// or https://)')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "publisher_domain": "aftonbladet.se",
                "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
                "anchor_text": "läs mer om AI",
                "llm_provider": "anthropic",
                "writing_strategy": "multi_stage",
                "country": "se",
                "use_ahrefs": True,
                "enable_llm_profiling": True
            }
        }


class JobUpdate(BaseModel):
    """Schema for updating a job."""
    status: Optional[JobStatus] = None
    article_text: Optional[str] = None
    qc_report: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    actual_cost: Optional[float] = None
    error_message: Optional[str] = None


class JobResponse(BaseModel):
    """Schema for job response."""
    id: str
    user_id: str
    publisher_domain: str
    target_url: str
    anchor_text: str
    llm_provider: Optional[str]
    writing_strategy: Optional[str]
    country: str
    status: str
    estimated_cost: Optional[float]
    actual_cost: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    """Schema for detailed job response with all data."""
    article_text: Optional[str]
    job_package: Optional[Dict[str, Any]]
    qc_report: Optional[Dict[str, Any]]
    execution_log: Optional[Dict[str, Any]]
    metrics: Optional[Dict[str, Any]]
    retry_count: int

    class Config:
        from_attributes = True


# Backlink Schemas

class BacklinkCreate(BaseModel):
    """Schema for creating a backlink."""
    publisher_domain: str = Field(..., min_length=3, max_length=255)
    publisher_url: Optional[str] = Field(None, max_length=2048)
    target_url: str = Field(..., min_length=10, max_length=2048)
    anchor_text: str = Field(..., min_length=1, max_length=500)
    domain_authority: Optional[int] = Field(None, ge=0, le=100)
    page_authority: Optional[int] = Field(None, ge=0, le=100)
    traffic_estimate: Optional[int] = Field(None, ge=0)
    backlink_count: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_metrics: Optional[Dict[str, Any]] = None
    published_at: Optional[datetime] = None


class BacklinkBulkImport(BaseModel):
    """Schema for bulk importing backlinks."""
    backlinks: List[BacklinkCreate] = Field(..., min_length=1, max_length=1000)


class BacklinkResponse(BaseModel):
    """Schema for backlink response."""
    id: str
    user_id: str
    publisher_domain: str
    publisher_url: Optional[str]
    target_url: str
    anchor_text: str
    domain_authority: Optional[int]
    page_authority: Optional[int]
    traffic_estimate: Optional[int]
    category: Optional[str]
    language: Optional[str]
    notes: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class BacklinkStats(BaseModel):
    """Schema for backlink statistics."""
    total_count: int
    by_publisher: Dict[str, int]
    by_category: Dict[str, int]
    by_language: Dict[str, int]
    avg_domain_authority: Optional[float]
    avg_page_authority: Optional[float]
    total_traffic_estimate: Optional[int]


# Analytics Schemas

class CostEstimateRequest(BaseModel):
    """Schema for cost estimation request."""
    llm_provider: LLMProvider = LLMProvider.ANTHROPIC
    writing_strategy: WritingStrategy = WritingStrategy.MULTI_STAGE
    num_jobs: int = Field(1, ge=1, le=10000)


class CostEstimateResponse(BaseModel):
    """Schema for cost estimation response."""
    num_jobs: int
    provider: str
    strategy: str
    estimated_cost_per_job: float
    estimated_total_cost: float
    estimated_time_seconds: float


class AnalyticsResponse(BaseModel):
    """Schema for analytics response."""
    total_jobs: int
    jobs_by_status: Dict[str, int]
    jobs_by_provider: Dict[str, int]
    jobs_by_strategy: Dict[str, int]
    total_cost: float
    avg_generation_time: Optional[float]
    success_rate: float
    period_start: datetime
    period_end: datetime


# User Schemas

class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: str = Field(..., min_length=5, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    api_key: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# WebSocket Schemas

class JobProgressUpdate(BaseModel):
    """Schema for job progress updates via WebSocket."""
    job_id: str
    status: str
    progress: float = Field(..., ge=0, le=100)  # Percentage 0-100
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Pagination

class PaginationParams(BaseModel):
    """Schema for pagination parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic schema for paginated responses."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: List[Any], total: int, page: int, page_size: int):
        """Create a paginated response."""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )


# Batch Schemas

class BatchCreate(BaseModel):
    """Schema for creating a batch."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    job_ids: List[str] = Field(..., min_length=1, max_length=1000)
    batch_config: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Daily batch 2025-11-19",
                "description": "175 backlinks for review",
                "job_ids": ["job-uuid-1", "job-uuid-2"],
                "batch_config": {
                    "auto_approve_threshold": 0.95,
                    "require_manual_review": True
                }
            }
        }


class BatchResponse(BaseModel):
    """Schema for batch response."""
    id: str
    user_id: str
    name: str
    description: Optional[str]
    status: str
    total_items: int
    items_completed: int
    items_approved: int
    items_rejected: int
    items_pending_review: int
    estimated_total_cost: Optional[float]
    actual_total_cost: Optional[float]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    review_started_at: Optional[datetime]
    review_completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class BatchItemResponse(BaseModel):
    """Schema for batch review item response."""
    id: str
    batch_id: str
    job_id: str
    review_status: str
    reviewer_notes: Optional[str]
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    qc_score: Optional[float]
    qc_status: Optional[str]
    qc_issues_count: int
    regeneration_count: int
    original_job_id: Optional[str]
    created_at: datetime

    # Include job details for convenience
    job: Optional[JobDetailResponse] = None

    class Config:
        from_attributes = True


class BatchDetailResponse(BatchResponse):
    """Schema for detailed batch response with items."""
    items: List[BatchItemResponse]
    batch_config: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class ReviewDecisionRequest(BaseModel):
    """Schema for review decision."""
    decision: ReviewStatus
    reviewer_notes: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "approved",
                "reviewer_notes": "Excellent quality, approved for publication"
            }
        }


class BatchExportResponse(BaseModel):
    """Schema for batch export response."""
    batch_id: str
    total_approved: int
    export_format: str
    download_url: Optional[str]
    file_path: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch-uuid",
                "total_approved": 142,
                "export_format": "json",
                "download_url": "/api/v1/batches/batch-uuid/download",
                "file_path": "storage/exports/batch-uuid-approved.json",
                "created_at": "2025-11-19T12:00:00Z"
            }
        }


# ==============================================================================
# Wave 5: Authentication & User Management Schemas
# ==============================================================================


class UserRole(str, Enum):
    """User role enumeration."""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class AccountStatus(str, Enum):
    """Account status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class UserRegistrationRequest(BaseModel):
    """Schema for user registration request."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")
    full_name: Optional[str] = Field(None, description="User full name")
    username: Optional[str] = Field(None, description="Optional username")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "SecurePassword123!",
                "full_name": "John Doe",
                "username": "johndoe"
            }
        }


class UserLoginRequest(BaseModel):
    """Schema for user login request."""
    email: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "password": "SecurePassword123!"
            }
        }


class TokenResponse(BaseModel):
    """Schema for token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: 'UserResponse'

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "user-uuid",
                    "email": "john@example.com",
                    "role": "editor"
                }
            }
        }


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: str

    class Config:
        json_schema_extra = {
            "example": {"email": "john@example.com"}
        }


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    reset_token: str
    new_password: str = Field(..., min_length=8)

    class Config:
        json_schema_extra = {
            "example": {
                "reset_token": "reset-token-here",
                "new_password": "NewSecurePassword123!"
            }
        }


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    role: str
    account_status: str
    is_active: bool
    jobs_created_count: int
    jobs_quota: int
    tokens_used: int
    tokens_quota: int
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "user-uuid",
                "email": "john@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "role": "editor",
                "account_status": "active",
                "is_active": True,
                "jobs_created_count": 42,
                "jobs_quota": 1000,
                "tokens_used": 125000,
                "tokens_quota": 1000000,
                "last_login": "2025-11-19T12:00:00Z",
                "created_at": "2025-11-01T10:00:00Z"
            }
        }


class UserUpdateRequest(BaseModel):
    """Schema for user update request."""
    full_name: Optional[str] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
    jobs_quota: Optional[int] = None
    tokens_quota: Optional[int] = None
    account_status: Optional[AccountStatus] = None

    class Config:
        json_schema_extra = {
            "example": {
                "full_name": "John Smith",
                "role": "editor",
                "jobs_quota": 2000
            }
        }


class UserListResponse(BaseModel):
    """Schema for user list response."""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int

    class Config:
        json_schema_extra = {
            "example": {
                "users": [],
                "total": 25,
                "page": 1,
                "page_size": 10
            }
        }


class QuotaStatus(BaseModel):
    """Schema for user quota status."""
    jobs_used: int
    jobs_quota: int
    jobs_remaining: int
    tokens_used: int
    tokens_quota: int
    tokens_remaining: int
    quota_exceeded: bool

    class Config:
        json_schema_extra = {
            "example": {
                "jobs_used": 42,
                "jobs_quota": 1000,
                "jobs_remaining": 958,
                "tokens_used": 125000,
                "tokens_quota": 1000000,
                "tokens_remaining": 875000,
                "quota_exceeded": False
            }
        }
