"""
Scheduler Service for executing scheduled jobs.

Runs as a background task using APScheduler to poll the database
for scheduled jobs that are ready to run.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
import asyncio
import logging

from .database import get_db
from .models.database import ScheduledJob, Job, User, JobTemplate, Campaign
from .models.schemas import ScheduledJobStatus
from .routes.scheduling import calculate_next_run

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


def create_job_from_scheduled(
    db: Session,
    scheduled_job: ScheduledJob
) -> Optional[Job]:
    """
    Create a Job record from a ScheduledJob configuration.

    Args:
        db: Database session
        scheduled_job: ScheduledJob to execute

    Returns:
        Created Job or None if failed
    """
    try:
        # Get job configuration
        job_config = scheduled_job.job_config

        # If using template, merge template config with job_config
        if scheduled_job.template_id:
            template = db.query(JobTemplate).filter(
                JobTemplate.id == scheduled_job.template_id
            ).first()

            if template:
                # Template provides defaults, job_config overrides
                merged_config = {
                    "publisher_domain": template.publisher_domain,
                    "llm_provider": template.llm_provider,
                    "llm_model": template.llm_model,
                    "writing_strategy": template.writing_strategy,
                    "country": template.country,
                    "language": template.language,
                    "max_retries": template.max_retries,
                    "batch_size": template.batch_size,
                }
                # Override with job-specific config
                merged_config.update(job_config)
                job_config = merged_config

                # Increment template usage
                template.use_count += 1
                template.last_used_at = datetime.utcnow()

        # Create Job record
        job = Job(
            user_id=scheduled_job.user_id,
            campaign_id=scheduled_job.campaign_id,
            publisher_domain=job_config.get("publisher_domain"),
            llm_provider=job_config.get("llm_provider"),
            llm_model=job_config.get("llm_model"),
            writing_strategy=job_config.get("writing_strategy", "standard"),
            country=job_config.get("country"),
            language=job_config.get("language", "en"),
            max_retries=job_config.get("max_retries", 3),
            batch_size=job_config.get("batch_size", 1),
            status="pending",
            metadata={
                "scheduled_job_id": scheduled_job.id,
                "scheduled_job_name": scheduled_job.name,
                "scheduled_at": scheduled_job.scheduled_at.isoformat(),
                "schedule_type": scheduled_job.schedule_type,
            }
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(
            f"Created job {job.id} from scheduled job {scheduled_job.id} "
            f"({scheduled_job.name})"
        )

        return job

    except Exception as e:
        logger.error(f"Error creating job from scheduled job {scheduled_job.id}: {e}")
        db.rollback()
        return None


async def process_scheduled_jobs():
    """
    Poll database for scheduled jobs that are ready to run.

    This function is called periodically by APScheduler.
    """
    db = next(get_db())

    try:
        now = datetime.utcnow()

        # Find all active scheduled jobs that are due to run
        due_jobs = db.query(ScheduledJob).filter(
            ScheduledJob.status == ScheduledJobStatus.ACTIVE,
            ScheduledJob.next_run_at != None,
            ScheduledJob.next_run_at <= now
        ).all()

        logger.info(f"Found {len(due_jobs)} scheduled jobs ready to run")

        for scheduled_job in due_jobs:
            try:
                # Check if max_runs limit reached
                if scheduled_job.max_runs and scheduled_job.run_count >= scheduled_job.max_runs:
                    logger.info(
                        f"Scheduled job {scheduled_job.id} ({scheduled_job.name}) "
                        f"reached max_runs limit ({scheduled_job.max_runs})"
                    )
                    scheduled_job.status = ScheduledJobStatus.COMPLETED
                    scheduled_job.updated_at = datetime.utcnow()
                    db.commit()
                    continue

                # Check if recurrence end date reached
                if scheduled_job.recurrence_end_date and now >= scheduled_job.recurrence_end_date:
                    logger.info(
                        f"Scheduled job {scheduled_job.id} ({scheduled_job.name}) "
                        f"reached recurrence end date"
                    )
                    scheduled_job.status = ScheduledJobStatus.EXPIRED
                    scheduled_job.updated_at = datetime.utcnow()
                    db.commit()
                    continue

                # Create the actual job
                job = create_job_from_scheduled(db, scheduled_job)

                if job:
                    # Update scheduled job stats
                    scheduled_job.run_count += 1
                    scheduled_job.last_run_at = now

                    # Calculate next run time
                    next_run = calculate_next_run(
                        scheduled_job.schedule_type,
                        scheduled_job.scheduled_at,
                        scheduled_job.recurrence_pattern,
                        now
                    )

                    scheduled_job.next_run_at = next_run

                    # If no next run, mark as completed
                    if next_run is None:
                        scheduled_job.status = ScheduledJobStatus.COMPLETED
                        logger.info(
                            f"Scheduled job {scheduled_job.id} ({scheduled_job.name}) "
                            f"has no more runs, marked as completed"
                        )

                    scheduled_job.updated_at = datetime.utcnow()
                    db.commit()

                    logger.info(
                        f"Successfully processed scheduled job {scheduled_job.id}. "
                        f"Next run: {next_run.isoformat() if next_run else 'None'}"
                    )
                else:
                    # Job creation failed, increment error count
                    scheduled_job.error_count += 1
                    scheduled_job.updated_at = datetime.utcnow()

                    # If too many errors, pause the scheduled job
                    if scheduled_job.error_count >= 5:
                        scheduled_job.status = ScheduledJobStatus.ERROR
                        logger.error(
                            f"Scheduled job {scheduled_job.id} ({scheduled_job.name}) "
                            f"has too many errors ({scheduled_job.error_count}), marking as ERROR"
                        )

                    db.commit()

            except Exception as e:
                logger.error(
                    f"Error processing scheduled job {scheduled_job.id}: {e}",
                    exc_info=True
                )
                db.rollback()

                # Increment error count
                try:
                    scheduled_job.error_count += 1
                    scheduled_job.updated_at = datetime.utcnow()

                    if scheduled_job.error_count >= 5:
                        scheduled_job.status = ScheduledJobStatus.ERROR

                    db.commit()
                except:
                    pass

    except Exception as e:
        logger.error(f"Error in process_scheduled_jobs: {e}", exc_info=True)

    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler.

    This should be called on application startup.
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running, skipping start")
        return

    logger.info("Starting job scheduler...")

    # Create scheduler
    scheduler = AsyncIOScheduler()

    # Add job to run every minute
    scheduler.add_job(
        process_scheduled_jobs,
        trigger=IntervalTrigger(minutes=1),
        id="process_scheduled_jobs",
        name="Process Scheduled Jobs",
        replace_existing=True,
        max_instances=1  # Prevent overlapping runs
    )

    # Start scheduler
    scheduler.start()

    logger.info("✓ Job scheduler started (polling every 1 minute)")


def stop_scheduler():
    """
    Stop the background scheduler.

    This should be called on application shutdown.
    """
    global scheduler

    if scheduler is None:
        return

    logger.info("Stopping job scheduler...")

    try:
        scheduler.shutdown(wait=True)
        scheduler = None
        logger.info("✓ Job scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")


def get_scheduler_status() -> dict:
    """
    Get the current status of the scheduler.

    Returns:
        Dictionary with scheduler status information
    """
    global scheduler

    if scheduler is None:
        return {
            "running": False,
            "jobs": []
        }

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        })

    return {
        "running": scheduler.running,
        "jobs": jobs
    }
