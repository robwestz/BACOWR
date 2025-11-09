"""
Analytics and cost estimation routes.

Comprehensive analytics dashboard with cost tracking, performance metrics,
time-series data, and export functionality.
"""

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import csv
import json
import io

from ..database import get_db
from ..models.database import User, Job, JobResult
from ..models.schemas import (
    CostEstimateRequest, CostEstimateResponse,
    AnalyticsResponse, JobStatus
)
from ..auth import get_current_user, get_current_admin_user
from ..core.bacowr_wrapper import bacowr

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============================================================================
# Cost Estimation
# ============================================================================

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


# ============================================================================
# User Analytics
# ============================================================================

@router.get("")
def get_analytics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive analytics for user's jobs.

    Args:
        days: Number of days to include in analytics (default: 30)

    Returns:
        Detailed analytics including:
        - Job counts by status, provider, strategy
        - Cost breakdown and trends
        - Performance metrics
        - Success rates
        - Time-series data for charts
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

    return {
        "total_jobs": total_jobs,
        "jobs_by_status": jobs_by_status,
        "jobs_by_provider": jobs_by_provider,
        "jobs_by_strategy": jobs_by_strategy,
        "total_cost": float(total_cost),
        "avg_generation_time": float(avg_time) if avg_time else None,
        "success_rate": float(success_rate),
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat()
    }


@router.get("/cost-breakdown")
def get_cost_breakdown(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed cost breakdown by provider and strategy.

    Returns cost analysis including:
    - Total cost per provider
    - Average cost per job by provider
    - Cost per strategy
    - Most expensive jobs
    """
    period_start = datetime.utcnow() - timedelta(days=days)

    # Cost by provider
    cost_by_provider = {}
    provider_costs = db.query(
        Job.llm_provider,
        func.sum(Job.actual_cost).label('total_cost'),
        func.avg(Job.actual_cost).label('avg_cost'),
        func.count(Job.id).label('job_count')
    ).filter(
        Job.user_id == current_user.id,
        Job.created_at >= period_start,
        Job.actual_cost.isnot(None)
    ).group_by(Job.llm_provider).all()

    for provider, total, avg, count in provider_costs:
        cost_by_provider[provider or "auto"] = {
            "total_cost": float(total or 0),
            "avg_cost_per_job": float(avg or 0),
            "job_count": count
        }

    # Cost by strategy
    cost_by_strategy = {}
    strategy_costs = db.query(
        Job.writing_strategy,
        func.sum(Job.actual_cost).label('total_cost'),
        func.avg(Job.actual_cost).label('avg_cost'),
        func.count(Job.id).label('job_count')
    ).filter(
        Job.user_id == current_user.id,
        Job.created_at >= period_start,
        Job.actual_cost.isnot(None)
    ).group_by(Job.writing_strategy).all()

    for strategy, total, avg, count in strategy_costs:
        cost_by_strategy[strategy] = {
            "total_cost": float(total or 0),
            "avg_cost_per_job": float(avg or 0),
            "job_count": count
        }

    # Most expensive jobs
    expensive_jobs = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.created_at >= period_start,
        Job.actual_cost.isnot(None)
    ).order_by(Job.actual_cost.desc()).limit(10).all()

    expensive_jobs_list = [
        {
            "job_id": job.id,
            "cost": float(job.actual_cost),
            "provider": job.llm_provider,
            "strategy": job.writing_strategy,
            "created_at": job.created_at.isoformat(),
            "status": job.status
        }
        for job in expensive_jobs
    ]

    # Total cost
    total_cost = sum(p["total_cost"] for p in cost_by_provider.values())

    return {
        "total_cost": total_cost,
        "cost_by_provider": cost_by_provider,
        "cost_by_strategy": cost_by_strategy,
        "most_expensive_jobs": expensive_jobs_list,
        "period_days": days
    }


@router.get("/performance")
def get_performance_metrics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get performance metrics for jobs.

    Returns:
    - Average generation times by provider
    - QC pass rates
    - Issue counts and categories
    - Provider comparison
    """
    period_start = datetime.utcnow() - timedelta(days=days)

    # Generation time by provider
    time_by_provider = {}
    provider_times = db.query(
        JobResult.provider_used,
        func.avg(JobResult.generation_time_seconds).label('avg_time'),
        func.min(JobResult.generation_time_seconds).label('min_time'),
        func.max(JobResult.generation_time_seconds).label('max_time'),
        func.count(JobResult.id).label('count')
    ).filter(
        JobResult.user_id == current_user.id,
        JobResult.created_at >= period_start,
        JobResult.generation_time_seconds.isnot(None)
    ).group_by(JobResult.provider_used).all()

    for provider, avg, min_t, max_t, count in provider_times:
        if provider:
            time_by_provider[provider] = {
                "avg_seconds": float(avg),
                "min_seconds": float(min_t),
                "max_seconds": float(max_t),
                "sample_count": count
            }

    # QC metrics
    qc_stats = db.query(
        func.count(JobResult.id).label('total'),
        func.sum(case((JobResult.delivered == True, 1), else_=0)).label('delivered'),
        func.avg(JobResult.qc_score).label('avg_score'),
        func.avg(JobResult.issue_count).label('avg_issues')
    ).filter(
        JobResult.user_id == current_user.id,
        JobResult.created_at >= period_start
    ).first()

    total_qc = qc_stats.total or 0
    delivered = qc_stats.delivered or 0
    delivery_rate = (delivered / total_qc * 100) if total_qc > 0 else 0

    # Issue breakdown by QC status
    qc_status_breakdown = db.query(
        JobResult.qc_status,
        func.count(JobResult.id).label('count')
    ).filter(
        JobResult.user_id == current_user.id,
        JobResult.created_at >= period_start
    ).group_by(JobResult.qc_status).all()

    qc_by_status = {status: count for status, count in qc_status_breakdown if status}

    return {
        "generation_time_by_provider": time_by_provider,
        "qc_metrics": {
            "total_jobs": total_qc,
            "delivered_jobs": delivered,
            "delivery_rate": float(delivery_rate),
            "avg_qc_score": float(qc_stats.avg_score) if qc_stats.avg_score else None,
            "avg_issue_count": float(qc_stats.avg_issues) if qc_stats.avg_issues else None
        },
        "qc_status_breakdown": qc_by_status,
        "period_days": days
    }


@router.get("/time-series")
def get_time_series(
    days: int = 30,
    interval: str = "day",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get time-series data for charts.

    Args:
        days: Number of days to include
        interval: Grouping interval ("day", "week", "month")

    Returns:
        Time-series data for:
        - Job counts over time
        - Cost over time
        - Success rate over time
    """
    period_start = datetime.utcnow() - timedelta(days=days)

    # Determine SQL date truncation based on interval
    if interval == "week":
        date_trunc = func.date_trunc('week', Job.created_at)
    elif interval == "month":
        date_trunc = func.date_trunc('month', Job.created_at)
    else:  # day
        date_trunc = func.date_trunc('day', Job.created_at)

    # Jobs over time
    jobs_over_time = db.query(
        date_trunc.label('period'),
        func.count(Job.id).label('job_count'),
        func.sum(Job.actual_cost).label('total_cost'),
        func.sum(case((Job.status == JobStatus.DELIVERED, 1), else_=0)).label('delivered_count')
    ).filter(
        Job.user_id == current_user.id,
        Job.created_at >= period_start
    ).group_by('period').order_by('period').all()

    time_series_data = []
    for period, jobs, cost, delivered in jobs_over_time:
        success_rate = (delivered / jobs * 100) if jobs > 0 else 0
        time_series_data.append({
            "date": period.isoformat() if period else None,
            "job_count": jobs,
            "cost": float(cost or 0),
            "delivered_count": delivered,
            "success_rate": float(success_rate)
        })

    return {
        "interval": interval,
        "period_days": days,
        "data": time_series_data
    }


# ============================================================================
# Export Functions
# ============================================================================

@router.get("/export/csv")
def export_jobs_csv(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export jobs data as CSV.

    Returns CSV file with all jobs in the specified period.
    """
    period_start = datetime.utcnow() - timedelta(days=days)

    jobs = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.created_at >= period_start
    ).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        'Job ID', 'Created At', 'Status', 'Publisher', 'Target URL',
        'Anchor Text', 'Provider', 'Strategy', 'Estimated Cost', 'Actual Cost',
        'Started At', 'Completed At'
    ])

    # Data
    for job in jobs:
        writer.writerow([
            job.id,
            job.created_at.isoformat() if job.created_at else '',
            job.status,
            job.publisher_domain,
            job.target_url,
            job.anchor_text,
            job.llm_provider or '',
            job.writing_strategy or '',
            job.estimated_cost or '',
            job.actual_cost or '',
            job.started_at.isoformat() if job.started_at else '',
            job.completed_at.isoformat() if job.completed_at else ''
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=bacowr_jobs_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        }
    )


@router.get("/export/json")
def export_jobs_json(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export jobs data as JSON.

    Returns JSON file with all jobs in the specified period.
    """
    period_start = datetime.utcnow() - timedelta(days=days)

    jobs = db.query(Job).filter(
        Job.user_id == current_user.id,
        Job.created_at >= period_start
    ).all()

    jobs_data = []
    for job in jobs:
        jobs_data.append({
            "id": job.id,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "status": job.status,
            "publisher_domain": job.publisher_domain,
            "target_url": job.target_url,
            "anchor_text": job.anchor_text,
            "llm_provider": job.llm_provider,
            "writing_strategy": job.writing_strategy,
            "estimated_cost": float(job.estimated_cost) if job.estimated_cost else None,
            "actual_cost": float(job.actual_cost) if job.actual_cost else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        })

    json_str = json.dumps(jobs_data, indent=2)

    return Response(
        content=json_str,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=bacowr_jobs_{datetime.utcnow().strftime('%Y%m%d')}.json"
        }
    )


# ============================================================================
# Admin Analytics
# ============================================================================

@router.get("/admin/overview")
def get_admin_overview(
    days: int = 30,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get system-wide analytics (admin only).

    Returns:
    - Total jobs across all users
    - Total cost across all users
    - User activity stats
    - System performance metrics
    """
    period_start = datetime.utcnow() - timedelta(days=days)

    # System-wide stats
    total_jobs = db.query(func.count(Job.id)).filter(
        Job.created_at >= period_start
    ).scalar() or 0

    total_cost = db.query(func.sum(Job.actual_cost)).filter(
        Job.created_at >= period_start,
        Job.actual_cost.isnot(None)
    ).scalar() or 0.0

    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(func.distinct(Job.user_id))).filter(
        Job.created_at >= period_start
    ).scalar() or 0

    # Jobs by status (system-wide)
    status_counts = db.query(
        Job.status,
        func.count(Job.id)
    ).filter(
        Job.created_at >= period_start
    ).group_by(Job.status).all()

    jobs_by_status = {status: count for status, count in status_counts}

    # Top users by job count
    top_users = db.query(
        User.email,
        func.count(Job.id).label('job_count'),
        func.sum(Job.actual_cost).label('total_cost')
    ).join(Job).filter(
        Job.created_at >= period_start
    ).group_by(User.email).order_by(func.count(Job.id).desc()).limit(10).all()

    top_users_list = [
        {
            "email": email,
            "job_count": count,
            "total_cost": float(cost or 0)
        }
        for email, count, cost in top_users
    ]

    # Provider usage (system-wide)
    provider_usage = db.query(
        Job.llm_provider,
        func.count(Job.id).label('count')
    ).filter(
        Job.created_at >= period_start,
        Job.llm_provider.isnot(None)
    ).group_by(Job.llm_provider).all()

    provider_stats = {provider: count for provider, count in provider_usage}

    return {
        "total_jobs": total_jobs,
        "total_cost": float(total_cost),
        "total_users": total_users,
        "active_users": active_users,
        "jobs_by_status": jobs_by_status,
        "top_users": top_users_list,
        "provider_usage": provider_stats,
        "period_days": days
    }


@router.get("/admin/user/{user_id}")
def get_user_analytics(
    user_id: str,
    days: int = 30,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    """
    Get analytics for a specific user (admin only).

    Returns comprehensive analytics for the specified user.
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")

    period_start = datetime.utcnow() - timedelta(days=days)

    # Use same queries as regular analytics but for specific user
    jobs_query = db.query(Job).filter(
        Job.user_id == user_id,
        Job.created_at >= period_start
    )

    total_jobs = jobs_query.count()
    total_cost = db.query(func.sum(Job.actual_cost)).filter(
        Job.user_id == user_id,
        Job.created_at >= period_start,
        Job.actual_cost.isnot(None)
    ).scalar() or 0.0

    delivered_count = jobs_query.filter(Job.status == JobStatus.DELIVERED).count()
    success_rate = (delivered_count / total_jobs * 100) if total_jobs > 0 else 0.0

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat()
        },
        "analytics": {
            "total_jobs": total_jobs,
            "total_cost": float(total_cost),
            "success_rate": float(success_rate),
            "period_days": days
        }
    }


# ============================================================================
# Provider Information
# ============================================================================

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
