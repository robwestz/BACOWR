"""
Job routes for creating and managing content generation jobs.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models.database import User, Job, JobResult
from ..models.schemas import (
    JobCreate, JobResponse, JobDetailResponse,
    PaginationParams, PaginatedResponse, JobStatus
)
from ..auth import get_current_user
from ..core.bacowr_wrapper import bacowr

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def run_job_background(
    job_id: str,
    job_create: JobCreate,
    db: Session
):
    """Background task to run BACOWR job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return

    try:
        # Update status to processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()

        # Run BACOWR
        result = await bacowr.run_job(
            publisher_domain=job_create.publisher_domain,
            target_url=job_create.target_url,
            anchor_text=job_create.anchor_text,
            llm_provider=job_create.llm_provider if job_create.llm_provider != "auto" else None,
            writing_strategy=job_create.writing_strategy,
            use_ahrefs=job_create.use_ahrefs,
            country=job_create.country,
            enable_llm_profiling=job_create.enable_llm_profiling
        )

        # Update job with results
        job.status = result['status']
        job.article_text = result.get('article')
        job.job_package = result.get('job_package')
        job.qc_report = result.get('qc_report')
        job.execution_log = result.get('execution_log')
        job.metrics = result.get('metrics')
        job.completed_at = datetime.utcnow()

        # Calculate actual cost (estimate for now)
        if job.metrics and 'generation' in job.metrics:
            provider = job.metrics['generation'].get('provider', 'anthropic')
            strategy = job.metrics['generation'].get('strategy', 'multi_stage')
            cost_estimate = bacowr.estimate_cost(provider, strategy, 1)
            job.actual_cost = cost_estimate['estimated_cost_per_job']

        db.commit()

        # Create analytics record
        if result.get('qc_report'):
            qc_report = result['qc_report']
            job_result = JobResult(
                job_id=job.id,
                user_id=job.user_id,
                qc_score=0,  # Calculate from qc_report
                qc_status=qc_report.get('status'),
                issue_count=len(qc_report.get('issues', [])),
                generation_time_seconds=job.metrics.get('generation', {}).get('duration_seconds') if job.metrics else None,
                total_time_seconds=(job.completed_at - job.started_at).total_seconds() if job.completed_at and job.started_at else None,
                provider_used=job.metrics.get('generation', {}).get('provider') if job.metrics else None,
                model_used=job.metrics.get('generation', {}).get('model') if job.metrics else None,
                strategy_used=job.writing_strategy,
                cost_actual=job.actual_cost,
                delivered=job.status == JobStatus.DELIVERED
            )
            db.add(job_result)
            db.commit()

    except Exception as e:
        job.status = JobStatus.ABORTED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_create: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new content generation job.

    The job will be processed asynchronously in the background.
    Use GET /jobs/{job_id} to check status and retrieve results.
    """
    # Estimate cost
    provider = job_create.llm_provider if job_create.llm_provider != "auto" else "anthropic"
    cost_estimate = bacowr.estimate_cost(provider, job_create.writing_strategy, 1)

    # Create job record
    job = Job(
        user_id=current_user.id,
        publisher_domain=job_create.publisher_domain,
        target_url=job_create.target_url,
        anchor_text=job_create.anchor_text,
        llm_provider=job_create.llm_provider,
        writing_strategy=job_create.writing_strategy,
        country=job_create.country,
        use_ahrefs=job_create.use_ahrefs,
        enable_llm_profiling=job_create.enable_llm_profiling,
        status=JobStatus.PENDING,
        estimated_cost=cost_estimate['estimated_cost_per_job']
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Schedule background task
    background_tasks.add_task(run_job_background, job.id, job_create, db)

    return job


@router.get("", response_model=PaginatedResponse)
def list_jobs(
    page: int = 1,
    page_size: int = 20,
    status: Optional[JobStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List jobs for current user with pagination.

    Optional filtering by status.
    """
    query = db.query(Job).filter(Job.user_id == current_user.id)

    if status:
        query = query.filter(Job.status == status)

    # Count total
    total = query.count()

    # Paginate
    jobs = query.order_by(Job.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()

    return PaginatedResponse.create(
        items=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed job information.

    Includes article text, QC report, execution log, and metrics.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return JobDetailResponse.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a job.

    Only pending or completed jobs can be deleted.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if job.status == JobStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete job that is currently processing"
        )

    db.delete(job)
    db.commit()

    return None


@router.get("/{job_id}/article")
def get_job_article(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get job article text.

    Returns plain text Markdown article.
    """
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    if not job.article_text:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not yet generated"
        )

    return {
        "job_id": job.id,
        "article": job.article_text,
        "created_at": job.completed_at
    }
