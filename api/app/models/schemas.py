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
