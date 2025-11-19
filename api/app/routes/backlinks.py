"""
Backlinks routes for managing historical backlinks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from ..database import get_db
from ..models.database import User, Backlink
from ..models.schemas import (
    BacklinkCreate, BacklinkBulkImport, BacklinkResponse,
    BacklinkStats, PaginatedResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/backlinks", tags=["backlinks"])


@router.post("", response_model=BacklinkResponse, status_code=status.HTTP_201_CREATED)
def create_backlink(
    backlink_create: BacklinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new backlink record."""
    backlink = Backlink(
        user_id=current_user.id,
        **backlink_create.model_dump()
    )

    db.add(backlink)
    db.commit()
    db.refresh(backlink)

    return BacklinkResponse.model_validate(backlink)


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
def bulk_import_backlinks(
    bulk_import: BacklinkBulkImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Bulk import backlinks.

    Maximum 1000 backlinks per request.
    """
    backlinks = []
    for backlink_data in bulk_import.backlinks:
        backlink = Backlink(
            user_id=current_user.id,
            **backlink_data.model_dump()
        )
        backlinks.append(backlink)

    db.bulk_save_objects(backlinks)
    db.commit()

    return {
        "imported_count": len(backlinks),
        "message": f"Successfully imported {len(backlinks)} backlinks"
    }


@router.get("", response_model=PaginatedResponse)
def list_backlinks(
    page: int = 1,
    page_size: int = 20,
    publisher_domain: Optional[str] = None,
    category: Optional[str] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List backlinks with pagination and filtering.

    Filters:
    - publisher_domain: Filter by publisher domain
    - category: Filter by category
    - language: Filter by language
    - search: Search in anchor text, publisher domain, or target URL
    """
    query = db.query(Backlink).filter(Backlink.user_id == current_user.id)

    # Apply filters
    if publisher_domain:
        query = query.filter(Backlink.publisher_domain == publisher_domain)

    if category:
        query = query.filter(Backlink.category == category)

    if language:
        query = query.filter(Backlink.language == language)

    if search:
        # Sanitize search input to prevent SQL injection and resource exhaustion
        if len(search) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search term too long (max 100 characters)"
            )
        # Escape special LIKE characters
        search_sanitized = search.replace('%', '\\%').replace('_', '\\_')
        search_term = f"%{search_sanitized}%"
        query = query.filter(
            (Backlink.anchor_text.ilike(search_term, escape='\\')) |
            (Backlink.publisher_domain.ilike(search_term, escape='\\')) |
            (Backlink.target_url.ilike(search_term, escape='\\'))
        )

    # Count total
    total = query.count()

    # Paginate
    backlinks = query.order_by(Backlink.created_at.desc())\
        .offset((page - 1) * page_size)\
        .limit(page_size)\
        .all()

    return PaginatedResponse.create(
        items=[BacklinkResponse.model_validate(b) for b in backlinks],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=BacklinkStats)
def get_backlinks_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about backlinks.

    Returns:
    - Total count
    - Breakdown by publisher, category, language
    - Average domain/page authority
    - Total traffic estimate
    """
    # Total count
    total_count = db.query(Backlink).filter(Backlink.user_id == current_user.id).count()

    # By publisher
    by_publisher = {}
    publisher_counts = db.query(
        Backlink.publisher_domain,
        func.count(Backlink.id)
    ).filter(
        Backlink.user_id == current_user.id
    ).group_by(Backlink.publisher_domain).all()

    for domain, count in publisher_counts:
        by_publisher[domain] = count

    # By category
    by_category = {}
    category_counts = db.query(
        Backlink.category,
        func.count(Backlink.id)
    ).filter(
        Backlink.user_id == current_user.id,
        Backlink.category.isnot(None)
    ).group_by(Backlink.category).all()

    for category, count in category_counts:
        by_category[category or "uncategorized"] = count

    # By language
    by_language = {}
    language_counts = db.query(
        Backlink.language,
        func.count(Backlink.id)
    ).filter(
        Backlink.user_id == current_user.id,
        Backlink.language.isnot(None)
    ).group_by(Backlink.language).all()

    for lang, count in language_counts:
        by_language[lang or "unknown"] = count

    # Average domain authority
    avg_da = db.query(func.avg(Backlink.domain_authority)).filter(
        Backlink.user_id == current_user.id,
        Backlink.domain_authority.isnot(None)
    ).scalar()

    # Average page authority
    avg_pa = db.query(func.avg(Backlink.page_authority)).filter(
        Backlink.user_id == current_user.id,
        Backlink.page_authority.isnot(None)
    ).scalar()

    # Total traffic estimate
    total_traffic = db.query(func.sum(Backlink.traffic_estimate)).filter(
        Backlink.user_id == current_user.id,
        Backlink.traffic_estimate.isnot(None)
    ).scalar()

    return BacklinkStats(
        total_count=total_count,
        by_publisher=by_publisher,
        by_category=by_category,
        by_language=by_language,
        avg_domain_authority=float(avg_da) if avg_da else None,
        avg_page_authority=float(avg_pa) if avg_pa else None,
        total_traffic_estimate=int(total_traffic) if total_traffic else None
    )


@router.get("/{backlink_id}", response_model=BacklinkResponse)
def get_backlink(
    backlink_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific backlink by ID."""
    backlink = db.query(Backlink).filter(
        Backlink.id == backlink_id,
        Backlink.user_id == current_user.id
    ).first()

    if not backlink:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backlink not found"
        )

    return BacklinkResponse.model_validate(backlink)


@router.delete("/{backlink_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backlink(
    backlink_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a backlink."""
    backlink = db.query(Backlink).filter(
        Backlink.id == backlink_id,
        Backlink.user_id == current_user.id
    ).first()

    if not backlink:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backlink not found"
        )

    db.delete(backlink)
    db.commit()

    return None
