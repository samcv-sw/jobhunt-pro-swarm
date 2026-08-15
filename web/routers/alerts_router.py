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


class HotLeadAlertRequest(BaseModel):
    user_id: str = "user_default"
    lead_name: str
    lead_company: str
    lead_email: str
    reply_snippet: str
    sentiment_score: Optional[float] = 0.95
    webhook_url: Optional[str] = None


@router.post("/hot-lead")
def trigger_hot_lead_alert(req: HotLeadAlertRequest):
    """Triggers an instant priority notification (Telegram/WhatsApp/Webhook)
    when a high-intent recruiter or client reply is detected.
    """
    from core.recruiter_notifier import recruiter_notifier
    result = recruiter_notifier.dispatch_hot_lead_alert(
        user_id=req.user_id,
        lead_name=req.lead_name,
        lead_company=req.lead_company,
        lead_email=req.lead_email,
        reply_snippet=req.reply_snippet,
        sentiment_score=req.sentiment_score or 0.95,
        webhook_url=req.webhook_url
    )
    return {
        "status": "success",
        "alert": result
    }


@router.get("/hot-lead/history")
def get_user_hot_leads(user_id: str = "user_default"):
    """Fetches user hot lead response history."""
    from core.recruiter_notifier import recruiter_notifier
    alerts = recruiter_notifier.get_hot_lead_alerts(user_id)
    return {"status": "success", "user_id": user_id, "total": len(alerts), "alerts": alerts}

