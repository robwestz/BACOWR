"""
User management routes for Wave 5 enterprise features.

Provides admin endpoints for managing users, roles, and quotas.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models.database import User
from ..models.schemas import (
    UserResponse,
    UserUpdateRequest,
    UserListResponse,
    QuotaStatus,
)
from ..services.auth_service import require_admin, get_current_user_jwt

router = APIRouter(prefix="/users", tags=["user-management"])


@router.get("", response_model=UserListResponse, dependencies=[Depends(require_admin)])
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    role: Optional[str] = Query(None, description="Filter by role"),
    status: Optional[str] = Query(None, description="Filter by account status"),
    search: Optional[str] = Query(None, description="Search by email or username"),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).

    Returns paginated list of users with optional filtering.

    Query parameters:
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    - **role**: Filter by role (admin/editor/viewer)
    - **status**: Filter by account status (active/suspended/deleted)
    - **search**: Search by email or username

    Requires: Admin role
    """
    query = db.query(User)

    # Apply filters
    if role:
        query = query.filter(User.role == role)

    if status:
        query = query.filter(User.account_status == status)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_term)) |
            (User.username.ilike(search_term)) |
            (User.full_name.ilike(search_term))
        )

    # Get total count
    total = query.count()

    # Paginate
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()

    return UserListResponse(
        users=[UserResponse.model_validate(user) for user in users],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def get_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get user by ID (admin only).

    Returns detailed information about a specific user.

    Path parameters:
    - **user_id**: User ID

    Requires: Admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user(
    user_id: str,
    user_update: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update user (admin only).

    Updates user information including role, quotas, and account status.

    Path parameters:
    - **user_id**: User ID

    Body parameters:
    - **full_name**: Update full name
    - **username**: Update username
    - **role**: Update role (admin/editor/viewer)
    - **jobs_quota**: Update monthly jobs quota
    - **tokens_quota**: Update monthly tokens quota
    - **account_status**: Update account status (active/suspended/deleted)

    Requires: Admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update fields
    if user_update.full_name is not None:
        user.full_name = user_update.full_name

    if user_update.username is not None:
        # Check if username is already taken
        existing = db.query(User).filter(
            User.username == user_update.username,
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = user_update.username

    if user_update.role is not None:
        user.role = user_update.role.value
        # Keep is_admin in sync
        user.is_admin = (user_update.role.value == "admin")

    if user_update.jobs_quota is not None:
        user.jobs_quota = user_update.jobs_quota

    if user_update.tokens_quota is not None:
        user.tokens_quota = user_update.tokens_quota

    if user_update.account_status is not None:
        user.account_status = user_update.account_status.value
        # Update is_active based on status
        user.is_active = (user_update.account_status.value == "active")

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: str,
    hard_delete: bool = Query(False, description="Permanently delete (vs soft delete)"),
    db: Session = Depends(get_db)
):
    """
    Delete user (admin only).

    Soft deletes (marks as deleted) or hard deletes (permanently removes) a user.

    Path parameters:
    - **user_id**: User ID

    Query parameters:
    - **hard_delete**: If true, permanently delete. If false, soft delete (default: false)

    Requires: Admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if hard_delete:
        # Permanently delete
        db.delete(user)
        db.commit()
        return {"message": "User permanently deleted", "user_id": user_id}
    else:
        # Soft delete
        user.account_status = "deleted"
        user.is_active = False
        db.commit()
        return {"message": "User marked as deleted", "user_id": user_id}


@router.get("/me/quota", response_model=QuotaStatus)
async def get_my_quota(
    current_user: User = Depends(get_current_user_jwt)
):
    """
    Get current user's quota status.

    Returns usage statistics and remaining quota for the authenticated user.

    Requires: Valid access token
    """
    return QuotaStatus(
        jobs_used=current_user.jobs_created_count,
        jobs_quota=current_user.jobs_quota,
        jobs_remaining=max(0, current_user.jobs_quota - current_user.jobs_created_count),
        tokens_used=current_user.tokens_used,
        tokens_quota=current_user.tokens_quota,
        tokens_remaining=max(0, current_user.tokens_quota - current_user.tokens_used),
        quota_exceeded=(
            current_user.jobs_created_count >= current_user.jobs_quota or
            current_user.tokens_used >= current_user.tokens_quota
        )
    )


@router.post("/{user_id}/quota/reset", dependencies=[Depends(require_admin)])
async def reset_user_quota(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Reset user quota counters (admin only).

    Resets the user's jobs and tokens usage counters to zero.
    Useful for monthly quota resets.

    Path parameters:
    - **user_id**: User ID

    Requires: Admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.jobs_created_count = 0
    user.tokens_used = 0
    db.commit()

    return {
        "message": "User quota reset successfully",
        "user_id": user_id,
        "jobs_used": 0,
        "tokens_used": 0
    }


@router.post("/{user_id}/suspend", dependencies=[Depends(require_admin)])
async def suspend_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Suspend user account (admin only).

    Suspends a user account, preventing them from accessing the system.

    Path parameters:
    - **user_id**: User ID

    Requires: Admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.account_status = "suspended"
    user.is_active = False
    db.commit()

    return {
        "message": "User suspended successfully",
        "user_id": user_id
    }


@router.post("/{user_id}/activate", dependencies=[Depends(require_admin)])
async def activate_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Activate user account (admin only).

    Activates a suspended or deleted user account.

    Path parameters:
    - **user_id**: User ID

    Requires: Admin role
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.account_status = "active"
    user.is_active = True
    db.commit()

    return {
        "message": "User activated successfully",
        "user_id": user_id
    }
