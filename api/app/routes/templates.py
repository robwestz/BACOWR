"""
Job template management routes.

Templates allow users to save and reuse job configurations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models.database import User, JobTemplate, Campaign
from ..models.schemas import (
    JobTemplateCreate, JobTemplateUpdate, JobTemplateResponse,
    JobCreate
)
from ..auth import get_current_user
from ..rate_limit import limiter, RATE_LIMITS

router = APIRouter(prefix="/templates", tags=["templates"])


@router.post("", response_model=JobTemplateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMITS["create_job"])
def create_template(
    request: Request,
    template_data: JobTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new job template.

    Templates save job configurations for reuse:
    - Publisher-specific settings
    - Common job types ("High quality backlink")
    - Client-specific configurations
    """
    # Validate campaign_id if provided
    if template_data.campaign_id:
        campaign = db.query(Campaign).filter(
            Campaign.id == template_data.campaign_id,
            Campaign.user_id == current_user.id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

    template = JobTemplate(
        user_id=current_user.id,
        campaign_id=template_data.campaign_id,
        name=template_data.name,
        description=template_data.description,
        publisher_domain=template_data.publisher_domain,
        llm_provider=template_data.llm_provider,
        writing_strategy=template_data.writing_strategy,
        country=template_data.country,
        use_ahrefs=template_data.use_ahrefs,
        enable_llm_profiling=template_data.enable_llm_profiling,
        is_favorite=template_data.is_favorite or False,
        tags=template_data.tags,
        use_count=0
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return JobTemplateResponse.model_validate(template)


@router.get("", response_model=List[JobTemplateResponse])
@limiter.limit(RATE_LIMITS["list_jobs"])
def list_templates(
    request: Request,
    campaign_id: Optional[str] = None,
    favorites_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all job templates for the current user.

    Optional filters:
    - campaign_id: Filter by campaign
    - favorites_only: Show only favorited templates
    """
    query = db.query(JobTemplate).filter(JobTemplate.user_id == current_user.id)

    if campaign_id:
        query = query.filter(JobTemplate.campaign_id == campaign_id)

    if favorites_only:
        query = query.filter(JobTemplate.is_favorite == True)

    templates = query.order_by(
        JobTemplate.is_favorite.desc(),
        JobTemplate.last_used_at.desc().nulls_last(),
        JobTemplate.created_at.desc()
    ).all()

    return [JobTemplateResponse.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=JobTemplateResponse)
@limiter.limit(RATE_LIMITS["get_job"])
def get_template(
    request: Request,
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific job template by ID.
    """
    template = db.query(JobTemplate).filter(
        JobTemplate.id == template_id,
        JobTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return JobTemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=JobTemplateResponse)
@limiter.limit(RATE_LIMITS["create_job"])
def update_template(
    request: Request,
    template_id: str,
    template_data: JobTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a job template.
    """
    template = db.query(JobTemplate).filter(
        JobTemplate.id == template_id,
        JobTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    # Validate campaign_id if being updated
    if template_data.campaign_id:
        campaign = db.query(Campaign).filter(
            Campaign.id == template_data.campaign_id,
            Campaign.user_id == current_user.id
        ).first()
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )

    # Update fields
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    template.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(template)

    return JobTemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(RATE_LIMITS["create_job"])
def delete_template(
    request: Request,
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a job template.
    """
    template = db.query(JobTemplate).filter(
        JobTemplate.id == template_id,
        JobTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    db.delete(template)
    db.commit()

    return None


@router.post("/{template_id}/use")
@limiter.limit(RATE_LIMITS["create_job"])
def use_template(
    request: Request,
    template_id: str,
    target_url: str,
    anchor_text: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Use a template to create a job configuration.

    This doesn't create the job itself, but returns a JobCreate
    object that can be used to create a job.

    Required parameters (not in template):
    - target_url: Target URL for the backlink
    - anchor_text: Anchor text for the backlink
    """
    template = db.query(JobTemplate).filter(
        JobTemplate.id == template_id,
        JobTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    # Update template usage stats
    template.use_count += 1
    template.last_used_at = datetime.utcnow()
    db.commit()

    # Build job config from template
    job_config = {
        "publisher_domain": template.publisher_domain or "",
        "target_url": target_url,
        "anchor_text": anchor_text,
        "llm_provider": template.llm_provider or "auto",
        "writing_strategy": template.writing_strategy or "multi_stage",
        "country": template.country or "se",
        "use_ahrefs": template.use_ahrefs,
        "enable_llm_profiling": template.enable_llm_profiling
    }

    return {
        "template_id": template_id,
        "template_name": template.name,
        "job_config": job_config
    }


@router.post("/{template_id}/favorite", response_model=JobTemplateResponse)
@limiter.limit(RATE_LIMITS["create_job"])
def toggle_favorite(
    request: Request,
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle template favorite status.
    """
    template = db.query(JobTemplate).filter(
        JobTemplate.id == template_id,
        JobTemplate.user_id == current_user.id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    template.is_favorite = not template.is_favorite
    template.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(template)

    return JobTemplateResponse.model_validate(template)
