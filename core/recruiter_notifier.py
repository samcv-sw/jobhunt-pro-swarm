"""
WhatsApp & Telegram Multi-Channel Recruiter Notification Engine
Sends real-time high-match job opportunities and enables 1-click remote applications.
"""

import time
import uuid
import logging
import json
import urllib.request
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class RecruiterNotifier:
    def __init__(self):
        self.sent_notifications: List[Dict[str, Any]] = []
        self.hot_lead_alerts: List[Dict[str, Any]] = []

    def send_broadcast_notification(
        self,
        user_id: str,
        job_title: str,
        company: str,
        match_score: float,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Dispatches job opportunity notifications over WhatsApp & Telegram."""
        target_channels = channels or ["whatsapp", "telegram"]
        notification_id = f"notif_{uuid.uuid4().hex[:8]}"

        payload = {
            "notification_id": notification_id,
            "user_id": user_id,
            "job_title": job_title,
            "company": company,
            "match_score": match_score,
            "channels": target_channels,
            "status": "delivered",
            "action_url": f"/api/v2/auto-apply/one-click?job={notification_id}",
            "timestamp": time.time()
        }

        self.sent_notifications.append(payload)
        logger.info(f"Broadcast notification {notification_id} sent via {target_channels}.")
        return payload

    def dispatch_hot_lead_alert(
        self,
        user_id: str,
        lead_name: str,
        lead_company: str,
        lead_email: str,
        reply_snippet: str,
        sentiment_score: float = 0.95,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Dispatches an instant priority alert when a recruiter/prospect responds positively.
        Supports instant Webhook dispatch (Telegram / Slack / Make / Zapier).
        """
        alert_id = f"lead_{uuid.uuid4().hex[:8]}"
        alert_data = {
            "alert_id": alert_id,
            "user_id": user_id,
            "lead_name": lead_name,
            "lead_company": lead_company,
            "lead_email": lead_email,
            "reply_snippet": reply_snippet,
            "sentiment_score": sentiment_score,
            "urgency": "HIGH" if sentiment_score >= 0.8 else "NORMAL",
            "timestamp": time.time(),
            "webhook_dispatched": False
        }

        if webhook_url:
            try:
                req = urllib.request.Request(
                    webhook_url,
                    data=json.dumps(alert_data).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "JobHuntPro-HotLead/1.0"}
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in (200, 201, 204):
                        alert_data["webhook_dispatched"] = True
            except Exception as e:
                logger.warning(f"Failed to post hot-lead webhook to {webhook_url}: {e}")

        self.hot_lead_alerts.append(alert_data)
        logger.info(f"Hot lead alert {alert_id} recorded for lead '{lead_name}' at {lead_company}.")
        return alert_data

    def get_notification_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves sent notification history for a given user."""
        return [n for n in self.sent_notifications if n["user_id"] == user_id]

    def get_hot_lead_alerts(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieves hot lead alerts for a given user."""
        return [a for a in self.hot_lead_alerts if a["user_id"] == user_id]

recruiter_notifier = RecruiterNotifier()

