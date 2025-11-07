"""
Analytics and cost estimation routes.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from ..database import get_db
from ..models.database import User, Job, JobResult
from ..models.schemas import (
    CostEstimateRequest, CostEstimateResponse,
    AnalyticsResponse, JobStatus
)
from ..auth import get_current_user
from ..core.bacowr_wrapper import bacowr

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/cost/estimate", response_model=CostEstimateResponse)
def estimate_cost(
    estimate_request: CostEstimateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Estimate cost for job(s).

    Provides cost estimate based on provider, strategy, and number of jobs.
    """
    estimate = bacowr.estimate_cost(
        llm_provider=estimate_request.llm_provider,
        writing_strategy=estimate_request.writing_strategy,
        num_jobs=estimate_request.num_jobs
    )

    return CostEstimateResponse(
        num_jobs=estimate_request.num_jobs,
        provider=estimate_request.llm_provider,
        strategy=estimate_request.writing_strategy,
        **estimate
    )


@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get analytics for user's jobs.

    Args:
        days: Number of days to include in analytics (default: 30)

    Returns:
        Analytics including job counts, costs, success rates, etc.
    """
    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()

    # Base query for jobs in period
    jobs_query = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.created_at >= period_start
    )

    # Total jobs
    total_jobs = jobs_query.count()

    # Jobs by status
    jobs_by_status = {}
    status_counts = jobs_query.with_entities(
        Job.status,
        func.count(Job.id)
    ).group_by(Job.status).all()

    for status, count in status_counts:
        jobs_by_status[status] = count

    # Jobs by provider
    jobs_by_provider = {}
    provider_counts = jobs_query.filter(
        Job.llm_provider.isnot(None)
    ).with_entities(
        Job.llm_provider,
        func.count(Job.id)
    ).group_by(Job.llm_provider).all()

    for provider, count in provider_counts:
        jobs_by_provider[provider or "auto"] = count

    # Jobs by strategy
    jobs_by_strategy = {}
    strategy_counts = jobs_query.filter(
        Job.writing_strategy.isnot(None)
    ).with_entities(
        Job.writing_strategy,
        func.count(Job.id)
    ).group_by(Job.writing_strategy).all()

    for strategy, count in strategy_counts:
        jobs_by_strategy[strategy] = count

    # Total cost
    total_cost = db.query(func.sum(Job.actual_cost)).filter(
        Job.user_id == current_user.id,
        Job.created_at >= period_start,
        Job.actual_cost.isnot(None)
    ).scalar() or 0.0

    # Average generation time
    avg_time = db.query(func.avg(JobResult.generation_time_seconds)).filter(
        JobResult.user_id == current_user.id,
        JobResult.created_at >= period_start
    ).scalar()

    # Success rate
    delivered_count = jobs_query.filter(Job.status == JobStatus.DELIVERED).count()
    success_rate = (delivered_count / total_jobs * 100) if total_jobs > 0 else 0.0

    return AnalyticsResponse(
        total_jobs=total_jobs,
        jobs_by_status=jobs_by_status,
        jobs_by_provider=jobs_by_provider,
        jobs_by_strategy=jobs_by_strategy,
        total_cost=float(total_cost),
        avg_generation_time=float(avg_time) if avg_time else None,
        success_rate=float(success_rate),
        period_start=period_start,
        period_end=period_end
    )


@router.get("/providers")
def get_available_providers(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available LLM providers.

    Returns provider information including models and features.
    """
    return {
        "providers": [
            {
                "id": "anthropic",
                "name": "Anthropic Claude",
                "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
                "default_model": "claude-3-haiku-20240307",
                "tested": True,
                "available": True
            },
            {
                "id": "openai",
                "name": "OpenAI GPT",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                "default_model": "gpt-4o-mini",
                "tested": False,
                "available": True
            },
            {
                "id": "google",
                "name": "Google Gemini",
                "models": ["gemini-1.5-flash", "gemini-1.5-pro"],
                "default_model": "gemini-1.5-flash",
                "tested": False,
                "available": True
            }
        ],
        "strategies": [
            {
                "id": "multi_stage",
                "name": "Multi-Stage",
                "description": "Best quality - 3 LLM calls (outline → content → polish)",
                "estimated_time": "30-60 seconds",
                "recommended": True
            },
            {
                "id": "single_shot",
                "name": "Single-Shot",
                "description": "Fast - 1 LLM call with optimized prompt",
                "estimated_time": "10-20 seconds",
                "recommended": False
            }
        ]
    }
