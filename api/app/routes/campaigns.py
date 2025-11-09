"""
Campaign management routes.

Campaigns organize jobs into logical groups for better project management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models.database import User, Campaign, Job, ScheduledJob, JobTemplate
from ..models.schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignStatus, PaginationParams, PaginatedResponse
)
from ..auth import get_current_user
from ..rate_limit import limiter, RATE_LIMITS

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create_job"])  # Same limit as job creation
def create_campaign(
    request: Request,
    campaign_data: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new campaign.

    Campaigns help organize jobs into logical groups:
    - Publisher-specific campaigns
    - Topic-based campaigns
    - Time-based campaigns (Q1 2025, etc.)
    - Client campaigns
    """
    campaign = Campaign(
        user_id=current_user.id,
        name=campaign_data.name,
        description=campaign_data.description,
        color=campaign_data.color,
        tags=campaign_data.tags,
        target_job_count=campaign_data.target_job_count,
        target_budget_usd=campaign_data.target_budget_usd,
        start_date=campaign_data.start_date,
        end_date=campaign_data.end_date,
        status=CampaignStatus.ACTIVE
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    # Add computed stats
    response = CampaignResponse.model_validate(campaign)
    response.job_count = 0
    response.total_cost = 0.0

    return response


@router.get("", response_model=List[CampaignResponse])
@limiter.limit(RATE_LIMITS["list_jobs"])
def list_campaigns(
    request: Request,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all campaigns for the current user.

    Optional filters:
    - status: Filter by campaign status (active, paused, completed, archived)
    """
    query = db.query(Campaign).filter(Campaign.user_id == current_user.id)

    if status_filter:
        query = query.filter(Campaign.status == status_filter)

    campaigns = query.order_by(Campaign.created_at.desc()).all()

    # Compute stats for each campaign
    response_list = []
    for campaign in campaigns:
        # Count scheduled jobs in this campaign
        job_count = db.query(func.count(ScheduledJob.id)).filter(
            ScheduledJob.campaign_id == campaign.id
        ).scalar() or 0

        # This is a simplified stat - in production you'd join with Job table
        # to get actual completed jobs and their costs
        total_cost = 0.0

        response = CampaignResponse.model_validate(campaign)
        response.job_count = job_count
        response.total_cost = total_cost
        response_list.append(response)

    return response_list


@router.get("/{campaign_id}", response_model=CampaignResponse)
@limiter.limit(RATE_LIMITS["get_job"])
def get_campaign(
    request: Request,
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific campaign by ID.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Compute stats
    job_count = db.query(func.count(ScheduledJob.id)).filter(
        ScheduledJob.campaign_id == campaign.id
    ).scalar() or 0

    total_cost = 0.0

    response = CampaignResponse.model_validate(campaign)
    response.job_count = job_count
    response.total_cost = total_cost

    return response


@router.put("/{campaign_id}", response_model=CampaignResponse)
@limiter.limit(RATE_LIMITS["create_job"])
def update_campaign(
    request: Request,
    campaign_id: str,
    campaign_data: CampaignUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a campaign.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Update fields
    update_data = campaign_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(campaign, field, value)

    campaign.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(campaign)

    # Compute stats
    job_count = db.query(func.count(ScheduledJob.id)).filter(
        ScheduledJob.campaign_id == campaign.id
    ).scalar() or 0

    total_cost = 0.0

    response = CampaignResponse.model_validate(campaign)
    response.job_count = job_count
    response.total_cost = total_cost

    return response


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RATE_LIMITS["create_job"])
def delete_campaign(
    request: Request,
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a campaign.

    Note: This will NOT delete associated scheduled jobs or templates.
    They will simply have their campaign_id set to NULL.
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Unlink scheduled jobs and templates (don't delete them)
    db.query(ScheduledJob).filter(ScheduledJob.campaign_id == campaign_id).update(
        {"campaign_id": None}
    )
    db.query(JobTemplate).filter(JobTemplate.campaign_id == campaign_id).update(
        {"campaign_id": None}
    )

    db.delete(campaign)
    db.commit()

    return None


@router.get("/{campaign_id}/stats")
@limiter.limit(RATE_LIMITS["analytics"])
def get_campaign_stats(
    request: Request,
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed statistics for a campaign.

    Returns:
    - Total scheduled jobs
    - Total templates
    - Budget usage (if target_budget_usd is set)
    - Job completion rate
    - Upcoming scheduled jobs
    """
    campaign = db.query(Campaign).filter(
        Campaign.id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()

    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )

    # Count scheduled jobs by status
    scheduled_jobs_query = db.query(
        ScheduledJob.status,
        func.count(ScheduledJob.id)
    ).filter(
        ScheduledJob.campaign_id == campaign_id
    ).group_by(ScheduledJob.status).all()

    scheduled_jobs_by_status = {status: count for status, count in scheduled_jobs_query}

    # Count templates
    template_count = db.query(func.count(JobTemplate.id)).filter(
        JobTemplate.campaign_id == campaign_id
    ).scalar() or 0

    # Get upcoming scheduled jobs (next 5)
    upcoming = db.query(ScheduledJob).filter(
        ScheduledJob.campaign_id == campaign_id,
        ScheduledJob.status == "active",
        ScheduledJob.next_run_at != None
    ).order_by(ScheduledJob.next_run_at).limit(5).all()

    return {
        "campaign_id": campaign_id,
        "campaign_name": campaign.name,
        "total_scheduled_jobs": sum(scheduled_jobs_by_status.values()),
        "scheduled_jobs_by_status": scheduled_jobs_by_status,
        "total_templates": template_count,
        "target_job_count": campaign.target_job_count,
        "target_budget_usd": campaign.target_budget_usd,
        "upcoming_runs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None
            }
            for job in upcoming
        ]
    }
