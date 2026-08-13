"""
Autonomous Swarm Observability & Real-Time Alert Engine
Dispatches Slack, Telegram, and Webhook notifications for swarm events.
"""

import json
import time
import urllib.request
from typing import Dict, Any, Optional

class AlertsEngine:
    def __init__(self):
        pass

    def send_telegram_alert(self, bot_token: str, chat_id: str, message: str) -> Dict[str, Any]:
        """
        Sends real-time notification to Telegram channel/group.
        """
        if not bot_token or not chat_id:
            return {"success": False, "error": "Telegram Bot Token or Chat ID missing"}

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"success": True, "channel": "telegram", "sent_at": time.time()}
        except Exception as e:
            return {"success": False, "channel": "telegram", "error": str(e)}

    def send_slack_alert(self, webhook_url: str, message: str) -> Dict[str, Any]:
        """
        Sends real-time notification to Slack webhook channel.
        """
        if not webhook_url:
            return {"success": False, "error": "Slack webhook URL missing"}

        payload = {
            "text": f"🚀 <b>JobHunt Pro Swarm Alert</b>\n{message}"
        }
        body_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=body_bytes,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"success": True, "channel": "slack", "sent_at": time.time()}
        except Exception as e:
            return {"success": False, "channel": "slack", "error": str(e)}

alerts_engine = AlertsEngine()
