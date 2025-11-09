"""
Email notification service using aiosmtplib.

Sends email notifications for job completion, errors, and other events.
"""

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
from typing import Optional, Dict, Any
import os
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending notifications.

    Supports HTML email templates with Jinja2.
    """

    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "notifications@bacowr.local")
        self.from_name = os.getenv("SMTP_FROM_NAME", "BACOWR")

        # Setup Jinja2 for email templates
        template_dir = Path(__file__).parent / "templates"
        template_dir.mkdir(exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml'])
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Add text version
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML version
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username if self.smtp_username else None,
                password=self.smtp_password if self.smtp_password else None,
                use_tls=self.smtp_use_tls
            )

            logger.info(f"Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render email template with context.

        Args:
            template_name: Template file name (e.g., "job_completed.html")
            context: Template variables

        Returns:
            Rendered HTML content
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {str(e)}")
            return ""

    async def send_job_completed(
        self,
        to_email: str,
        job_id: str,
        publisher_domain: str,
        target_url: str,
        status: str,
        **kwargs
    ) -> bool:
        """
        Send job completion notification.

        Args:
            to_email: Recipient email
            job_id: Job ID
            publisher_domain: Publisher domain
            target_url: Target URL
            status: Job status (delivered, blocked, aborted)
            **kwargs: Additional template variables

        Returns:
            True if sent successfully
        """
        context = {
            "job_id": job_id,
            "publisher_domain": publisher_domain,
            "target_url": target_url,
            "status": status,
            "dashboard_url": os.getenv("FRONTEND_URL", "http://localhost:3000"),
            **kwargs
        }

        html_content = self.render_template("job_completed.html", context)

        # Fallback text version
        text_content = f"""
BACOWR Job Completed

Job ID: {job_id}
Publisher: {publisher_domain}
Target URL: {target_url}
Status: {status}

View in dashboard: {context['dashboard_url']}/jobs/{job_id}
        """.strip()

        subject = f"BACOWR Job {status.upper()}: {publisher_domain}"

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_job_error(
        self,
        to_email: str,
        job_id: str,
        publisher_domain: str,
        error_message: str,
        **kwargs
    ) -> bool:
        """
        Send job error notification.

        Args:
            to_email: Recipient email
            job_id: Job ID
            publisher_domain: Publisher domain
            error_message: Error description
            **kwargs: Additional template variables

        Returns:
            True if sent successfully
        """
        context = {
            "job_id": job_id,
            "publisher_domain": publisher_domain,
            "error_message": error_message,
            "dashboard_url": os.getenv("FRONTEND_URL", "http://localhost:3000"),
            **kwargs
        }

        html_content = self.render_template("job_error.html", context)

        # Fallback text version
        text_content = f"""
BACOWR Job Error

Job ID: {job_id}
Publisher: {publisher_domain}
Error: {error_message}

View in dashboard: {context['dashboard_url']}/jobs/{job_id}
        """.strip()

        subject = f"BACOWR Job Error: {publisher_domain}"

        return await self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()
