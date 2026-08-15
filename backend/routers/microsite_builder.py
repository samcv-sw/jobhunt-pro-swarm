"""
JobHunt Pro — Executive Microsite & Pitch Generator Router
API endpoints to generate luxury glassmorphic portfolio microsites and 60-second video elevator pitch scripts.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.executive_microsite_builder import executive_microsite_builder

router = APIRouter(prefix="/api/v2/microsite", tags=["Executive Microsite Builder"])


class MicrositeGenerateRequest(BaseModel):
    candidate_name: str = "Samir Haddad"
    role_title: str = "Principal Solutions Architect"
    years_experience: int = 8
    core_strength: str = "Cloud Scalability & Microservices"
    skills: Optional[List[str]] = ["Python", "FastAPI", "Kubernetes", "PostgreSQL", "AWS", "System Design"]
    ats_score: int = 96


@router.post("/generate", response_model=Dict[str, Any])
def generate_candidate_microsite(req: MicrositeGenerateRequest) -> Dict[str, Any]:
    """Generate portfolio microsite link, QR code, video elevator pitch, and glassmorphic HTML."""
    return executive_microsite_builder.generate_microsite_package(
        candidate_name=req.candidate_name,
        role_title=req.role_title,
        years_exp=req.years_experience,
        core_strength=req.core_strength,
        skills=req.skills,
        ats_score=req.ats_score
    )
