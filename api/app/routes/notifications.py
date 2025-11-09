"""
Notification routes for managing email and webhook preferences.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional

from ..database import get_db
from ..models.database import User
from ..auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ============================================================================
# Schemas
# ============================================================================

class NotificationPreferences(BaseModel):
    """Notification preferences schema."""
    notification_email: Optional[EmailStr] = None
    webhook_url: Optional[HttpUrl] = None
    enable_email_notifications: bool = False
    enable_webhook_notifications: bool = False


class NotificationPreferencesResponse(BaseModel):
    """Notification preferences response schema."""
    notification_email: Optional[str]
    webhook_url: Optional[str]
    enable_email_notifications: bool
    enable_webhook_notifications: bool

    class Config:
        from_attributes = True


# ============================================================================
# Endpoints
# ============================================================================

@router.get("", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's notification preferences.

    Returns email and webhook notification settings.
    """
    return NotificationPreferencesResponse(
        notification_email=current_user.notification_email,
        webhook_url=current_user.webhook_url,
        enable_email_notifications=current_user.enable_email_notifications,
        enable_webhook_notifications=current_user.enable_webhook_notifications
    )


@router.put("", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update notification preferences.

    Configure email and webhook notifications for job events.

    **Email Notifications:**
    - Set `notification_email` to receive email notifications
    - Enable with `enable_email_notifications: true`
    - Notifications sent for job completion and errors

    **Webhook Notifications:**
    - Set `webhook_url` to receive HTTP POST callbacks
    - Enable with `enable_webhook_notifications: true`
    - Webhook payload includes job details and status

    **Example:**
    ```json
    {
      "notification_email": "alerts@example.com",
      "webhook_url": "https://example.com/webhooks/bacowr",
      "enable_email_notifications": true,
      "enable_webhook_notifications": true
    }
    ```
    """
    # Update preferences
    if preferences.notification_email is not None:
        current_user.notification_email = str(preferences.notification_email)

    if preferences.webhook_url is not None:
        current_user.webhook_url = str(preferences.webhook_url)

    current_user.enable_email_notifications = preferences.enable_email_notifications
    current_user.enable_webhook_notifications = preferences.enable_webhook_notifications

    # Validation: Can't enable notifications without configuration
    if current_user.enable_email_notifications and not current_user.notification_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enable email notifications without setting notification_email"
        )

    if current_user.enable_webhook_notifications and not current_user.webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enable webhook notifications without setting webhook_url"
        )

    db.commit()
    db.refresh(current_user)

    return NotificationPreferencesResponse(
        notification_email=current_user.notification_email,
        webhook_url=current_user.webhook_url,
        enable_email_notifications=current_user.enable_email_notifications,
        enable_webhook_notifications=current_user.enable_webhook_notifications
    )


@router.post("/test-email")
async def test_email_notification(
    current_user: User = Depends(get_current_user)
):
    """
    Send a test email notification.

    Sends a test email to verify email configuration.
    Email notifications must be enabled.
    """
    if not current_user.enable_email_notifications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email notifications are not enabled"
        )

    if not current_user.notification_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notification email is not configured"
        )

    from ..notifications.email import email_service

    success = await email_service.send_job_completed(
        to_email=current_user.notification_email,
        job_id="test-job-id",
        publisher_domain="example.com",
        target_url="https://example.com/target",
        status="delivered",
        completed_at="2025-11-09T12:00:00Z",
        actual_cost=0.0123
    )

    if success:
        return {"message": f"Test email sent to {current_user.notification_email}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email. Check SMTP configuration."
        )


@router.post("/test-webhook")
async def test_webhook_notification(
    current_user: User = Depends(get_current_user)
):
    """
    Send a test webhook notification.

    Sends a test webhook to verify webhook configuration.
    Webhook notifications must be enabled.
    """
    if not current_user.enable_webhook_notifications:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook notifications are not enabled"
        )

    if not current_user.webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL is not configured"
        )

    from ..notifications.webhook import webhook_service

    success = await webhook_service.send_job_completed(
        webhook_url=current_user.webhook_url,
        job_id="test-job-id",
        status="delivered",
        publisher_domain="example.com",
        target_url="https://example.com/target",
        completed_at="2025-11-09T12:00:00Z",
        actual_cost=0.0123
    )

    if success:
        return {"message": f"Test webhook sent to {current_user.webhook_url}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test webhook. Check webhook URL and connectivity."
        )
