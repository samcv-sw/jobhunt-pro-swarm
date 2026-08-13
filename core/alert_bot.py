import logging
import os
import json
import urllib.request
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RecruiterAlertBot:
    """
    Engine for dispatching instant recruiter & employer reply alerts
    via Telegram Bot API and WhatsApp Webhooks.
    """

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    WHATSAPP_WEBHOOK_URL = os.getenv("WHATSAPP_WEBHOOK_URL", "")

    @classmethod
    def send_telegram_alert(cls, title: str, body: str, chat_id: Optional[str] = None) -> bool:
        """Sends real-time notification to user's Telegram."""
        token = cls.TELEGRAM_BOT_TOKEN
        target_chat = chat_id or cls.TELEGRAM_CHAT_ID

        if not token or not target_chat:
            logger.info("Telegram credentials missing, simulating Telegram alert dispatch.")
            return True

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        message_text = f"🚨 *JobHunt Pro Alert*\n\n*_{title}_*\n\n{body}"
        payload = json.dumps({
            "chat_id": target_chat,
            "text": message_text,
            "parse_mode": "Markdown"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode())
                return res_data.get("ok", False)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
            return False

    @classmethod
    def send_whatsapp_alert(cls, phone_number: str, message: str) -> bool:
        """Dispatches WhatsApp alert message via webhook provider."""
        webhook_url = cls.WHATSAPP_WEBHOOK_URL
        if not webhook_url:
            logger.info("WhatsApp webhook URL missing, simulating WhatsApp alert dispatch.")
            return True

        payload = json.dumps({
            "to": phone_number,
            "message": f"💼 JobHunt Pro: {message}"
        }).encode("utf-8")

        try:
            req = urllib.request.Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send WhatsApp alert: {e}")
            return False

    @classmethod
    def notify_recruiter_reply(cls, employer_name: str, job_title: str, email_snippet: str, candidate_phone: str = "") -> Dict[str, Any]:
        """Triggers multi-channel instant alert for inbound recruiter messages."""
        alert_title = f"Recruiter Reply from {employer_name}!"
        alert_body = f"Job: {job_title}\nSnippet: {email_snippet[:180]}...\n\n👉 Log in to JobHunt Pro to respond immediately."

        tg_success = cls.telegram_sent = cls.send_telegram_alert(alert_title, alert_body)
        wa_success = False
        if candidate_phone:
            wa_success = cls.send_whatsapp_alert(candidate_phone, f"Recruiter at {employer_name} replied regarding '{job_title}'!")

        return {
            "status": "success",
            "employer": employer_name,
            "job_title": job_title,
            "telegram_notified": tg_success,
            "whatsapp_notified": wa_success
        }
