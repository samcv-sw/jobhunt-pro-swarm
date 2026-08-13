"""
Real-Time Notifications Router for JobHunt Pro.
"""

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any
from core.alerts import dispatch_alert

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

@router.post("/send-alert")
async def send_notification_alert(payload: Dict[str, Any] = Body(...)):
    """Sends a real-time notification via Telegram, Slack, or WhatsApp."""
    channel = payload.get("channel")
    recipient = payload.get("recipient")
    title = payload.get("title", "JobHunt Pro Alert")
    message = payload.get("message", "New lead reply received!")

    if not channel or not recipient:
        raise HTTPException(status_code=400, detail="Channel and recipient parameters are required.")

    result = dispatch_alert(channel=channel, recipient=recipient, title=title, message=message)
    return result
