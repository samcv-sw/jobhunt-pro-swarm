"""
JobHunt Pro — LinkedIn Recruiter Algorithm Magnet Router
API endpoints to optimize candidate profile components for LinkedIn Recruiter search ranking.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.linkedin_recruiter_magnet import linkedin_recruiter_magnet

router = APIRouter(prefix="/api/v2/linkedin", tags=["LinkedIn Recruiter Magnet"])


class LinkedInOptimizationRequest(BaseModel):
    candidate_name: str = "Tariq Al-Mansoor"
    target_role: str = "Senior Cloud Architect"
    years_experience: int = 8
    skills: Optional[List[str]] = ["Python", "FastAPI", "Kubernetes", "AWS", "PostgreSQL", "Kafka"]
    key_achievements: Optional[List[str]] = [
        "Scaled fintech core engine to 10M daily transactions with sub-50ms latency.",
        "Saved $120k annually by refactoring cloud infrastructure to serverless event architecture."
    ]
    current_duties: Optional[List[str]] = [
        "Leading distributed engineering teams across Riyadh and Dubai",
        "Managing cloud security and automated CI/CD pipelines"
    ]
    target_city: str = "Riyadh & Dubai"


@router.post("/optimize-profile", response_model=Dict[str, Any])
def optimize_linkedin_profile(req: LinkedInOptimizationRequest) -> Dict[str, Any]:
    """Generate search-optimized headline, structured About section, and quantified experience bullets."""
    return linkedin_recruiter_magnet.full_profile_optimization(
        candidate_name=req.candidate_name,
        target_role=req.target_role,
        years_experience=req.years_experience,
        skills=req.skills,
        key_achievements=req.key_achievements,
        current_duties=req.current_duties,
        target_city=req.target_city
    )
