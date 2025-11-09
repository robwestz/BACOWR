"""
Webhook notification service.

Sends HTTP POST callbacks to external systems for job events.
"""

import httpx
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger(__name__)


class WebhookService:
    """
    Webhook service for sending HTTP callbacks.

    Supports retry logic and webhook signature verification.
    """

    def __init__(self):
        """Initialize webhook service."""
        self.timeout = int(os.getenv("WEBHOOK_TIMEOUT", "10"))
        self.max_retries = int(os.getenv("WEBHOOK_MAX_RETRIES", "3"))
        self.secret_key = os.getenv("WEBHOOK_SECRET_KEY", "")

    def generate_signature(self, payload: str) -> str:
        """
        Generate HMAC signature for webhook payload.

        Args:
            payload: JSON payload string

        Returns:
            Hexadecimal signature
        """
        if not self.secret_key:
            return ""

        signature = hmac.new(
            self.secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def send_webhook(
        self,
        webhook_url: str,
        event_type: str,
        payload: Dict[str, Any],
        retries: int = 0
    ) -> bool:
        """
        Send webhook POST request.

        Args:
            webhook_url: Target webhook URL
            event_type: Event type (job.completed, job.error, etc.)
            payload: Event data
            retries: Current retry attempt

        Returns:
            True if sent successfully, False otherwise
        """
        # Prepare webhook payload
        webhook_payload = {
            "event": event_type,
            "data": payload,
            "timestamp": payload.get("timestamp", "")
        }

        payload_json = json.dumps(webhook_payload)

        # Generate signature
        signature = self.generate_signature(payload_json)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "BACOWR-Webhook/1.0"
        }

        if signature:
            headers["X-BACOWR-Signature"] = signature

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    webhook_url,
                    content=payload_json,
                    headers=headers
                )

                # Consider 2xx status codes as success
                if 200 <= response.status_code < 300:
                    logger.info(f"Webhook sent to {webhook_url}: {event_type}")
                    return True
                else:
                    logger.warning(
                        f"Webhook returned {response.status_code} for {webhook_url}: {event_type}"
                    )

                    # Retry on 5xx errors
                    if 500 <= response.status_code < 600 and retries < self.max_retries:
                        logger.info(f"Retrying webhook (attempt {retries + 1}/{self.max_retries})")
                        return await self.send_webhook(webhook_url, event_type, payload, retries + 1)

                    return False

        except httpx.TimeoutException:
            logger.error(f"Webhook timeout for {webhook_url}")

            # Retry on timeout
            if retries < self.max_retries:
                logger.info(f"Retrying webhook (attempt {retries + 1}/{self.max_retries})")
                return await self.send_webhook(webhook_url, event_type, payload, retries + 1)

            return False

        except Exception as e:
            logger.error(f"Failed to send webhook to {webhook_url}: {str(e)}")
            return False

    async def send_job_completed(
        self,
        webhook_url: str,
        job_id: str,
        status: str,
        publisher_domain: str,
        target_url: str,
        **kwargs
    ) -> bool:
        """
        Send job completed webhook.

        Args:
            webhook_url: Target webhook URL
            job_id: Job ID
            status: Job status (delivered, blocked, aborted)
            publisher_domain: Publisher domain
            target_url: Target URL
            **kwargs: Additional payload data

        Returns:
            True if sent successfully
        """
        from datetime import datetime

        payload = {
            "job_id": job_id,
            "status": status,
            "publisher_domain": publisher_domain,
            "target_url": target_url,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        return await self.send_webhook(webhook_url, "job.completed", payload)

    async def send_job_error(
        self,
        webhook_url: str,
        job_id: str,
        publisher_domain: str,
        error_message: str,
        **kwargs
    ) -> bool:
        """
        Send job error webhook.

        Args:
            webhook_url: Target webhook URL
            job_id: Job ID
            publisher_domain: Publisher domain
            error_message: Error description
            **kwargs: Additional payload data

        Returns:
            True if sent successfully
        """
        from datetime import datetime

        payload = {
            "job_id": job_id,
            "publisher_domain": publisher_domain,
            "error_message": error_message,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }

        return await self.send_webhook(webhook_url, "job.error", payload)


# Global webhook service instance
webhook_service = WebhookService()
