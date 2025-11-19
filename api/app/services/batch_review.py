"""
Batch review service for Day 2 QA workflow.

Handles business logic for:
- Creating batches from completed jobs
- Managing review workflow
- Approving/rejecting items
- Regenerating content
- Exporting approved batches
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json
from pathlib import Path

from ..models.database import Batch, BatchReviewItem, Job, User
from ..core.bacowr_wrapper import bacowr


class BatchReviewService:
    """Service for managing batch review workflow."""

    def __init__(self, db: Session, user_id: str):
        """
        Initialize batch review service.

        Args:
            db: Database session
            user_id: Current user ID
        """
        self.db = db
        self.user_id = user_id

    def create_batch_from_jobs(
        self,
        name: str,
        job_ids: List[str],
        description: Optional[str] = None,
        batch_config: Optional[Dict[str, Any]] = None
    ) -> Batch:
        """
        Create a new batch from completed jobs.

        Args:
            name: Batch name
            job_ids: List of job IDs to include
            description: Optional description
            batch_config: Optional configuration (auto-approve threshold, etc.)

        Returns:
            Created Batch object

        Raises:
            ValueError: If jobs not found, not owned by user, or not completed
        """
        # Validate all jobs exist and are owned by user
        jobs = self.db.query(Job).filter(
            and_(
                Job.id.in_(job_ids),
                Job.user_id == self.user_id
            )
        ).all()

        if len(jobs) != len(job_ids):
            found_ids = {job.id for job in jobs}
            missing_ids = set(job_ids) - found_ids
            raise ValueError(f"Jobs not found or not accessible: {missing_ids}")

        # Validate all jobs are completed (delivered or blocked)
        incomplete_jobs = [
            job.id for job in jobs
            if job.status.lower() not in ['delivered', 'blocked']
        ]
        if incomplete_jobs:
            raise ValueError(
                f"Jobs must be completed (status: delivered or blocked). "
                f"Incomplete jobs: {incomplete_jobs}"
            )

        # Calculate estimated total cost
        estimated_total = sum(
            job.estimated_cost or 0 for job in jobs
        )
        actual_total = sum(
            job.actual_cost or 0 for job in jobs
            if job.actual_cost is not None
        )

        # Create batch
        batch = Batch(
            user_id=self.user_id,
            name=name,
            description=description,
            status="pending",
            total_items=len(jobs),
            items_completed=0,
            items_approved=0,
            items_rejected=0,
            items_pending_review=len(jobs),
            estimated_total_cost=estimated_total,
            actual_total_cost=actual_total if actual_total > 0 else None,
            batch_config=batch_config
        )
        self.db.add(batch)
        self.db.flush()  # Get batch ID

        # Create batch review items
        for job in jobs:
            # Extract QC data from job
            qc_report = job.qc_report or {}
            qc_score = qc_report.get('score')
            qc_status = qc_report.get('status')
            qc_issues_count = len(qc_report.get('issues', []))

            item = BatchReviewItem(
                batch_id=batch.id,
                job_id=job.id,
                review_status="pending",
                qc_score=qc_score,
                qc_status=qc_status,
                qc_issues_count=qc_issues_count
            )
            self.db.add(item)

        # Update batch status to ready for review
        batch.status = "ready_for_review"
        batch.started_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(batch)

        return batch

    def get_batch(self, batch_id: str) -> Optional[Batch]:
        """
        Get batch by ID.

        Args:
            batch_id: Batch ID

        Returns:
            Batch object or None
        """
        return self.db.query(Batch).filter(
            and_(
                Batch.id == batch_id,
                Batch.user_id == self.user_id
            )
        ).first()

    def get_batch_items(
        self,
        batch_id: str,
        review_status: Optional[str] = None,
        min_qc_score: Optional[float] = None,
        max_qc_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[BatchReviewItem], int]:
        """
        Get batch items with filtering.

        Args:
            batch_id: Batch ID
            review_status: Filter by review status
            min_qc_score: Minimum QC score filter
            max_qc_score: Maximum QC score filter
            limit: Max items to return
            offset: Offset for pagination

        Returns:
            Tuple of (items, total_count)
        """
        # Base query
        query = self.db.query(BatchReviewItem).join(Batch).filter(
            and_(
                BatchReviewItem.batch_id == batch_id,
                Batch.user_id == self.user_id
            )
        )

        # Apply filters
        if review_status:
            query = query.filter(BatchReviewItem.review_status == review_status)

        if min_qc_score is not None:
            query = query.filter(BatchReviewItem.qc_score >= min_qc_score)

        if max_qc_score is not None:
            query = query.filter(BatchReviewItem.qc_score <= max_qc_score)

        # Get total count
        total = query.count()

        # Get items with pagination
        items = query.order_by(
            BatchReviewItem.qc_score.desc().nullslast(),
            BatchReviewItem.created_at
        ).limit(limit).offset(offset).all()

        return items, total

    def approve_item(
        self,
        batch_id: str,
        item_id: str,
        reviewer_notes: Optional[str] = None
    ) -> BatchReviewItem:
        """
        Approve a batch item.

        Args:
            batch_id: Batch ID
            item_id: Item ID
            reviewer_notes: Optional reviewer notes

        Returns:
            Updated BatchReviewItem

        Raises:
            ValueError: If item not found or already reviewed
        """
        item = self._get_item_for_review(batch_id, item_id)

        if item.review_status != "pending":
            raise ValueError(
                f"Item already reviewed with status: {item.review_status}"
            )

        # Update item
        item.review_status = "approved"
        item.reviewer_notes = reviewer_notes
        item.reviewed_by = self.user_id
        item.reviewed_at = datetime.utcnow()

        # Update batch statistics
        batch = item.batch
        batch.items_approved += 1
        batch.items_pending_review -= 1

        self._check_batch_completion(batch)

        self.db.commit()
        self.db.refresh(item)

        return item

    def reject_item(
        self,
        batch_id: str,
        item_id: str,
        reviewer_notes: Optional[str] = None
    ) -> BatchReviewItem:
        """
        Reject a batch item.

        Args:
            batch_id: Batch ID
            item_id: Item ID
            reviewer_notes: Optional reviewer notes (reason for rejection)

        Returns:
            Updated BatchReviewItem

        Raises:
            ValueError: If item not found or already reviewed
        """
        item = self._get_item_for_review(batch_id, item_id)

        if item.review_status != "pending":
            raise ValueError(
                f"Item already reviewed with status: {item.review_status}"
            )

        # Update item
        item.review_status = "rejected"
        item.reviewer_notes = reviewer_notes
        item.reviewed_by = self.user_id
        item.reviewed_at = datetime.utcnow()

        # Update batch statistics
        batch = item.batch
        batch.items_rejected += 1
        batch.items_pending_review -= 1

        self._check_batch_completion(batch)

        self.db.commit()
        self.db.refresh(item)

        return item

    def regenerate_item(
        self,
        batch_id: str,
        item_id: str,
        reviewer_notes: Optional[str] = None
    ) -> BatchReviewItem:
        """
        Request regeneration of a batch item.

        Args:
            batch_id: Batch ID
            item_id: Item ID
            reviewer_notes: Optional notes (reason for regeneration)

        Returns:
            Updated BatchReviewItem

        Raises:
            ValueError: If item not found or already approved
        """
        item = self._get_item_for_review(batch_id, item_id)

        if item.review_status == "approved":
            raise ValueError("Cannot regenerate approved item")

        # Update item status
        item.review_status = "needs_regeneration"
        item.reviewer_notes = reviewer_notes
        item.reviewed_by = self.user_id
        item.reviewed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(item)

        return item

    async def execute_regeneration(
        self,
        batch_id: str,
        item_id: str
    ) -> BatchReviewItem:
        """
        Execute regeneration for a batch item.

        Creates a new job with the same parameters and links it to the batch.

        Args:
            batch_id: Batch ID
            item_id: Item ID

        Returns:
            Updated BatchReviewItem with new job

        Raises:
            ValueError: If item not in needs_regeneration status
        """
        item = self._get_item_for_review(batch_id, item_id)

        if item.review_status != "needs_regeneration":
            raise ValueError(
                f"Item status must be 'needs_regeneration', got: {item.review_status}"
            )

        # Get original job
        original_job = item.job
        if not item.original_job_id:
            item.original_job_id = original_job.id

        # Update status to regenerating
        item.review_status = "regenerating"
        self.db.commit()

        try:
            # Create new job with same parameters
            result = await bacowr.run_job(
                publisher_domain=original_job.publisher_domain,
                target_url=original_job.target_url,
                anchor_text=original_job.anchor_text,
                llm_provider=original_job.llm_provider,
                writing_strategy=original_job.writing_strategy,
                use_ahrefs=original_job.use_ahrefs,
                country=original_job.country,
                enable_llm_profiling=original_job.enable_llm_profiling
            )

            # Create new job record
            new_job = Job(
                user_id=self.user_id,
                publisher_domain=original_job.publisher_domain,
                target_url=original_job.target_url,
                anchor_text=original_job.anchor_text,
                llm_provider=original_job.llm_provider,
                writing_strategy=original_job.writing_strategy,
                country=original_job.country,
                use_ahrefs=original_job.use_ahrefs,
                enable_llm_profiling=original_job.enable_llm_profiling,
                status=result['status'].lower(),
                article_text=result.get('article'),
                job_package=result.get('job_package'),
                qc_report=result.get('qc_report'),
                execution_log=result.get('execution_log'),
                metrics=result.get('metrics'),
                actual_cost=result.get('metrics', {}).get('generation', {}).get('cost'),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            self.db.add(new_job)
            self.db.flush()

            # Update batch item to point to new job
            item.job_id = new_job.id
            item.review_status = "regenerated"
            item.regeneration_count += 1

            # Update QC snapshot
            qc_report = new_job.qc_report or {}
            item.qc_score = qc_report.get('score')
            item.qc_status = qc_report.get('status')
            item.qc_issues_count = len(qc_report.get('issues', []))

            self.db.commit()
            self.db.refresh(item)

            return item

        except Exception as e:
            # Revert status on failure
            item.review_status = "needs_regeneration"
            item.reviewer_notes = f"Regeneration failed: {str(e)}"
            self.db.commit()
            raise

    def export_approved_batch(
        self,
        batch_id: str,
        export_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export all approved items from a batch.

        Args:
            batch_id: Batch ID
            export_format: Export format ("json", "csv", etc.)

        Returns:
            Export metadata dict with file path

        Raises:
            ValueError: If batch not found or no approved items
        """
        batch = self.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch not found: {batch_id}")

        # Get all approved items
        approved_items, count = self.get_batch_items(
            batch_id=batch_id,
            review_status="approved",
            limit=10000
        )

        if count == 0:
            raise ValueError(f"No approved items in batch {batch_id}")

        # Prepare export data
        export_data = {
            "batch_id": batch.id,
            "batch_name": batch.name,
            "exported_at": datetime.utcnow().isoformat(),
            "total_approved": count,
            "items": []
        }

        for item in approved_items:
            job = item.job
            export_data["items"].append({
                "job_id": job.id,
                "publisher_domain": job.publisher_domain,
                "target_url": job.target_url,
                "anchor_text": job.anchor_text,
                "article_text": job.article_text,
                "qc_score": item.qc_score,
                "qc_status": item.qc_status,
                "reviewer_notes": item.reviewer_notes,
                "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
                "job_package": job.job_package
            })

        # Write to file
        export_dir = Path("storage/exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = export_dir / f"batch_{batch.id}_{timestamp}_approved.{export_format}"

        if export_format == "json":
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Export format not supported: {export_format}")

        return {
            "batch_id": batch.id,
            "total_approved": count,
            "export_format": export_format,
            "file_path": str(file_path),
            "download_url": f"/api/v1/batches/{batch.id}/download",
            "created_at": datetime.utcnow()
        }

    def _get_item_for_review(self, batch_id: str, item_id: str) -> BatchReviewItem:
        """
        Get batch item for review, with validation.

        Args:
            batch_id: Batch ID
            item_id: Item ID

        Returns:
            BatchReviewItem

        Raises:
            ValueError: If item not found or not accessible
        """
        item = self.db.query(BatchReviewItem).join(Batch).filter(
            and_(
                BatchReviewItem.id == item_id,
                BatchReviewItem.batch_id == batch_id,
                Batch.user_id == self.user_id
            )
        ).first()

        if not item:
            raise ValueError(f"Batch item not found: {item_id}")

        return item

    def _check_batch_completion(self, batch: Batch):
        """
        Check if batch review is complete and update status.

        Args:
            batch: Batch to check
        """
        if batch.items_pending_review == 0:
            batch.status = "completed"
            batch.completed_at = datetime.utcnow()
            batch.review_completed_at = datetime.utcnow()
