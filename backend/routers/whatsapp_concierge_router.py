"""
WhatsApp Career Concierge Router
JobHunt Pro SaaS - Webhook endpoint for WhatsApp interactive messaging & voice interview assistant.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from core.whatsapp_career_concierge import whatsapp_concierge

router = APIRouter(prefix="/api/v2/whatsapp/concierge", tags=["WhatsApp AI Concierge"])


class WhatsAppIncomingWebhook(BaseModel):
    sender_phone: str = Field("+966501234567", description="Sender phone number with country code")
    message_body: str = Field("وظائف", description="Message text or transcript")
    message_type: Optional[str] = Field("text", description="text or audio")
    media_url: Optional[str] = Field(None, description="Optional audio file URL")


@router.post("/webhook")
def handle_whatsapp_webhook(req: WhatsAppIncomingWebhook):
    """Processes incoming WhatsApp messages and voice notes for job dispatch and interview coaching."""
    return whatsapp_concierge.process_incoming_message(
        sender_phone=req.sender_phone,
        message_body=req.message_body,
        message_type=req.message_type or "text",
        media_url=req.media_url
    )
