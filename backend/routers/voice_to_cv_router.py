"""
Voice-to-CV Router
JobHunt Pro SaaS - REST endpoints for voice transcript to ATS resume transformation.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from core.voice_to_cv_engine import voice_to_cv_engine

router = APIRouter(prefix="/api/v2/voice-to-cv", tags=["Voice to CV Engine"])


class VoiceToCvRequest(BaseModel):
    candidate_name: str = Field("Candidate", description="Full name")
    voice_transcript: str = Field(..., min_length=5, description="Spoken voice transcript in Arabic or English")
    target_role: Optional[str] = Field("Enterprise Cloud Architect", description="Target role")
    contact_email: Optional[str] = Field("candidate@jobhunt-pro.com", description="Email")
    contact_phone: Optional[str] = Field("+966 50 000 0000", description="Phone")
    location: Optional[str] = Field("Riyadh, Saudi Arabia", description="Location")


@router.post("/generate")
def generate_cv_from_voice(req: VoiceToCvRequest):
    """Converts a spoken voice note transcript into a complete ATS-compliant resume."""
    return voice_to_cv_engine.convert_voice_transcript_to_cv(
        candidate_name=req.candidate_name,
        voice_transcript=req.voice_transcript,
        target_role=req.target_role,
        contact_email=req.contact_email,
        contact_phone=req.contact_phone,
        location=req.location or "Riyadh, Saudi Arabia"
    )
