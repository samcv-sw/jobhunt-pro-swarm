"""
FastAPI Router exposing the 1000% God-Tier Suite endpoints.
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.auto_applier_swarm_v2 import auto_applier_swarm_v2
from core.ai_voice_interviewer import ai_voice_interviewer
from core.recruiter_notifier import recruiter_notifier
from core.ats_heatmap_engine import ats_heatmap_engine

router = APIRouter(prefix="/api/v2/god-tier", tags=["God-Tier Suite"])

class SwarmDispatchPayload(BaseModel):
    user_id: str
    target_role: str
    locations: List[str]
    platforms: Optional[List[str]] = None
    max_applications: int = 10

class InterviewAnalyzePayload(BaseModel):
    question: str
    transcript_text: str
    target_role: str = "software_engineer"
    language: str = "en"

class BroadcastPayload(BaseModel):
    user_id: str
    job_title: str
    company: str
    match_score: float = 95.0
    channels: Optional[List[str]] = None

class ATSOptimizePayload(BaseModel):
    resume_text: str
    target_job_description: Optional[str] = None

@router.post("/swarm/dispatch")
def dispatch_swarm_endpoint(payload: SwarmDispatchPayload) -> Dict[str, Any]:
    return auto_applier_swarm_v2.dispatch_swarm(
        user_id=payload.user_id,
        target_role=payload.target_role,
        locations=payload.locations,
        platforms=payload.platforms,
        max_applications=payload.max_applications
    )

@router.get("/swarm/telemetry")
def get_swarm_telemetry_endpoint() -> Dict[str, Any]:
    return auto_applier_swarm_v2.get_swarm_telemetry()

@router.post("/interview/analyze")
def analyze_interview_endpoint(payload: InterviewAnalyzePayload) -> Dict[str, Any]:
    return ai_voice_interviewer.analyze_response(
        question=payload.question,
        transcript_text=payload.transcript_text,
        target_role=payload.target_role,
        language=payload.language
    )

@router.post("/notifier/broadcast")
def broadcast_notification_endpoint(payload: BroadcastPayload) -> Dict[str, Any]:
    return recruiter_notifier.send_broadcast_notification(
        user_id=payload.user_id,
        job_title=payload.job_title,
        company=payload.company,
        match_score=payload.match_score,
        channels=payload.channels
    )

@router.post("/ats/heatmap")
def ats_heatmap_endpoint(payload: ATSOptimizePayload) -> Dict[str, Any]:
    return ats_heatmap_engine.generate_heatmap_and_optimize(
        resume_text=payload.resume_text,
        target_job_description=payload.target_job_description
    )
