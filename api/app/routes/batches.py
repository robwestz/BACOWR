"""
Batch review API routes.

Endpoints for Day 2 QA workflow:
- Create batches from completed jobs
- List and filter batch items
- Approve/reject/regenerate items
- Export approved batches
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional

from ..database import get_db
from ..models.schemas import (
    BatchCreate,
    BatchResponse,
    BatchDetailResponse,
    BatchItemResponse,
    ReviewDecisionRequest,
    BatchExportResponse,
    JobDetailResponse
)
from ..models.database import Batch, BatchReviewItem, Job, User
from ..services.batch_review import BatchReviewService
from ..auth import get_current_user

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(
    batch_data: BatchCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new batch from completed jobs.

    Args:
        batch_data: Batch creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created batch

    Raises:
        400: If jobs invalid or not completed
        404: If jobs not found
    """
    service = BatchReviewService(db, current_user.id)

    try:
        batch = service.create_batch_from_jobs(
            name=batch_data.name,
            job_ids=batch_data.job_ids,
            description=batch_data.description,
            batch_config=batch_data.batch_config
        )
        return batch

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[BatchResponse])
async def list_batches(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all batches for current user.

    Args:
        status_filter: Optional status filter
        limit: Max batches to return
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of batches
    """
    query = db.query(Batch).filter(Batch.user_id == current_user.id)

    if status_filter:
        query = query.filter(Batch.status == status_filter)

    batches = query.order_by(
        Batch.created_at.desc()
    ).limit(limit).offset(offset).all()

    return batches


@router.get("/{batch_id}", response_model=BatchDetailResponse)
async def get_batch(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get batch details with all items.

    Args:
        batch_id: Batch ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Batch details with items

    Raises:
        404: If batch not found
    """
    service = BatchReviewService(db, current_user.id)
    batch = service.get_batch(batch_id)

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}"
        )

    # Load items (eagerly to avoid N+1 queries)
    batch = db.query(Batch).options(
        joinedload(Batch.items).joinedload(BatchReviewItem.job)
    ).filter(Batch.id == batch_id).first()

    return batch


@router.get("/{batch_id}/items", response_model=List[BatchItemResponse])
async def get_batch_items(
    batch_id: str,
    review_status: Optional[str] = Query(None),
    min_qc_score: Optional[float] = Query(None, ge=0, le=1),
    max_qc_score: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get batch items with filtering.

    Args:
        batch_id: Batch ID
        review_status: Filter by review status
        min_qc_score: Minimum QC score filter
        max_qc_score: Maximum QC score filter
        limit: Max items to return
        offset: Offset for pagination
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of batch items

    Raises:
        404: If batch not found
    """
    service = BatchReviewService(db, current_user.id)

    # Verify batch exists
    batch = service.get_batch(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}"
        )

    items, total = service.get_batch_items(
        batch_id=batch_id,
        review_status=review_status,
        min_qc_score=min_qc_score,
        max_qc_score=max_qc_score,
        limit=limit,
        offset=offset
    )

    # Eagerly load job data for each item
    items_with_jobs = []
    for item in items:
        item_dict = BatchItemResponse.from_orm(item).dict()

        # Load job details
        job = db.query(Job).filter(Job.id == item.job_id).first()
        if job:
            item_dict['job'] = JobDetailResponse.from_orm(job)

        items_with_jobs.append(BatchItemResponse(**item_dict))

    return items_with_jobs


@router.post("/{batch_id}/items/{item_id}/review", response_model=BatchItemResponse)
async def review_item(
    batch_id: str,
    item_id: str,
    decision: ReviewDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Review a batch item (approve, reject, or request regeneration).

    Args:
        batch_id: Batch ID
        item_id: Item ID
        decision: Review decision
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated batch item

    Raises:
        400: If item already reviewed or invalid decision
        404: If batch or item not found
    """
    service = BatchReviewService(db, current_user.id)

    try:
        if decision.decision == "approved":
            item = service.approve_item(
                batch_id=batch_id,
                item_id=item_id,
                reviewer_notes=decision.reviewer_notes
            )
        elif decision.decision == "rejected":
            item = service.reject_item(
                batch_id=batch_id,
                item_id=item_id,
                reviewer_notes=decision.reviewer_notes
            )
        elif decision.decision == "needs_regeneration":
            item = service.regenerate_item(
                batch_id=batch_id,
                item_id=item_id,
                reviewer_notes=decision.reviewer_notes
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid decision: {decision.decision}"
            )

        return item

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{batch_id}/items/{item_id}/regenerate", response_model=BatchItemResponse)
async def execute_regeneration(
    batch_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute regeneration for a batch item.

    Creates a new job with the same parameters and updates the batch item.

    Args:
        batch_id: Batch ID
        item_id: Item ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated batch item with new job

    Raises:
        400: If item not in needs_regeneration status
        404: If batch or item not found
    """
    service = BatchReviewService(db, current_user.id)

    try:
        item = await service.execute_regeneration(
            batch_id=batch_id,
            item_id=item_id
        )
        return item

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{batch_id}/export", response_model=BatchExportResponse)
async def export_batch(
    batch_id: str,
    export_format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all approved items from a batch.

    Args:
        batch_id: Batch ID
        export_format: Export format (json or csv)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Export metadata with file path

    Raises:
        400: If no approved items
        404: If batch not found
    """
    service = BatchReviewService(db, current_user.id)

    try:
        export_data = service.export_approved_batch(
            batch_id=batch_id,
            export_format=export_format
        )
        return export_data

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{batch_id}/stats")
async def get_batch_stats(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get batch statistics and analytics.

    Args:
        batch_id: Batch ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Batch statistics

    Raises:
        404: If batch not found
    """
    service = BatchReviewService(db, current_user.id)
    batch = service.get_batch(batch_id)

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch not found: {batch_id}"
        )

    # Get QC distribution
    qc_distribution = db.query(
        BatchReviewItem.qc_status,
        func.count(BatchReviewItem.id)
    ).filter(
        BatchReviewItem.batch_id == batch_id
    ).group_by(
        BatchReviewItem.qc_status
    ).all()

    # Get review status distribution
    review_distribution = db.query(
        BatchReviewItem.review_status,
        func.count(BatchReviewItem.id)
    ).filter(
        BatchReviewItem.batch_id == batch_id
    ).group_by(
        BatchReviewItem.review_status
    ).all()

    # Get average QC score
    avg_qc_score = db.query(
        func.avg(BatchReviewItem.qc_score)
    ).filter(
        BatchReviewItem.batch_id == batch_id
    ).scalar()

    return {
        "batch_id": batch.id,
        "total_items": batch.total_items,
        "items_approved": batch.items_approved,
        "items_rejected": batch.items_rejected,
        "items_pending_review": batch.items_pending_review,
        "avg_qc_score": float(avg_qc_score) if avg_qc_score else None,
        "qc_status_distribution": {
            status: count for status, count in qc_distribution
        },
        "review_status_distribution": {
            status: count for status, count in review_distribution
        },
        "estimated_total_cost": batch.estimated_total_cost,
        "actual_total_cost": batch.actual_total_cost,
        "completion_rate": (
            (batch.items_approved + batch.items_rejected) / batch.total_items * 100
            if batch.total_items > 0 else 0
        )
    }
