"""
Real-Time Push & Telegram Webhook Engine — GOD-MODE Module
Handles instant Telegram Bot push notifications for payment confirmations,
candidate applications, referral reward payouts, and system alerts.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
import httpx
from config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/telegram-push", tags=["telegram_push"])

async def dispatch_telegram_message(chat_id: str, text: str, parse_mode: str = "HTML"):
    """Dispatches a push notification via Telegram Bot API."""
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured; logging message locally.")
        logger.info(f"Notification to {chat_id}: {text}")
        return True

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode
    }
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        logger.error(f"Failed to dispatch Telegram message: {e}")
        return False

@router.post("/send")
async def send_push_notification(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """API Endpoint to trigger a push notification to a Telegram user."""
    chat_id = payload.get("chat_id")
    message = payload.get("message")
    if not chat_id or not message:
        raise HTTPException(status_code=400, detail="chat_id and message are required.")

    background_tasks.add_task(dispatch_telegram_message, str(chat_id), str(message))
    return {"status": "queued", "chat_id": chat_id}

@router.post("/broadcast-job")
async def broadcast_job_alert(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Broadcast a rich job alert to a Telegram channel or user with 1-click apply link.
    """
    chat_id = payload.get("chat_id", "@jobhuntpro_alerts")
    job_title = payload.get("title", "Senior Software Engineer")
    company = payload.get("company", "Tech Global")
    location = payload.get("location", "Remote / Gulf Region")
    salary = payload.get("salary", "$4,500 - $7,000 / month")
    apply_url = payload.get("apply_url", "https://t.me/JobHuntProBot/app")
    
    formatted_msg = (
        f"🎯 <b>NEW MATCHED JOB ALERT</b>\n\n"
        f"💼 <b>Role:</b> {job_title}\n"
        f"🏢 <b>Company:</b> {company}\n"
        f"📍 <b>Location:</b> {location}\n"
        f"💰 <b>Salary:</b> {salary}\n\n"
        f"⚡ <i>Tap below to auto-apply with your tailored CV!</i>\n"
        f"👉 <a href='{apply_url}'>Apply via Telegram Mini App</a>"
    )
    
    background_tasks.add_task(dispatch_telegram_message, str(chat_id), formatted_msg)
    return {
        "status": "success",
        "chat_id": chat_id,
        "job_title": job_title,
        "message": "Job alert broadcast queued successfully."
    }

