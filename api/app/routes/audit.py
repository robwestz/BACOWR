"""
Audit log API routes.

Endpoints for viewing and searching audit logs (admin only).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models.database import User
from ..models.audit import AuditLog
from ..auth import get_current_user
from ..services.audit_service import AuditService
from pydantic import BaseModel


router = APIRouter(prefix="/audit", tags=["audit"])


# Response schemas
class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: str
    timestamp: datetime
    user_id: Optional[str]
    user_email: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    method: Optional[str]
    endpoint: Optional[str]
    ip_address: Optional[str]
    status: str
    status_code: Optional[str]
    error_message: Optional[str]
    duration_ms: Optional[str]

    class Config:
        from_attributes = True


class AuditLogDetailResponse(AuditLogResponse):
    """Detailed audit log with request/response data."""
    request_data: Optional[dict]
    response_data: Optional[dict]
    metadata: Optional[dict]
    user_agent: Optional[str]

    class Config:
        from_attributes = True


class AuditStatsResponse(BaseModel):
    """Audit statistics."""
    total_events: int
    events_by_action: dict
    events_by_user: dict
    events_by_status: dict
    failed_events: int
    security_events: int
    avg_duration_ms: Optional[float]


# Admin check decorator
def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


@router.get("/logs", response_model=List[AuditLogResponse])
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    hours: Optional[int] = Query(None, ge=1, le=720),  # Max 30 days
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List audit logs (admin only).

    Args:
        limit: Max results
        offset: Offset for pagination
        action: Filter by action
        user_id: Filter by user
        resource_type: Filter by resource type
        status_filter: Filter by status
        hours: Look back N hours
        current_user: Current admin user
        db: Database session

    Returns:
        List of audit logs
    """
    query = db.query(AuditLog)

    # Apply filters
    if action:
        query = query.filter(AuditLog.action == action)

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)

    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)

    if status_filter:
        query = query.filter(AuditLog.status == status_filter)

    if hours:
        since = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(AuditLog.timestamp >= since)

    logs = query.order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).offset(offset).all()

    return logs


@router.get("/logs/{log_id}", response_model=AuditLogDetailResponse)
async def get_audit_log(
    log_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed audit log entry (admin only).

    Args:
        log_id: Audit log ID
        current_user: Current admin user
        db: Database session

    Returns:
        Detailed audit log

    Raises:
        404: If log not found
    """
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log not found: {log_id}"
        )

    return log


@router.get("/users/{user_id}/activity", response_model=List[AuditLogResponse])
async def get_user_activity(
    user_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    hours: Optional[int] = Query(None, ge=1, le=720),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit trail for specific user (admin only).

    Args:
        user_id: User ID
        limit: Max results
        offset: Offset for pagination
        action: Filter by action
        hours: Look back N hours
        current_user: Current admin user
        db: Database session

    Returns:
        List of user's audit logs
    """
    service = AuditService(db)

    start_date = None
    if hours:
        start_date = datetime.utcnow() - timedelta(hours=hours)

    logs = service.get_user_activity(
        user_id=user_id,
        limit=limit,
        offset=offset,
        action_filter=action,
        start_date=start_date
    )

    return logs


@router.get("/resources/{resource_type}/{resource_id}/history", response_model=List[AuditLogResponse])
async def get_resource_history(
    resource_type: str,
    resource_id: str,
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit history for specific resource (admin only).

    Args:
        resource_type: Resource type (job, batch, etc.)
        resource_id: Resource ID
        limit: Max results
        current_user: Current admin user
        db: Database session

    Returns:
        List of resource audit logs
    """
    service = AuditService(db)
    logs = service.get_resource_history(
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit
    )

    return logs


@router.get("/security-events", response_model=List[AuditLogResponse])
async def get_security_events(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get recent security events (admin only).

    Args:
        hours: Look back N hours
        limit: Max results
        current_user: Current admin user
        db: Database session

    Returns:
        List of security event audit logs
    """
    service = AuditService(db)
    logs = service.get_security_events(hours=hours, limit=limit)

    return logs


@router.get("/failed-actions", response_model=List[AuditLogResponse])
async def get_failed_actions(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get recent failed actions (admin only).

    Args:
        hours: Look back N hours
        limit: Max results
        current_user: Current admin user
        db: Database session

    Returns:
        List of failed action audit logs
    """
    service = AuditService(db)
    logs = service.get_failed_actions(hours=hours, limit=limit)

    return logs


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    hours: int = Query(24, ge=1, le=720),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get audit statistics (admin only).

    Args:
        hours: Look back N hours
        current_user: Current admin user
        db: Database session

    Returns:
        Audit statistics
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    # Get all logs in time range
    logs = db.query(AuditLog).filter(AuditLog.timestamp >= since).all()

    # Calculate statistics
    total_events = len(logs)

    events_by_action = {}
    events_by_user = {}
    events_by_status = {}
    failed_events = 0
    security_events = 0
    total_duration = 0
    duration_count = 0

    for log in logs:
        # By action
        events_by_action[log.action] = events_by_action.get(log.action, 0) + 1

        # By user
        user_key = log.user_email or log.user_id or "anonymous"
        events_by_user[user_key] = events_by_user.get(user_key, 0) + 1

        # By status
        events_by_status[log.status] = events_by_status.get(log.status, 0) + 1

        # Failed events
        if log.status in ["failure", "error"]:
            failed_events += 1

        # Security events
        if log.action.startswith("auth."):
            security_events += 1

        # Duration
        if log.duration_ms:
            try:
                total_duration += int(log.duration_ms)
                duration_count += 1
            except:
                pass

    avg_duration_ms = total_duration / duration_count if duration_count > 0 else None

    return AuditStatsResponse(
        total_events=total_events,
        events_by_action=events_by_action,
        events_by_user=events_by_user,
        events_by_status=events_by_status,
        failed_events=failed_events,
        security_events=security_events,
        avg_duration_ms=avg_duration_ms
    )
