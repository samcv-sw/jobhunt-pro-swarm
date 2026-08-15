"""
AI Video Pitch Router
JobHunt Pro SaaS - REST endpoints for generating cinematic 45-second video resume scripts and scene directions.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from core.ai_video_pitch_engine import ai_video_pitch_engine

router = APIRouter(prefix="/api/v2/video-pitch", tags=["AI Video Elevator Pitch"])


class VideoPitchRequest(BaseModel):
    candidate_name: str = Field("Samir Atou", description="Candidate full name")
    current_title: str = Field("Principal Cloud Architect", description="Current or target title")
    key_achievement: Optional[str] = Field("Scaled distributed microservices to 100k req/sec while cutting cloud bill by 35%")
    target_company_type: Optional[str] = Field("Saudi Vision 2030 / UAE Enterprise Scale-ups")
    duration_seconds: Optional[int] = Field(45, ge=30, le=120)


@router.post("/generate")
def create_video_pitch_script(req: VideoPitchRequest):
    """Generates 4-scene video script with pacing, camera directions, and overlays."""
    return ai_video_pitch_engine.generate_pitch_package(
        candidate_name=req.candidate_name,
        current_title=req.current_title,
        key_achievement=req.key_achievement or "Engineered high-scale systems",
        target_company_type=req.target_company_type or "GCC Enterprise",
        duration_seconds=req.duration_seconds or 45
    )
