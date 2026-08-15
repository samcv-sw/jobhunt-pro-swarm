"""
WebRTC Interview Copilot Router
Provides endpoints for creating real-time interview HUD sessions,
streaming transcript frame analysis, and computing BATNA salary negotiation plans.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.webrtc_interview_copilot import webrtc_interview_copilot

router = APIRouter(prefix="/api/webrtc-copilot", tags=["WebRTC Interview Copilot"])

class SessionCreateRequest(BaseModel):
    candidate_name: str = Field("Sami", example="Sami")
    target_role: str = Field("Senior Software Engineer", example="Senior Software Engineer")
    company: str = Field("Careem", example="Careem")

class TranscriptFrameRequest(BaseModel):
    session_id: str = Field(..., example="webrtc_a1b2c3d4e5f6")
    interviewer_question: str = Field(..., example="Tell me about a time you had a technical disagreement with your team lead.")

class NegotiationRequest(BaseModel):
    role_key: str = Field("senior_software_engineer", example="senior_software_engineer")
    initial_offer: float = Field(30000.0, example=30000.0)
    has_competing_offer: bool = Field(True, example=True)

@router.post("/create-session")
def create_webrtc_session(req: SessionCreateRequest) -> Dict[str, Any]:
    """Start a real-time WebRTC coaching HUD session."""
    return webrtc_interview_copilot.create_session(
        candidate_name=req.candidate_name,
        target_role=req.target_role,
        company=req.company
    )

@router.post("/process-transcript")
def process_transcript_frame(req: TranscriptFrameRequest) -> Dict[str, Any]:
    """Analyze interviewer speech and stream instant coaching points."""
    return webrtc_interview_copilot.process_live_transcript_frame(
        session_id=req.session_id,
        interviewer_question=req.interviewer_question
    )

@router.post("/calculate-batna")
def calculate_batna(req: NegotiationRequest) -> Dict[str, Any]:
    """Compute game-theoretic counter-offer and negotiation script."""
    return webrtc_interview_copilot.compute_batna_negotiation(
        role_key=req.role_key,
        initial_offer=req.initial_offer,
        has_competing_offer=req.has_competing_offer
    )
