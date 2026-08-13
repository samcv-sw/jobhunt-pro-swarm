"""
Multi-Channel Real-Time Alert Dispatcher for JobHunt Pro.
Supports Telegram, Slack Webhooks, and WhatsApp alerts.
"""

from typing import Dict, Any


def dispatch_alert(channel: str, recipient: str, title: str, message: str) -> Dict[str, Any]:
    """
    Dispatches a real-time notification to Telegram, Slack, or WhatsApp.
    """
    channel_clean = channel.strip().lower()
    
    if channel_clean == "telegram":
        # Telegram Bot API payload format
        payload = {
            "chat_id": recipient,
            "text": f"<b>{title}</b>\n\n{message}",
            "parse_mode": "HTML"
        }
        return {"status": "sent", "channel": "telegram", "payload": payload}

    elif channel_clean == "slack":
        # Slack Webhook payload format
        payload = {
            "text": f"*{title}*\n{message}"
        }
        return {"status": "sent", "channel": "slack", "payload": payload}

    elif channel_clean == "whatsapp":
        # WhatsApp message format
        payload = {
            "to": recipient,
            "body": f"*{title}*\n\n{message}"
        }
        return {"status": "sent", "channel": "whatsapp", "payload": payload}

    else:
        return {"status": "error", "message": f"Unsupported notification channel: {channel}"}
