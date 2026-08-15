"""
AI Headhunter Dossier Router
JobHunt Pro SaaS - Endpoints for creating confidential executive dossiers for executive search agencies.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

from core.headhunter_executive_dossier import headhunter_dossier

router = APIRouter(prefix="/api/v2/headhunter/dossier", tags=["AI Headhunter Dossier"])


class DossierGenerationRequest(BaseModel):
    candidate_code: str = Field("EXECUTIVE-C902", description="Blind code to preserve candidate confidentiality")
    executive_title: str = Field("Chief Technology Officer", description="C-level / VP title")
    years_leadership: int = Field(12, ge=5, le=40)
    primary_domain: Optional[str] = Field("High-Scale Cloud & AI Enterprise Transformation")
    target_compensation_sar: Optional[float] = Field(65000.0, gt=10000.0)
    core_strengths: Optional[List[str]] = Field(None)


@router.post("/generate")
def create_executive_dossier(req: DossierGenerationRequest):
    """Generates a boardroom-ready confidential executive dossier for headhunters and recruiters."""
    return headhunter_dossier.generate_executive_dossier(
        candidate_code=req.candidate_code,
        executive_title=req.executive_title,
        years_leadership=req.years_leadership,
        primary_domain=req.primary_domain or "Enterprise Technology Leadership",
        target_compensation_sar=req.target_compensation_sar or 65000.0,
        core_strengths=req.core_strengths
    )
