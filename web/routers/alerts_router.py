"""
Web Router for Observability Alerts & Notifications
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from core.alerts_engine import alerts_engine

router = APIRouter(prefix="/alerts", tags=["Swarm Alerts & Observability"])

class AlertDispatchRequest(BaseModel):
    channel: str = Field(..., description="telegram | slack")
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None
    webhook_url: Optional[str] = None
    message: str

@router.post("/send")
async def dispatch_alert(req: AlertDispatchRequest):
    """
    Dispatches a real-time notification alert to Telegram or Slack.
    """
    channel = req.channel.lower()
    if channel == "telegram":
        res = alerts_engine.send_telegram_alert(req.bot_token or "", req.chat_id or "", req.message)
    elif channel == "slack":
        res = alerts_engine.send_slack_alert(req.webhook_url or "", req.message)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported alert channel: {channel}")

    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Dispatch failed"))
    return res
