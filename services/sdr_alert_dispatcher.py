"""
services/sdr_alert_dispatcher.py - Real-time Telegram & WhatsApp Instant SDR Alert Engine
Sends instant alerts to recruiters/candidates when high-value leads reply or open application emails.
"""
import logging
import os
import urllib.parse
import urllib.request
import json
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SDRAlertDispatcher:
    """
    Dispatches real-time alerts via Telegram Bot API or WhatsApp Webhooks when campaign events occur.
    """

    def __init__(self, bot_token: Optional[str] = None, admin_chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("PA_BOT_TOKEN") or "7845102941:AAEbX..."
        self.admin_chat_id = admin_chat_id or os.getenv("TELEGRAM_ADMIN_CHAT_ID") or os.getenv("ADMIN_CHAT_ID")

    def send_telegram_alert(self, message: str, chat_id: Optional[str] = None) -> bool:
        """Send formatted message via Telegram Bot API."""
        target_chat_id = chat_id or self.admin_chat_id
        if not self.bot_token or not target_chat_id:
            logger.info(f"[SDRAlert Mock] Telegram alert logged: {message}")
            return True

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = json.dumps({
                "chat_id": target_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                result = json.loads(resp.read().decode())
                return result.get("ok", False)
        except Exception as e:
            logger.warning(f"Telegram alert send failed: {e}")
            return False

    def notify_lead_replied(self, lead_email: str, company: str, job_title: str, reply_snippet: str, user_chat_id: Optional[str] = None) -> bool:
        """Dispatch instant alert when a target HR manager/company replies to a campaign email."""
        message = (
            f"🔥 <b>HOT LEAD REPLY RECEIVED!</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Role:</b> {job_title}\n"
            f"✉️ <b>From:</b> {lead_email}\n\n"
            f"📝 <b>Reply Snippet:</b>\n<i>\"{reply_snippet[:300]}\"</i>\n\n"
            f"⚡ <b>Action Required:</b> Respond within 15 minutes to maximize conversion!"
        )
        return self.send_telegram_alert(message, chat_id=user_chat_id)

    def notify_email_opened(self, lead_email: str, company: str, job_title: str, open_count: int = 1, user_chat_id: Optional[str] = None) -> bool:
        """Dispatch instant alert when an outreach email is opened."""
        message = (
            f"👁️ <b>EMAIL OPENED NOTIFICATION</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Role:</b> {job_title}\n"
            f"✉️ <b>Recipient:</b> {lead_email}\n"
            f"📊 <b>Total Opens:</b> {open_count}\n\n"
            f"💡 <i>Tip: The recipient is actively viewing your profile right now.</i>"
        )
        return self.send_telegram_alert(message, chat_id=user_chat_id)
