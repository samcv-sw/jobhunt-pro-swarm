"""
FastAPI router for PWA Web Push Notifications and Manifest management.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.push_notifier import push_notification_engine

router = APIRouter(prefix="/api/v2/pwa-push", tags=["PWA & Web Push"])

class SubscribeRequest(BaseModel):
    endpoint: str
    keys: Dict[str, str]
    user_id: Optional[str] = "default_user"

class PushTriggerRequest(BaseModel):
    title: str = "🎯 Job Match Found!"
    body: str = "A top tier Senior Engineer role matched your ATS profile 98%."
    url: Optional[str] = "/dashboard"

@router.post("/subscribe")
async def subscribe_push(req: SubscribeRequest):
    return push_notification_engine.register_subscription(req.endpoint, req.keys, req.user_id or "default_user")

@router.post("/send-alert")
async def send_push_notification(req: PushTriggerRequest):
    return push_notification_engine.send_push_alert(req.title, req.body, req.url or "/dashboard")
