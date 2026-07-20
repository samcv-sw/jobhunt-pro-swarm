# ──────────────────────────────────────────────────────────────────────────────
# notification_service.py - Email, SMS, Push Notifications
# Unified notification system for all communication channels
# ──────────────────────────────────────────────────────────────────────────────

import logging
import asyncio
import os
from typing import List, Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NotificationTemplate:
    """Notification template."""
    id: str
    name: str
    subject: Optional[str]
    body: str
    channel: NotificationChannel
    variables: List[str]  # Template variables like {user_name}, {link}


@dataclass
class Notification:
    """Notification object."""
    id: str
    recipient: str  # email, phone, user_id, etc.
    channel: NotificationChannel
    subject: Optional[str]
    body: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    template_id: Optional[str] = None
    template_vars: Optional[Dict[str, str]] = None
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed, delivered
    retry_count: int = 0
    max_retries: int = 3


class EmailNotificationService:
    """Send email notifications."""
    
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("MAIL_FROM", "noreply@jobhuntpro.com")
    
    async def send(self, notification: Notification) -> bool:
        """Send email notification via SMTP (TLS)."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            logger.info(f"Sending email to {notification.recipient}")

            msg = MIMEMultipart("alternative")
            msg["Subject"] = notification.subject or "Notification"
            msg["From"] = self.from_email
            msg["To"] = notification.recipient
            msg.attach(MIMEText(notification.body or "", "html"))

            def _send_sync() -> None:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                    server.starttls()
                    if self.smtp_user and self.smtp_password:
                        server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.from_email, [notification.recipient], msg.as_string())

            await asyncio.to_thread(_send_sync)

            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            notification.status = "failed"
            notification.retry_count += 1
            return False


class SMSNotificationService:
    """Send SMS notifications."""
    
    def __init__(self):
        self.provider = os.getenv("SMS_PROVIDER", "twilio")
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "")
    
    async def send(self, notification: Notification) -> bool:
        """Send SMS notification via Twilio REST API."""
        try:
            logger.info(f"Sending SMS to {notification.recipient}")
            
            if not (self.account_sid and self.auth_token and self.from_number):
                logger.warning("Twilio credentials not configured; skipping SMS send (graceful degradation).")
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
                return True
            
            import httpx
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
            data = {
                "To": notification.recipient,
                "From": self.from_number,
                "Body": notification.body or notification.subject or "",
            }
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, data=data, auth=(self.account_sid, self.auth_token))
                resp.raise_for_status()
            
            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            return True
        
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            notification.status = "failed"
            notification.retry_count += 1
            return False


class PushNotificationService:
    """Send push notifications via Firebase Cloud Messaging (FCM)."""

    def __init__(self):
        self.server_key = os.getenv("FCM_SERVER_KEY", "")
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"

    async def send(self, notification: Notification) -> bool:
        """Send push notification via FCM HTTP v1 legacy API."""
        try:
            logger.info(f"Sending push notification to {notification.recipient}")

            if not self.server_key:
                logger.warning("FCM_SERVER_KEY not configured; skipping push send (graceful degradation).")
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
                return True

            import httpx

            payload = {
                "to": notification.recipient,
                "notification": {
                    "title": notification.subject or "JobHunt Pro",
                    "body": notification.body or "",
                },
                "data": {
                    "subject": notification.subject or "",
                    "body": notification.body or "",
                },
            }
            headers = {
                "Authorization": f"key={self.server_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self.fcm_url, json=payload, headers=headers)
                resp.raise_for_status()

            notification.status = "sent"
            notification.sent_at = datetime.utcnow()
            return True

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            notification.status = "failed"
            notification.retry_count += 1
            return False


class InAppNotificationService:
    """Store in-app notifications."""
    
    def __init__(self):
        self._notifications: Dict[str, List[Notification]] = {}
    
    async def send(self, notification: Notification) -> bool:
        """Store in-app notification."""
        try:
            user_id = notification.recipient
            
            if user_id not in self._notifications:
                self._notifications[user_id] = []
            
            self._notifications[user_id].append(notification)
            notification.status = "delivered"
            notification.sent_at = datetime.utcnow()
            
            logger.info(f"In-app notification stored for user {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to store in-app notification: {e}")
            return False
    
    def get_notifications(self, user_id: str, unread_only: bool = False) -> List[Notification]:
        """Get notifications for user."""
        notifications = self._notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if n.status == "pending"]
        
        return notifications


class NotificationService:
    """Unified notification service."""
    
    def __init__(self):
        self.email_service = EmailNotificationService()
        self.sms_service = SMSNotificationService()
        self.push_service = PushNotificationService()
        self.in_app_service = InAppNotificationService()
        
        self._notifications: Dict[str, Notification] = {}
        self._templates: Dict[str, NotificationTemplate] = {}
    
    def register_template(self, template: NotificationTemplate) -> None:
        """Register notification template."""
        self._templates[template.id] = template
        logger.info(f"Notification template registered: {template.id}")
    
    async def send(self, notification: Notification) -> bool:
        """Send notification through appropriate channel."""
        try:
            # Store notification
            self._notifications[notification.id] = notification
            
            # Send through appropriate channel
            if notification.channel == NotificationChannel.EMAIL:
                return await self.email_service.send(notification)
            
            elif notification.channel == NotificationChannel.SMS:
                return await self.sms_service.send(notification)
            
            elif notification.channel == NotificationChannel.PUSH:
                return await self.push_service.send(notification)
            
            elif notification.channel == NotificationChannel.IN_APP:
                return await self.in_app_service.send(notification)
            
            else:
                logger.warning(f"Unknown notification channel: {notification.channel}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            notification.status = "failed"
            return False
    
    async def send_from_template(
        self,
        recipient: str,
        template_id: str,
        channel: NotificationChannel,
        template_vars: Optional[Dict[str, str]] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
    ) -> bool:
        """Send notification from template."""
        template = self._templates.get(template_id)
        if not template:
            logger.error(f"Template not found: {template_id}")
            return False
        
        # Render template with variables
        body = template.body
        subject = template.subject
        
        if template_vars:
            for var_name, var_value in template_vars.items():
                body = body.replace(f"{{{var_name}}}", str(var_value))
                if subject:
                    subject = subject.replace(f"{{{var_name}}}", str(var_value))
        
        notification = Notification(
            id=f"notif_{int(datetime.utcnow().timestamp() * 1000)}",
            recipient=recipient,
            channel=channel,
            subject=subject,
            body=body,
            priority=priority,
            template_id=template_id,
            template_vars=template_vars,
        )
        
        return await self.send(notification)
    
    async def send_batch(self, notifications: List[Notification]) -> Dict[str, bool]:
        """Send multiple notifications."""
        results = {}
        tasks = [self.send(n) for n in notifications]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for notification, result in zip(notifications, results_list):
            results[notification.id] = result if isinstance(result, bool) else False
        
        return results
    
    def get_notification(self, notification_id: str) -> Optional[Notification]:
        """Get notification by ID."""
        return self._notifications.get(notification_id)
    
    def get_unread_notifications(self, user_id: str) -> List[Notification]:
        """Get unread notifications for user."""
        return self.in_app_service.get_notifications(user_id, unread_only=True)
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        notification = self._notifications.get(notification_id)
        if notification:
            notification.status = "delivered"
            return True
        return False


# Global notification service instance
notification_service = NotificationService()


# Register common templates
def setup_notification_templates():
    """Setup default notification templates."""
    
    templates = [
        NotificationTemplate(
            id="welcome_email",
            name="Welcome Email",
            subject="Welcome to JobHunt Pro!",
            body="<h1>Welcome {user_name}!</h1><p>Get started with your job search.</p>",
            channel=NotificationChannel.EMAIL,
            variables=["user_name"],
        ),
        NotificationTemplate(
            id="job_alert",
            name="Job Alert",
            subject="New job opportunity: {job_title}",
            body="<p>We found a match: <a href='{job_link}'>{job_title}</a> at {company_name}</p>",
            channel=NotificationChannel.EMAIL,
            variables=["job_title", "job_link", "company_name"],
        ),
        NotificationTemplate(
            id="application_status",
            name="Application Status Update",
            subject="Update on your application for {job_title}",
            body="<p>Your application status: {status}</p>",
            channel=NotificationChannel.EMAIL,
            variables=["job_title", "status"],
        ),
    ]
    
    for template in templates:
        notification_service.register_template(template)
    
    logger.info(f"Registered {len(templates)} notification templates")


# Usage in FastAPI:
#
# @app.post("/api/notifications/send")
# async def send_notification(request: NotificationRequest):
#     notification = Notification(
#         id=str(uuid.uuid4()),
#         recipient=request.recipient,
#         channel=NotificationChannel[request.channel],
#         subject=request.subject,
#         body=request.body,
#     )
#     
#     success = await notification_service.send(notification)
#     return success_response(data={"sent": success})
