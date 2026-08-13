"""
JobHunt Pro SaaS — Voice SDR Router (v2026.1)
FastAPI Router for Voice AI SDR Outbound Lead Qualification & Call Webhooks.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from core.voice_sdr_agent import CallState, LeadDisposition, voice_sdr_agent

router = APIRouter(prefix="/api/voice-sdr", tags=["Voice SDR"])


class DispatchCallRequest(BaseModel):
    lead_phone: str
    lead_name: str
    company_name: str
    target_role: str = "Software Engineer"
    language: str = "en"
    provider: str = "elevenlabs_webrtc"


class CallStatusUpdateRequest(BaseModel):
    call_id: str
    state: str
    disposition: Optional[str] = None
    duration_seconds: int = 0


@router.post("/dispatch")
async def dispatch_voice_call(payload: DispatchCallRequest):
    """Dispatches outbound Voice AI call to candidate or company decision maker."""
    if not payload.lead_phone or not payload.lead_name:
        raise HTTPException(status_code=400, detail="lead_phone and lead_name are required.")

    result = await voice_sdr_agent.dispatch_call(
        lead_phone=payload.lead_phone,
        lead_name=payload.lead_name,
        company_name=payload.company_name,
        target_role=payload.target_role,
        language=payload.language,
        provider=payload.provider,
    )
    return result


@router.post("/webhook")
async def voice_call_webhook(request: Request):
    """Processes real-time callbacks from telephony / WebRTC providers."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    call_id = body.get("call_id")
    state_str = body.get("state", "completed")
    disposition_str = body.get("disposition")
    duration = int(body.get("duration", 0))

    if not call_id:
        return {"status": "ignored", "reason": "No call_id provided"}

    try:
        new_state = CallState(state_str)
    except ValueError:
        new_state = CallState.COMPLETED

    disposition = None
    if disposition_str:
        try:
            disposition = LeadDisposition(disposition_str)
        except ValueError:
            disposition = LeadDisposition.QUALIFIED

    result = voice_sdr_agent.update_call_state(
        call_id=call_id,
        new_state=new_state,
        disposition=disposition,
        duration_seconds=duration,
    )
    return result


@router.get("/status/{call_id}")
async def get_call_status(call_id: str):
    """Fetches details, current state, and disposition of a voice call."""
    status = voice_sdr_agent.get_call_status(call_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Call ID {call_id} not found.")
    return status


@router.get("/recent")
async def list_recent_calls(limit: int = Query(default=20, ge=1, le=100)):
    """Lists recent SDR calls and qualifications."""
    return {"calls": voice_sdr_agent.list_recent_calls(limit=limit)}


class WebRTCVoiceScriptRequest(BaseModel):
    call_id: str
    transcript_snippet: str
    calendar_link: Optional[str] = "https://calendly.com/user/demo"

@router.post("/webrtc/process-speech")
async def process_webrtc_speech_stream(req: WebRTCVoiceScriptRequest):
    """
    Real-time WebRTC AI Speech Processor: analyzes prospect spoken input over phone/browser
    and returns next vocal script line and calendar booking link.
    """
    text_lower = req.transcript_snippet.lower()
    
    if any(w in text_lower for w in ["yes", "schedule", "book", "available"]):
        next_response = f"Awesome! I have just sent a calendar invite link to your phone: {req.calendar_link}. Looking forward to speaking with you!"
        action = "BOOK_CALENDAR"
    elif any(w in text_lower for w in ["price", "cost", "how much"]):
        next_response = "Our plans start at just $49/mo for 500 AI credits, fully equipped with automated MX deliverability protection."
        action = "ANSWER_PRICING"
    else:
        next_response = "I completely understand. Would a quick 5-minute overview on Tuesday work best for your schedule?"
        action = "QUALIFY_LEAD"

    return {
        "status": "success",
        "call_id": req.call_id,
        "transcript_received": req.transcript_snippet,
        "action": action,
        "ai_spoken_response": next_response,
        "calendar_link": req.calendar_link
    }

