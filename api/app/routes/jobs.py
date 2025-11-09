"""
Job routes for creating and managing content generation jobs.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

from ..database import get_db
from ..models.database import User, Job, JobResult
from ..models.schemas import (
    JobCreate, JobResponse, JobDetailResponse,
    PaginationParams, PaginatedResponse, JobStatus
)
from ..auth import get_current_user
from ..core.bacowr_wrapper import bacowr
from ..websocket import ws_manager
from ..rate_limit import limiter, RATE_LIMITS
from ..notifications.email import email_service
from ..notifications.webhook import webhook_service

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

        # Emit WebSocket event: Job started
        await ws_manager.broadcast_job_update(
            job_id=job_id,
            status='PROCESSING',
            progress=10,
            message='Job started - Profiling publisher and target'
        )

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

        # Emit WebSocket event: Content generated
        await ws_manager.broadcast_job_update(
            job_id=job_id,
            status='PROCESSING',
            progress=80,
            message='Content generated - Running quality checks'
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

        # Emit WebSocket event: Job completed
        if job.status == JobStatus.DELIVERED:
            await ws_manager.broadcast_job_completed(
                job_id=job_id,
                message=f'Article successfully generated and delivered'
            )
        else:
            await ws_manager.broadcast_job_update(
                job_id=job_id,
                status=job.status,
                progress=100,
                message=f'Job completed with status: {job.status}'
            )

        # Send notifications
        user = db.query(User).filter(User.id == job.user_id).first()
        if user:
            # Send email notification
            if user.enable_email_notifications and user.notification_email:
                try:
                    await email_service.send_job_completed(
                        to_email=user.notification_email,
                        job_id=job.id,
                        publisher_domain=job.publisher_domain,
                        target_url=job.target_url,
                        status=job.status,
                        completed_at=job.completed_at.isoformat() if job.completed_at else None,
                        actual_cost=job.actual_cost
                    )
                except Exception as e:
                    logger.error(f"Failed to send email notification: {str(e)}")

            # Send webhook notification
            if user.enable_webhook_notifications and user.webhook_url:
                try:
                    await webhook_service.send_job_completed(
                        webhook_url=user.webhook_url,
                        job_id=job.id,
                        status=job.status,
                        publisher_domain=job.publisher_domain,
                        target_url=job.target_url,
                        completed_at=job.completed_at.isoformat() if job.completed_at else None,
                        actual_cost=job.actual_cost
                    )
                except Exception as e:
                    logger.error(f"Failed to send webhook notification: {str(e)}")

    except Exception as e:
        job.status = JobStatus.ABORTED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()

        # Emit WebSocket event: Job error
        await ws_manager.broadcast_job_error(
            job_id=job_id,
            error_message=str(e)
        )

        # Send error notifications
        user = db.query(User).filter(User.id == job.user_id).first()
        if user:
            # Send email notification
            if user.enable_email_notifications and user.notification_email:
                try:
                    await email_service.send_job_error(
                        to_email=user.notification_email,
                        job_id=job.id,
                        publisher_domain=job.publisher_domain,
                        error_message=str(e)
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send email notification: {str(email_error)}")

            # Send webhook notification
            if user.enable_webhook_notifications and user.webhook_url:
                try:
                    await webhook_service.send_job_error(
                        webhook_url=user.webhook_url,
                        job_id=job.id,
                        publisher_domain=job.publisher_domain,
                        error_message=str(e)
                    )
                except Exception as webhook_error:
                    logger.error(f"Failed to send webhook notification: {str(webhook_error)}")


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create_job"])
async def create_job(
    request: Request,
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

    # Emit WebSocket event: Job created
    await ws_manager.broadcast_job_update(
        job_id=job.id,
        status='PENDING',
        progress=0,
        message='Job created and queued for processing'
    )

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


async def run_orchestrated_job_background(
    job_id: str,
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    user_id: str,
    country: str,
    language: str,
    writing_strategy: str,
    llm_provider: str,
    db: Session
):
    """Background task to run orchestrated BACOWR job using new pipeline."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return

    try:
        # Update status to processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()

        # Emit WebSocket event: Job started
        await ws_manager.broadcast_job_update(
            job_id=job_id,
            status='PROCESSING',
            progress=10,
            message='Job started - Profiling target and publisher'
        )

        # Import orchestrator
        from ..services.job_orchestrator import BacklinkJobOrchestrator

        # Initialize orchestrator
        orchestrator = BacklinkJobOrchestrator(
            provider=llm_provider,
            serp_mode="api"  # Use real SERP API
        )

        # Progress callback for WebSocket updates
        async def progress_callback(step: str, progress: int, message: str):
            await ws_manager.broadcast_job_update(
                job_id=job_id,
                status='PROCESSING',
                progress=progress,
                message=message
            )

        # Update progress - Profiling
        await progress_callback("profiling", 15, "Profiling target and publisher...")

        # Execute orchestrator
        result = await orchestrator.execute(
            publisher_domain=publisher_domain,
            target_url=target_url,
            anchor_text=anchor_text,
            user_id=user_id,
            country=country,
            language=language,
            writing_strategy=writing_strategy
        )

        # Update progress - Content generation
        await progress_callback("generation", 60, "Generating content with LLM...")

        # Update progress - QC validation
        await progress_callback("qc", 85, "Running quality validation...")

        # Determine job status from QC
        qc_status = result.get("qc_report", {}).get("status", "BLOCKED")
        if qc_status == "PASS":
            job.status = JobStatus.DELIVERED
        elif qc_status == "WARNING":
            job.status = JobStatus.DELIVERED  # Still deliver with warnings
        else:
            job.status = JobStatus.BLOCKED

        # Update job with results
        job.article_text = result.get('article_content', '')
        job.job_package = result.get('job_package')
        job.qc_report = result.get('qc_report')
        job.execution_log = result.get('execution_log')
        job.metrics = {
            "profiling": result.get('profiling_metrics', {}),
            "generation": {
                "provider": llm_provider,
                "strategy": writing_strategy,
                "duration_seconds": result.get('generation_time_seconds', 0)
            },
            "qc": result.get('qc_metrics', {})
        }
        job.completed_at = datetime.utcnow()

        # Calculate actual cost (simplified)
        cost_estimate = bacowr.estimate_cost(llm_provider, writing_strategy, 1)
        job.actual_cost = cost_estimate['estimated_cost_per_job']

        db.commit()

        # Create analytics record
        if result.get('qc_report'):
            qc_report = result['qc_report']
            job_result = JobResult(
                job_id=job.id,
                user_id=job.user_id,
                qc_score=qc_report.get('overall_score', 0),
                qc_status=qc_report.get('status'),
                issue_count=len(qc_report.get('issues', [])),
                generation_time_seconds=result.get('generation_time_seconds', 0),
                total_time_seconds=(job.completed_at - job.started_at).total_seconds() if job.completed_at and job.started_at else None,
                provider_used=llm_provider,
                model_used=result.get('model_used', 'claude-3-5-sonnet-20241022'),
                strategy_used=writing_strategy,
                cost_actual=job.actual_cost,
                delivered=job.status == JobStatus.DELIVERED
            )
            db.add(job_result)
            db.commit()

        # Emit WebSocket event: Job completed
        if job.status == JobStatus.DELIVERED:
            await ws_manager.broadcast_job_completed(
                job_id=job_id,
                message=f'Article successfully generated and delivered (QC: {qc_status})'
            )
        else:
            await ws_manager.broadcast_job_update(
                job_id=job_id,
                status=job.status,
                progress=100,
                message=f'Job completed with status: {job.status}'
            )

        # Send notifications
        user = db.query(User).filter(User.id == job.user_id).first()
        if user:
            # Send email notification
            if user.enable_email_notifications and user.notification_email:
                try:
                    await email_service.send_job_completed(
                        to_email=user.notification_email,
                        job_id=job.id,
                        publisher_domain=job.publisher_domain,
                        target_url=job.target_url,
                        status=job.status,
                        completed_at=job.completed_at.isoformat() if job.completed_at else None,
                        actual_cost=job.actual_cost
                    )
                except Exception as e:
                    logger.error(f"Failed to send email notification: {str(e)}")

            # Send webhook notification
            if user.enable_webhook_notifications and user.webhook_url:
                try:
                    await webhook_service.send_job_completed(
                        webhook_url=user.webhook_url,
                        job_id=job.id,
                        status=job.status,
                        publisher_domain=job.publisher_domain,
                        target_url=job.target_url,
                        completed_at=job.completed_at.isoformat() if job.completed_at else None,
                        actual_cost=job.actual_cost
                    )
                except Exception as e:
                    logger.error(f"Failed to send webhook notification: {str(e)}")

    except Exception as e:
        logger.error(f"Orchestrated job failed: {str(e)}", exc_info=True)
        job.status = JobStatus.ABORTED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.commit()

        # Emit WebSocket event: Job error
        await ws_manager.broadcast_job_error(
            job_id=job_id,
            error_message=str(e)
        )

        # Send error notifications
        user = db.query(User).filter(User.id == job.user_id).first()
        if user:
            if user.enable_email_notifications and user.notification_email:
                try:
                    await email_service.send_job_error(
                        to_email=user.notification_email,
                        job_id=job.id,
                        publisher_domain=job.publisher_domain,
                        error_message=str(e)
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send email notification: {str(email_error)}")

            if user.enable_webhook_notifications and user.webhook_url:
                try:
                    await webhook_service.send_job_error(
                        webhook_url=user.webhook_url,
                        job_id=job.id,
                        publisher_domain=job.publisher_domain,
                        error_message=str(e)
                    )
                except Exception as webhook_error:
                    logger.error(f"Failed to send webhook notification: {str(webhook_error)}")


@router.post("/create-complete", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create_job"])
async def create_complete_job(
    request: Request,
    job_create: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new content generation job using the complete orchestrated pipeline.

    This endpoint uses the new BacklinkJobOrchestrator which follows the
    Next-A1 specification with SERP research, intent analysis, and QC validation.

    **Pipeline Steps:**
    1. Profile target URL
    2. Profile publisher domain
    3. Classify anchor text
    4. Generate SERP queries
    5. Fetch SERP data (SerpAPI)
    6. Analyze intent alignment
    7. Generate content (LLM)
    8. Validate QC (Next-A1 criteria)
    9. Return complete job package

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

    # Emit WebSocket event: Job created
    await ws_manager.broadcast_job_update(
        job_id=job.id,
        status='PENDING',
        progress=0,
        message='Job created and queued for processing'
    )

    # Schedule background task with orchestrator
    background_tasks.add_task(
        run_orchestrated_job_background,
        job.id,
        job_create.publisher_domain,
        job_create.target_url,
        job_create.anchor_text,
        current_user.id,
        job_create.country,
        "sv",  # Default Swedish
        job_create.writing_strategy,
        provider,
        db
    )

    logger.info(
        f"Orchestrated job created: {job.id} - {job_create.publisher_domain} → {job_create.target_url}"
    )

    return job
