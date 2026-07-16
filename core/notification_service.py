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

from core.email_engine import send_email_via_brevo_http

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
        """Send email notification."""
        try:
            logger.info(f"Sending email to {notification.recipient}")

            # Send via real email engine (Brevo HTTP / Gmail SMTP fallback)
            sent = send_email_via_brevo_http(
                to_email=notification.recipient,
                custom_body=notification.body,
                subject=notification.subject or "Notification",
                sender_name=self.from_email,
            )

            if sent:
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
                return True

            notification.status = "failed"
            notification.retry_count += 1
            return False
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            notification.status = "failed"
            notification.retry_count += 1
            return False


class SMSNotificationService:
    """Send SMS notifications."""
    
    def __init__(self):
        self.provider = os.getenv("SMS_PROVIDER", "twilio")
        self.api_key = os.getenv("SMS_API_KEY", "")
    
    async def send(self, notification: Notification) -> bool:
        """Send SMS notification via Twilio/Nexmo REST API."""
        try:
            logger.info(f"Sending SMS to {notification.recipient}")

            provider = self.provider
            api_key = self.api_key
            if not api_key:
                logger.warning("SMS_API_KEY not configured; cannot send SMS")
                notification.status = "failed"
                notification.retry_count += 1
                return False

            if provider == "twilio":
                account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
                auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
                from_number = os.getenv("TWILIO_FROM_NUMBER", "")
                if not (account_sid and auth_token and from_number):
                    logger.warning("Twilio credentials incomplete; cannot send SMS")
                    notification.status = "failed"
                    notification.retry_count += 1
                    return False
                import httpx
                url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
                data = {
                    "To": notification.recipient,
                    "From": from_number,
                    "Body": notification.body,
                }
                resp = httpx.post(url, data=data, auth=(account_sid, auth_token), timeout=15)
                if resp.status_code in (200, 201, 202):
                    notification.status = "sent"
                    notification.sent_at = datetime.utcnow()
                    return True
                logger.error(f"Twilio SMS failed: {resp.status_code} {resp.text[:200]}")
            else:
                # Nexmo / Vonage
                import httpx
                url = "https://rest.nexmo.com/sms/json"
                params = {
                    "api_key": os.getenv("NEXMO_API_KEY", ""),
                    "api_secret": os.getenv("NEXMO_API_SECRET", ""),
                    "to": notification.recipient,
                    "from": os.getenv("NEXMO_FROM", "JobHuntPro"),
                    "text": notification.body,
                }
                resp = httpx.post(url, params=params, timeout=15)
                if resp.status_code == 200 and resp.json().get("messages", [{}])[0].get("status") == "0":
                    notification.status = "sent"
                    notification.sent_at = datetime.utcnow()
                    return True
                logger.error(f"Nexmo SMS failed: {resp.status_code} {resp.text[:200]}")

            notification.status = "failed"
            notification.retry_count += 1
            return False

        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            notification.status = "failed"
            notification.retry_count += 1
            return False


class PushNotificationService:
    """Send push notifications."""
    
    async def send(self, notification: Notification) -> bool:
        """Send push notification via FCM HTTP API."""
        try:
            logger.info(f"Sending push notification to {notification.recipient}")

            fcm_server_key = os.getenv("FCM_SERVER_KEY", "")
            if not fcm_server_key:
                logger.warning("FCM_SERVER_KEY not configured; cannot send push")
                notification.status = "failed"
                notification.retry_count += 1
                return False

            import httpx
            url = "https://fcm.googleapis.com/fcm/send"
            headers = {
                "Authorization": f"key={fcm_server_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "to": notification.recipient,
                "notification": {
                    "title": notification.subject or "JobHunt Pro",
                    "body": notification.body,
                },
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=15)
            if resp.status_code == 200:
                notification.status = "sent"
                notification.sent_at = datetime.utcnow()
                return True
            logger.error(f"FCM push failed: {resp.status_code} {resp.text[:200]}")
            notification.status = "failed"
            notification.retry_count += 1
            return False

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
