"""
Publisher Research routes.

Endpoints for publisher performance analytics, recommendations, and insights.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models.database import User, PublisherMetrics, PublisherInsight
from ..models.schemas import (
    PublisherMetricsResponse,
    PublisherInsightCreate, PublisherInsightUpdate, PublisherInsightResponse,
    PublisherComparisonRequest, PublisherComparisonResponse, PublisherComparisonItem,
    PublisherRecommendationRequest, PublisherRecommendationResponse,
    InsightType, InsightPriority
)
from ..auth import get_current_user
from ..rate_limit import limiter, RATE_LIMITS
from ..services.publisher_metrics import (
    update_publisher_metrics,
    update_all_publisher_metrics,
    generate_publisher_insights
)

router = APIRouter(prefix="/publishers", tags=["publisher-research"])


@router.get("/metrics", response_model=List[PublisherMetricsResponse])
@limiter.limit(RATE_LIMITS["list_jobs"])
def list_publisher_metrics(
    request: Request,
    min_jobs: int = 1,
    sort_by: str = "recommendation_score",  # recommendation_score, success_rate, total_jobs
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all publisher metrics for current user.

    Optional filters:
    - min_jobs: Minimum number of jobs to include publisher
    - sort_by: Sort criteria (recommendation_score, success_rate, total_jobs)
    """
    query = db.query(PublisherMetrics).filter(
        PublisherMetrics.user_id == current_user.id,
        PublisherMetrics.total_jobs >= min_jobs
    )

    # Sort
    if sort_by == "recommendation_score":
        query = query.order_by(desc(PublisherMetrics.recommendation_score))
    elif sort_by == "success_rate":
        query = query.order_by(desc(PublisherMetrics.success_rate))
    elif sort_by == "total_jobs":
        query = query.order_by(desc(PublisherMetrics.total_jobs))
    else:
        query = query.order_by(desc(PublisherMetrics.last_updated_at))

    metrics = query.all()

    return [PublisherMetricsResponse.model_validate(m) for m in metrics]


@router.get("/metrics/{publisher_domain}", response_model=PublisherMetricsResponse)
@limiter.limit(RATE_LIMITS["get_job"])
def get_publisher_metrics(
    request: Request,
    publisher_domain: str,
    refresh: bool = False,  # Force recalculation
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get metrics for a specific publisher.

    Optional:
    - refresh=true: Force recalculation of metrics
    """
    if refresh:
        # Force update
        metrics = update_publisher_metrics(db, current_user.id, publisher_domain)
    else:
        # Get existing
        metrics = db.query(PublisherMetrics).filter(
            PublisherMetrics.user_id == current_user.id,
            PublisherMetrics.publisher_domain == publisher_domain
        ).first()

        if not metrics:
            # Create if doesn't exist
            metrics = update_publisher_metrics(db, current_user.id, publisher_domain)

    if not metrics or metrics.total_jobs == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No metrics found for publisher {publisher_domain}"
        )

    return PublisherMetricsResponse.model_validate(metrics)


@router.post("/metrics/refresh", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/hour")  # Expensive operation
def refresh_all_metrics(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Refresh metrics for all publishers.

    This is an expensive operation, rate limited to 10/hour.
    """
    count = update_all_publisher_metrics(db, current_user.id)

    return {
        "message": "Metrics refresh initiated",
        "publishers_updated": count
    }


@router.post("/compare", response_model=PublisherComparisonResponse)
@limiter.limit(RATE_LIMITS["analytics"])
def compare_publishers(
    request: Request,
    comparison: PublisherComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Compare performance across multiple publishers.

    Provide 2-10 publisher domains to compare their metrics.
    """
    metrics_list = db.query(PublisherMetrics).filter(
        PublisherMetrics.user_id == current_user.id,
        PublisherMetrics.publisher_domain.in_(comparison.publisher_domains)
    ).all()

    if len(metrics_list) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Found only {len(metrics_list)} publishers with metrics. Need at least 2."
        )

    # Build comparison items
    comparison_items = []
    for m in metrics_list:
        comparison_items.append(
            PublisherComparisonItem(
                publisher_domain=m.publisher_domain,
                total_jobs=m.total_jobs,
                success_rate=m.success_rate,
                avg_qc_score=m.avg_qc_score,
                avg_cost_per_job=m.avg_cost_per_job,
                recommendation_score=m.recommendation_score,
                rank=0  # Will be set after sorting
            )
        )

    # Sort by recommendation_score (highest first) and assign ranks
    comparison_items.sort(key=lambda x: x.recommendation_score, reverse=True)
    for i, item in enumerate(comparison_items, start=1):
        item.rank = i

    # Find best publisher
    best_publisher = comparison_items[0].publisher_domain

    return PublisherComparisonResponse(
        publishers=comparison_items,
        best_publisher=best_publisher,
        metrics_compared=comparison.metrics,
        comparison_date=datetime.utcnow()
    )


@router.post("/recommendations", response_model=PublisherRecommendationResponse)
@limiter.limit(RATE_LIMITS["analytics"])
def get_recommendations(
    request: Request,
    req: PublisherRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recommended publishers based on performance.

    Criteria:
    - balanced: Balance of quality, cost, and success rate
    - cost_optimized: Prioritize low cost
    - quality_focused: Prioritize high quality scores
    """
    query = db.query(PublisherMetrics).filter(
        PublisherMetrics.user_id == current_user.id,
        PublisherMetrics.total_jobs >= req.min_jobs
    )

    # Apply criteria
    if req.criteria == "cost_optimized":
        # Sort by lowest cost, then by success rate
        query = query.order_by(
            PublisherMetrics.avg_cost_per_job.asc().nulls_last(),
            desc(PublisherMetrics.success_rate)
        )
    elif req.criteria == "quality_focused":
        # Sort by highest quality, then by success rate
        query = query.order_by(
            desc(PublisherMetrics.avg_qc_score),
            desc(PublisherMetrics.success_rate)
        )
    else:  # balanced
        # Sort by recommendation score (already balanced)
        query = query.order_by(desc(PublisherMetrics.recommendation_score))

    metrics = query.limit(req.limit).all()

    total_evaluated = db.query(PublisherMetrics).filter(
        PublisherMetrics.user_id == current_user.id,
        PublisherMetrics.total_jobs >= req.min_jobs
    ).count()

    return PublisherRecommendationResponse(
        recommendations=[PublisherMetricsResponse.model_validate(m) for m in metrics],
        criteria=req.criteria,
        total_publishers_evaluated=total_evaluated
    )


# ============================================================================
# PUBLISHER INSIGHTS
# ============================================================================

@router.get("/insights", response_model=List[PublisherInsightResponse])
@limiter.limit(RATE_LIMITS["list_jobs"])
def list_insights(
    request: Request,
    publisher_domain: Optional[str] = None,
    insight_type: Optional[InsightType] = None,
    priority: Optional[InsightPriority] = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List publisher insights for current user.

    Optional filters:
    - publisher_domain: Filter by publisher
    - insight_type: Filter by type (recommendation, warning, etc.)
    - priority: Filter by priority (high, medium, low)
    - active_only: Show only active insights
    """
    query = db.query(PublisherInsight).filter(PublisherInsight.user_id == current_user.id)

    if publisher_domain:
        query = query.filter(PublisherInsight.publisher_domain == publisher_domain)

    if insight_type:
        query = query.filter(PublisherInsight.insight_type == insight_type.value)

    if priority:
        query = query.filter(PublisherInsight.priority == priority.value)

    if active_only:
        query = query.filter(PublisherInsight.is_active == True)

    insights = query.order_by(
        PublisherInsight.priority.desc(),
        PublisherInsight.created_at.desc()
    ).all()

    return [PublisherInsightResponse.model_validate(i) for i in insights]


@router.get("/insights/{insight_id}", response_model=PublisherInsightResponse)
@limiter.limit(RATE_LIMITS["get_job"])
def get_insight(
    request: Request,
    insight_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific insight by ID."""
    insight = db.query(PublisherInsight).filter(
        PublisherInsight.id == insight_id,
        PublisherInsight.user_id == current_user.id
    ).first()

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )

    return PublisherInsightResponse.model_validate(insight)


@router.post("/insights", response_model=PublisherInsightResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create_job"])
def create_insight(
    request: Request,
    insight_data: PublisherInsightCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a manual insight.

    Automated insights are generated by the system, but users can create custom ones.
    """
    insight = PublisherInsight(
        user_id=current_user.id,
        publisher_domain=insight_data.publisher_domain,
        insight_type=insight_data.insight_type.value,
        priority=insight_data.priority.value,
        title=insight_data.title,
        description=insight_data.description,
        action_items=insight_data.action_items,
        confidence_score=insight_data.confidence_score,
        sample_size=insight_data.sample_size,
        evidence=insight_data.evidence,
        is_automated=False,  # User-created
        tags=insight_data.tags,
        expires_at=insight_data.expires_at
    )

    db.add(insight)
    db.commit()
    db.refresh(insight)

    return PublisherInsightResponse.model_validate(insight)


@router.put("/insights/{insight_id}", response_model=PublisherInsightResponse)
@limiter.limit(RATE_LIMITS["create_job"])
def update_insight(
    request: Request,
    insight_id: str,
    insight_data: PublisherInsightUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an insight (typically to dismiss or change priority).
    """
    insight = db.query(PublisherInsight).filter(
        PublisherInsight.id == insight_id,
        PublisherInsight.user_id == current_user.id
    ).first()

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )

    # Update fields
    update_data = insight_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(insight, field, value)

    insight.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(insight)

    return PublisherInsightResponse.model_validate(insight)


@router.delete("/insights/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RATE_LIMITS["create_job"])
def delete_insight(
    request: Request,
    insight_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an insight."""
    insight = db.query(PublisherInsight).filter(
        PublisherInsight.id == insight_id,
        PublisherInsight.user_id == current_user.id
    ).first()

    if not insight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insight not found"
        )

    db.delete(insight)
    db.commit()

    return None


@router.post("/insights/generate/{publisher_domain}", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")  # AI-powered, rate limited
def generate_insights(
    request: Request,
    publisher_domain: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate AI-powered insights for a publisher.

    Analyzes publisher metrics and creates actionable insights.
    Rate limited to 20/hour due to computational cost.
    """
    # Get or update metrics first
    metrics = db.query(PublisherMetrics).filter(
        PublisherMetrics.user_id == current_user.id,
        PublisherMetrics.publisher_domain == publisher_domain
    ).first()

    if not metrics:
        # Create metrics if don't exist
        metrics = update_publisher_metrics(db, current_user.id, publisher_domain)

    if metrics.total_jobs < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Need at least 3 jobs for {publisher_domain} to generate insights. Current: {metrics.total_jobs}"
        )

    # Deactivate old automated insights for this publisher
    db.query(PublisherInsight).filter(
        PublisherInsight.user_id == current_user.id,
        PublisherInsight.publisher_domain == publisher_domain,
        PublisherInsight.is_automated == True
    ).update({"is_active": False})
    db.commit()

    # Generate new insights
    insights = generate_publisher_insights(db, current_user.id, publisher_domain, metrics)

    return {
        "message": f"Generated {len(insights)} insights for {publisher_domain}",
        "insights_created": len(insights),
        "publisher_domain": publisher_domain
    }
