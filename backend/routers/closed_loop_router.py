"""
FastAPI Router for Closed-Loop AI Calendar & Email Negotiator.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any
from core.closed_loop_negotiator import closed_loop_negotiator

router = APIRouter(prefix="/api/v1/closed-loop", tags=["Closed-Loop Negotiator"])

class RecruiterEmailPayload(BaseModel):
    email_body: str
    sender_email: str

@router.post("/incoming-email")
async def handle_incoming_email(payload: RecruiterEmailPayload):
    """
    Handles recruiter email payload, parses intent, and returns negotiated schedule reply.
    """
    try:
        parsed = closed_loop_negotiator.parse_incoming_email(payload.email_body)
        negotiated = closed_loop_negotiator.negotiate_slots(parsed)
        return {
            "status": "success",
            "parsed_metadata": parsed,
            "negotiated_response": negotiated
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar-slots")
async def get_available_slots():
    """
    Returns available calendar scheduling slots.
    """
    return {
        "status": "success",
        "owner": closed_loop_negotiator.calendar_owner,
        "available_days": closed_loop_negotiator.available_days,
        "available_slots": closed_loop_negotiator.slots
    }
