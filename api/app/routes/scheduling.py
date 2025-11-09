"""
Job scheduling routes.

Schedule jobs to run in the future with support for:
- One-time scheduled jobs
- Recurring jobs (daily, weekly, monthly)
- Template-based scheduling
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from dateutil import rrule

from ..database import get_db
from ..models.database import User, ScheduledJob, Campaign, JobTemplate
from ..models.schemas import (
    ScheduledJobCreate, ScheduledJobUpdate, ScheduledJobResponse,
    ScheduleType, ScheduledJobStatus
)
from ..auth import get_current_user
from ..rate_limit import limiter, RATE_LIMITS

router = APIRouter(prefix="/schedule", tags=["scheduling"])


def calculate_next_run(
    schedule_type: str,
    scheduled_at: datetime,
    recurrence_pattern: Optional[str],
    last_run: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Calculate next run time based on schedule configuration.

    Args:
        schedule_type: once, daily, weekly, monthly, cron
        scheduled_at: Initial scheduled time
        recurrence_pattern: Pattern like "daily", "weekly:monday", "monthly:1"
        last_run: Last execution time

    Returns:
        Next run datetime or None if no more runs
    """
    base_time = last_run if last_run else scheduled_at
    now = datetime.utcnow()

    if schedule_type == ScheduleType.ONCE:
        # One-time job
        if last_run:
            return None  # Already ran
        return scheduled_at if scheduled_at > now else None

    elif schedule_type == ScheduleType.DAILY:
        # Daily at same time
        next_run = base_time + timedelta(days=1)
        while next_run <= now:
            next_run += timedelta(days=1)
        return next_run

    elif schedule_type == ScheduleType.WEEKLY:
        # Weekly on specific day
        # Pattern: "weekly:monday" or just "weekly" (same day as scheduled_at)
        if recurrence_pattern and ":" in recurrence_pattern:
            weekday_name = recurrence_pattern.split(":")[1].lower()
            weekdays = {
                "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                "friday": 4, "saturday": 5, "sunday": 6
            }
            target_weekday = weekdays.get(weekday_name, scheduled_at.weekday())
        else:
            target_weekday = scheduled_at.weekday()

        next_run = base_time + timedelta(days=1)
        while next_run <= now or next_run.weekday() != target_weekday:
            next_run += timedelta(days=1)
        return next_run

    elif schedule_type == ScheduleType.MONTHLY:
        # Monthly on specific day
        # Pattern: "monthly:1" (1st of month) or just "monthly" (same day as scheduled_at)
        if recurrence_pattern and ":" in recurrence_pattern:
            target_day = int(recurrence_pattern.split(":")[1])
        else:
            target_day = scheduled_at.day

        # Try next month
        if base_time.month == 12:
            next_month = base_time.replace(year=base_time.year + 1, month=1, day=1)
        else:
            next_month = base_time.replace(month=base_time.month + 1, day=1)

        # Handle day overflow (e.g., Feb 30 -> Feb 28)
        try:
            next_run = next_month.replace(day=target_day)
        except ValueError:
            # Day doesn't exist in month, use last day
            import calendar
            last_day = calendar.monthrange(next_month.year, next_month.month)[1]
            next_run = next_month.replace(day=last_day)

        # Ensure it's in the future
        while next_run <= now:
            if next_run.month == 12:
                next_run = next_run.replace(year=next_run.year + 1, month=1)
            else:
                next_run = next_run.replace(month=next_run.month + 1)

        return next_run

    # For CRON, would need cron parser (not implemented in basic version)
    return None


@router.post("", response_model=ScheduledJobResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create_job"])
def create_scheduled_job(
    request: Request,
    schedule_data: ScheduledJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new scheduled job.

    Supports:
    - One-time jobs (run once at specific time)
    - Daily jobs (run every day at same time)
    - Weekly jobs (run specific weekday)
    - Monthly jobs (run specific day of month)

    Examples:
    - Once: schedule_type="once", scheduled_at="2025-12-01T10:00:00Z"
    - Daily: schedule_type="daily", scheduled_at="2025-11-10T09:00:00Z"
    - Weekly: schedule_type="weekly", recurrence_pattern="weekly:monday"
    - Monthly: schedule_type="monthly", recurrence_pattern="monthly:1" (1st of month)
    """
    # Validate campaign_id if provided
    if schedule_data.campaign_id:
        campaign = db.query(Campaign).filter(
            Campaign.id == schedule_data.campaign_id,
            Campaign.user_id == current_user.id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

    # Validate template_id if provided
    if schedule_data.template_id:
        template = db.query(JobTemplate).filter(
            JobTemplate.id == schedule_data.template_id,
            JobTemplate.user_id == current_user.id
        ).first()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

    # Validate scheduled_at is in the future
    if schedule_data.scheduled_at <= datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="scheduled_at must be in the future"
        )

    # Calculate next run time
    next_run = calculate_next_run(
        schedule_data.schedule_type,
        schedule_data.scheduled_at,
        schedule_data.recurrence_pattern
    )

    scheduled_job = ScheduledJob(
        user_id=current_user.id,
        campaign_id=schedule_data.campaign_id,
        template_id=schedule_data.template_id,
        name=schedule_data.name,
        description=schedule_data.description,
        schedule_type=schedule_data.schedule_type,
        scheduled_at=schedule_data.scheduled_at,
        recurrence_pattern=schedule_data.recurrence_pattern,
        recurrence_end_date=schedule_data.recurrence_end_date,
        timezone=schedule_data.timezone or "UTC",
        max_runs=schedule_data.max_runs,
        job_config=schedule_data.job_config,
        status=ScheduledJobStatus.ACTIVE,
        next_run_at=next_run,
        run_count=0,
        error_count=0
    )

    db.add(scheduled_job)
    db.commit()
    db.refresh(scheduled_job)

    return ScheduledJobResponse.model_validate(scheduled_job)


@router.get("", response_model=List[ScheduledJobResponse])
@limiter.limit(RATE_LIMITS["list_jobs"])
def list_scheduled_jobs(
    request: Request,
    campaign_id: Optional[str] = None,
    status_filter: Optional[str] = None,
    upcoming_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all scheduled jobs for the current user.

    Optional filters:
    - campaign_id: Filter by campaign
    - status_filter: Filter by status (active, paused, completed, expired, error)
    - upcoming_only: Show only jobs with upcoming runs
    """
    query = db.query(ScheduledJob).filter(ScheduledJob.user_id == current_user.id)

    if campaign_id:
        query = query.filter(ScheduledJob.campaign_id == campaign_id)

    if status_filter:
        query = query.filter(ScheduledJob.status == status_filter)

    if upcoming_only:
        query = query.filter(
            ScheduledJob.status == ScheduledJobStatus.ACTIVE,
            ScheduledJob.next_run_at != None
        )

    scheduled_jobs = query.order_by(ScheduledJob.next_run_at.asc().nulls_last()).all()

    return [ScheduledJobResponse.model_validate(job) for job in scheduled_jobs]


@router.get("/upcoming")
@limiter.limit(RATE_LIMITS["list_jobs"])
def get_upcoming_runs(
    request: Request,
    hours: int = 24,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all scheduled jobs that will run in the next N hours.

    Default: 24 hours
    """
    cutoff_time = datetime.utcnow() + timedelta(hours=hours)

    upcoming = db.query(ScheduledJob).filter(
        ScheduledJob.user_id == current_user.id,
        ScheduledJob.status == ScheduledJobStatus.ACTIVE,
        ScheduledJob.next_run_at != None,
        ScheduledJob.next_run_at <= cutoff_time
    ).order_by(ScheduledJob.next_run_at).all()

    return {
        "time_window_hours": hours,
        "cutoff_time": cutoff_time.isoformat(),
        "upcoming_count": len(upcoming),
        "jobs": [ScheduledJobResponse.model_validate(job) for job in upcoming]
    }


@router.get("/{scheduled_job_id}", response_model=ScheduledJobResponse)
@limiter.limit(RATE_LIMITS["get_job"])
def get_scheduled_job(
    request: Request,
    scheduled_job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific scheduled job by ID.
    """
    scheduled_job = db.query(ScheduledJob).filter(
        ScheduledJob.id == scheduled_job_id,
        ScheduledJob.user_id == current_user.id
    ).first()

    if not scheduled_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled job not found"
        )

    return ScheduledJobResponse.model_validate(scheduled_job)


@router.put("/{scheduled_job_id}", response_model=ScheduledJobResponse)
@limiter.limit(RATE_LIMITS["create_job"])
def update_scheduled_job(
    request: Request,
    scheduled_job_id: str,
    schedule_data: ScheduledJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a scheduled job.
    """
    scheduled_job = db.query(ScheduledJob).filter(
        ScheduledJob.id == scheduled_job_id,
        ScheduledJob.user_id == current_user.id
    ).first()

    if not scheduled_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled job not found"
        )

    # Update fields
    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scheduled_job, field, value)

    # Recalculate next_run if schedule changed
    if "scheduled_at" in update_data or "recurrence_pattern" in update_data:
        next_run = calculate_next_run(
            scheduled_job.schedule_type,
            scheduled_job.scheduled_at,
            scheduled_job.recurrence_pattern,
            scheduled_job.last_run_at
        )
        scheduled_job.next_run_at = next_run

    scheduled_job.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(scheduled_job)

    return ScheduledJobResponse.model_validate(scheduled_job)


@router.post("/{scheduled_job_id}/pause", response_model=ScheduledJobResponse)
@limiter.limit(RATE_LIMITS["create_job"])
def pause_scheduled_job(
    request: Request,
    scheduled_job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Pause a scheduled job.

    Paused jobs will not run until resumed.
    """
    scheduled_job = db.query(ScheduledJob).filter(
        ScheduledJob.id == scheduled_job_id,
        ScheduledJob.user_id == current_user.id
    ).first()

    if not scheduled_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled job not found"
        )

    scheduled_job.status = ScheduledJobStatus.PAUSED
    scheduled_job.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(scheduled_job)

    return ScheduledJobResponse.model_validate(scheduled_job)


@router.post("/{scheduled_job_id}/resume", response_model=ScheduledJobResponse)
@limiter.limit(RATE_LIMITS["create_job"])
def resume_scheduled_job(
    request: Request,
    scheduled_job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resume a paused scheduled job.
    """
    scheduled_job = db.query(ScheduledJob).filter(
        ScheduledJob.id == scheduled_job_id,
        ScheduledJob.user_id == current_user.id
    ).first()

    if not scheduled_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled job not found"
        )

    if scheduled_job.status != ScheduledJobStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only resume paused jobs"
        )

    scheduled_job.status = ScheduledJobStatus.ACTIVE
    scheduled_job.updated_at = datetime.utcnow()

    # Recalculate next run
    next_run = calculate_next_run(
        scheduled_job.schedule_type,
        scheduled_job.scheduled_at,
        scheduled_job.recurrence_pattern,
        scheduled_job.last_run_at
    )
    scheduled_job.next_run_at = next_run

    db.commit()
    db.refresh(scheduled_job)

    return ScheduledJobResponse.model_validate(scheduled_job)


@router.delete("/{scheduled_job_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RATE_LIMITS["create_job"])
def delete_scheduled_job(
    request: Request,
    scheduled_job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a scheduled job.
    """
    scheduled_job = db.query(ScheduledJob).filter(
        ScheduledJob.id == scheduled_job_id,
        ScheduledJob.user_id == current_user.id
    ).first()

    if not scheduled_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scheduled job not found"
        )

    db.delete(scheduled_job)
    db.commit()

    return None
