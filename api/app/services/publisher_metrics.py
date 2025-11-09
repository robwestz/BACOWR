"""
Publisher Metrics Service.

Calculates and updates publisher performance metrics based on job data.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from collections import Counter
import logging

from ..models.database import PublisherMetrics, Job, PublisherInsight
from ..models.schemas import InsightType, InsightPriority

logger = logging.getLogger(__name__)


def calculate_recommendation_score(
    success_rate: float,
    avg_qc_score: Optional[float],
    avg_cost_per_job: Optional[float],
    total_jobs: int
) -> float:
    """
    Calculate publisher recommendation score (0-100).

    Factors:
    - Success rate (40%)
    - Quality score (30%)
    - Cost efficiency (20%)
    - Sample size reliability (10%)
    """
    score = 0.0

    # Success rate component (0-40 points)
    score += (success_rate / 100.0) * 40

    # Quality component (0-30 points)
    if avg_qc_score is not None:
        score += (avg_qc_score / 100.0) * 30
    else:
        # No quality data, neutral
        score += 15

    # Cost component (0-20 points)
    if avg_cost_per_job is not None:
        # Lower cost is better
        # Assuming $0.10 is excellent, $1.00 is poor
        cost_score = max(0, min(20, (1.0 - avg_cost_per_job) * 20))
        score += cost_score
    else:
        # No cost data, neutral
        score += 10

    # Sample size reliability (0-10 points)
    # More jobs = more reliable data
    if total_jobs >= 20:
        score += 10
    elif total_jobs >= 10:
        score += 7
    elif total_jobs >= 5:
        score += 5
    elif total_jobs >= 3:
        score += 3
    else:
        score += 1

    return round(score, 2)


def calculate_trend(current_value: float, previous_value: Optional[float]) -> str:
    """
    Calculate trend direction.

    Args:
        current_value: Current period value
        previous_value: Previous period value

    Returns:
        "improving", "stable", or "declining"
    """
    if previous_value is None:
        return "stable"

    change_pct = ((current_value - previous_value) / previous_value) * 100

    if abs(change_pct) < 5:
        return "stable"
    elif change_pct > 0:
        return "improving"
    else:
        return "declining"


def update_publisher_metrics(
    db: Session,
    user_id: str,
    publisher_domain: str
) -> PublisherMetrics:
    """
    Update or create publisher metrics for a user/publisher.

    Args:
        db: Database session
        user_id: User ID
        publisher_domain: Publisher domain

    Returns:
        Updated PublisherMetrics
    """
    # Get or create metrics record
    metrics = db.query(PublisherMetrics).filter(
        PublisherMetrics.user_id == user_id,
        PublisherMetrics.publisher_domain == publisher_domain
    ).first()

    if not metrics:
        metrics = PublisherMetrics(
            user_id=user_id,
            publisher_domain=publisher_domain
        )
        db.add(metrics)

    # Get all jobs for this user/publisher
    jobs = db.query(Job).filter(
        Job.user_id == user_id,
        Job.publisher_domain == publisher_domain
    ).all()

    if not jobs:
        db.commit()
        return metrics

    # Calculate statistics
    total_jobs = len(jobs)
    successful_jobs = len([j for j in jobs if j.status == "delivered"])
    failed_jobs = len([j for j in jobs if j.status in ["blocked", "aborted"]])
    pending_jobs = len([j for j in jobs if j.status in ["pending", "processing"]])

    success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0.0

    # Quality metrics (from successful jobs)
    successful_job_qc_scores = []
    successful_job_issue_counts = []

    for job in jobs:
        if job.status == "delivered" and job.qc_report:
            qc_score = job.qc_report.get("overall_score")
            if qc_score is not None:
                successful_job_qc_scores.append(qc_score)

            issue_count = len(job.qc_report.get("issues", []))
            successful_job_issue_counts.append(issue_count)

    avg_qc_score = sum(successful_job_qc_scores) / len(successful_job_qc_scores) if successful_job_qc_scores else None
    avg_issue_count = sum(successful_job_issue_counts) / len(successful_job_issue_counts) if successful_job_issue_counts else None

    # Cost metrics
    job_costs = [j.actual_cost for j in jobs if j.actual_cost is not None]
    total_cost_usd = sum(job_costs)
    avg_cost_per_job = total_cost_usd / len(job_costs) if job_costs else None

    # Performance metrics
    generation_times = [
        j.metrics.get("generation_time_seconds")
        for j in jobs
        if j.metrics and j.metrics.get("generation_time_seconds")
    ]
    avg_generation_time_seconds = sum(generation_times) / len(generation_times) if generation_times else None

    retry_counts = [j.retry_count for j in jobs]
    avg_retry_count = sum(retry_counts) / len(retry_counts) if retry_counts else None

    # Provider analytics
    providers = [j.llm_provider for j in jobs if j.llm_provider]
    strategies = [j.writing_strategy for j in jobs if j.writing_strategy]

    provider_counter = Counter(providers)
    most_used_provider = provider_counter.most_common(1)[0][0] if provider_counter else None
    provider_distribution = dict(provider_counter)

    strategy_counter = Counter(strategies)
    most_used_strategy = strategy_counter.most_common(1)[0][0] if strategy_counter else None

    # Timestamps
    job_dates = [j.created_at for j in jobs if j.created_at]
    first_job_at = min(job_dates) if job_dates else None
    last_job_at = max(job_dates) if job_dates else None

    # Calculate trends (compare to previous values)
    quality_trend = calculate_trend(avg_qc_score, metrics.avg_qc_score) if avg_qc_score else "stable"
    cost_trend = calculate_trend(avg_cost_per_job, metrics.avg_cost_per_job) if avg_cost_per_job else "stable"

    # Calculate recommendation score
    recommendation_score = calculate_recommendation_score(
        success_rate,
        avg_qc_score,
        avg_cost_per_job,
        total_jobs
    )

    # Generate recommendation reason
    recommendation_reason = generate_recommendation_reason(
        success_rate,
        avg_qc_score,
        avg_cost_per_job,
        total_jobs
    )

    # Update metrics
    metrics.total_jobs = total_jobs
    metrics.successful_jobs = successful_jobs
    metrics.failed_jobs = failed_jobs
    metrics.pending_jobs = pending_jobs
    metrics.success_rate = success_rate
    metrics.avg_qc_score = avg_qc_score
    metrics.avg_issue_count = avg_issue_count
    metrics.quality_trend = quality_trend
    metrics.total_cost_usd = total_cost_usd
    metrics.avg_cost_per_job = avg_cost_per_job
    metrics.cost_trend = cost_trend
    metrics.avg_generation_time_seconds = avg_generation_time_seconds
    metrics.avg_retry_count = avg_retry_count
    metrics.most_used_provider = most_used_provider
    metrics.most_used_strategy = most_used_strategy
    metrics.provider_distribution = provider_distribution
    metrics.recommendation_score = recommendation_score
    metrics.recommendation_reason = recommendation_reason
    metrics.first_job_at = first_job_at
    metrics.last_job_at = last_job_at
    metrics.last_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(metrics)

    logger.info(
        f"Updated metrics for publisher {publisher_domain} (user {user_id}): "
        f"{total_jobs} jobs, {success_rate:.1f}% success, score {recommendation_score:.1f}"
    )

    return metrics


def generate_recommendation_reason(
    success_rate: float,
    avg_qc_score: Optional[float],
    avg_cost_per_job: Optional[float],
    total_jobs: int
) -> str:
    """Generate human-readable recommendation reason."""

    reasons = []

    # Success rate
    if success_rate >= 90:
        reasons.append("excellent success rate")
    elif success_rate >= 75:
        reasons.append("good success rate")
    elif success_rate >= 50:
        reasons.append("moderate success rate")
    else:
        reasons.append("low success rate")

    # Quality
    if avg_qc_score is not None:
        if avg_qc_score >= 90:
            reasons.append("high quality content")
        elif avg_qc_score >= 75:
            reasons.append("good quality content")
        elif avg_qc_score >= 60:
            reasons.append("acceptable quality")
        else:
            reasons.append("quality issues")

    # Cost
    if avg_cost_per_job is not None:
        if avg_cost_per_job <= 0.20:
            reasons.append("very cost-effective")
        elif avg_cost_per_job <= 0.50:
            reasons.append("cost-effective")
        elif avg_cost_per_job <= 1.00:
            reasons.append("moderate cost")
        else:
            reasons.append("high cost")

    # Sample size
    if total_jobs < 5:
        reasons.append(f"limited data ({total_jobs} jobs)")
    elif total_jobs >= 20:
        reasons.append(f"reliable data ({total_jobs} jobs)")

    return ", ".join(reasons).capitalize()


def generate_publisher_insights(
    db: Session,
    user_id: str,
    publisher_domain: str,
    metrics: PublisherMetrics
) -> List[PublisherInsight]:
    """
    Generate automated insights for a publisher.

    Args:
        db: Database session
        user_id: User ID
        publisher_domain: Publisher domain
        metrics: Publisher metrics

    Returns:
        List of generated insights
    """
    insights = []

    # Insight 1: Success rate warning
    if metrics.total_jobs >= 5 and metrics.success_rate < 50:
        insight = PublisherInsight(
            user_id=user_id,
            publisher_domain=publisher_domain,
            insight_type=InsightType.WARNING.value,
            priority=InsightPriority.HIGH.value,
            title=f"Low Success Rate for {publisher_domain}",
            description=f"Only {metrics.success_rate:.1f}% of jobs succeeded for this publisher. "
                       f"Out of {metrics.total_jobs} jobs, {metrics.failed_jobs} failed. "
                       f"Consider reviewing job configurations or trying different approaches.",
            action_items=[
                "Review failed job error messages",
                "Try different writing strategies",
                "Verify publisher domain requirements",
                "Consider using a different LLM provider"
            ],
            confidence_score=95.0,
            sample_size=metrics.total_jobs,
            evidence={
                "success_rate": metrics.success_rate,
                "total_jobs": metrics.total_jobs,
                "failed_jobs": metrics.failed_jobs
            },
            tags=["performance", "warning"]
        )
        db.add(insight)
        insights.append(insight)

    # Insight 2: High quality recommendation
    if metrics.total_jobs >= 5 and metrics.avg_qc_score and metrics.avg_qc_score >= 85:
        insight = PublisherInsight(
            user_id=user_id,
            publisher_domain=publisher_domain,
            insight_type=InsightType.RECOMMENDATION.value,
            priority=InsightPriority.HIGH.value,
            title=f"High-Quality Publisher: {publisher_domain}",
            description=f"This publisher consistently produces high-quality content "
                       f"with an average QC score of {metrics.avg_qc_score:.1f}/100. "
                       f"Recommended for important backlink opportunities.",
            action_items=[
                "Prioritize this publisher for critical backlinks",
                f"Current configuration ({metrics.most_used_strategy}) works well",
                "Consider creating a template for this publisher"
            ],
            confidence_score=90.0,
            sample_size=metrics.total_jobs,
            evidence={
                "avg_qc_score": metrics.avg_qc_score,
                "success_rate": metrics.success_rate,
                "total_jobs": metrics.total_jobs
            },
            tags=["quality", "recommendation"]
        )
        db.add(insight)
        insights.append(insight)

    # Insight 3: Cost optimization opportunity
    if metrics.total_jobs >= 5 and metrics.avg_cost_per_job and metrics.avg_cost_per_job > 0.75:
        insight = PublisherInsight(
            user_id=user_id,
            publisher_domain=publisher_domain,
            insight_type=InsightType.OPTIMIZATION.value,
            priority=InsightPriority.MEDIUM.value,
            title=f"High Cost for {publisher_domain}",
            description=f"Average cost per job is ${metrics.avg_cost_per_job:.2f}, "
                       f"which is above typical rates. Consider cost optimization strategies.",
            action_items=[
                "Try different LLM providers (cost comparison)",
                "Use single-shot strategy instead of multi-stage",
                "Review if all features are necessary",
                "Compare with similar publishers"
            ],
            confidence_score=85.0,
            sample_size=metrics.total_jobs,
            evidence={
                "avg_cost_per_job": metrics.avg_cost_per_job,
                "total_cost_usd": metrics.total_cost_usd,
                "most_used_provider": metrics.most_used_provider
            },
            tags=["cost", "optimization"]
        )
        db.add(insight)
        insights.append(insight)

    # Insight 4: Success pattern
    if metrics.total_jobs >= 10 and metrics.success_rate >= 85:
        insight = PublisherInsight(
            user_id=user_id,
            publisher_domain=publisher_domain,
            insight_type=InsightType.SUCCESS_PATTERN.value,
            priority=InsightPriority.MEDIUM.value,
            title=f"Reliable Publisher: {publisher_domain}",
            description=f"Strong track record with {metrics.success_rate:.1f}% success rate "
                       f"across {metrics.total_jobs} jobs. "
                       f"Most successful with {metrics.most_used_provider} using {metrics.most_used_strategy} strategy.",
            action_items=[
                "Continue using current configuration",
                "Scale up jobs for this publisher",
                "Document what works for future reference"
            ],
            confidence_score=92.0,
            sample_size=metrics.total_jobs,
            evidence={
                "success_rate": metrics.success_rate,
                "most_used_provider": metrics.most_used_provider,
                "most_used_strategy": metrics.most_used_strategy
            },
            tags=["success", "pattern"]
        )
        db.add(insight)
        insights.append(insight)

    # Insight 5: Performance trend
    if metrics.quality_trend == "declining" and metrics.total_jobs >= 10:
        insight = PublisherInsight(
            user_id=user_id,
            publisher_domain=publisher_domain,
            insight_type=InsightType.WARNING.value,
            priority=InsightPriority.MEDIUM.value,
            title=f"Declining Quality for {publisher_domain}",
            description=f"Quality scores have been declining recently. "
                       f"Current average: {metrics.avg_qc_score:.1f}/100. "
                       f"Review recent changes or publisher guidelines updates.",
            action_items=[
                "Compare recent jobs to earlier successful ones",
                "Check if publisher changed their requirements",
                "Review any configuration changes",
                "Consider reverting to previous successful settings"
            ],
            confidence_score=80.0,
            sample_size=metrics.total_jobs,
            evidence={
                "quality_trend": metrics.quality_trend,
                "avg_qc_score": metrics.avg_qc_score
            },
            tags=["trend", "warning"]
        )
        db.add(insight)
        insights.append(insight)

    db.commit()

    logger.info(f"Generated {len(insights)} insights for {publisher_domain}")

    return insights


def update_all_publisher_metrics(db: Session, user_id: str) -> int:
    """
    Update metrics for all publishers for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Number of publishers updated
    """
    # Get all unique publisher domains for this user
    publishers = db.query(Job.publisher_domain).filter(
        Job.user_id == user_id
    ).distinct().all()

    count = 0
    for (publisher_domain,) in publishers:
        try:
            update_publisher_metrics(db, user_id, publisher_domain)
            count += 1
        except Exception as e:
            logger.error(f"Error updating metrics for {publisher_domain}: {e}")

    logger.info(f"Updated metrics for {count} publishers for user {user_id}")

    return count
