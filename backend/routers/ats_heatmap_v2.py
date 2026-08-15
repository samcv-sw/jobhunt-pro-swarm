"""
ATS Heatmap V2 Router
Provides endpoints for dual-language ATS scoring, interactive visual heatmap generation,
and PDF XMP metadata tag generation.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.ats_dual_heatmap_sculptor import ats_dual_heatmap_sculptor

router = APIRouter(prefix="/api/ats-heatmap-v2", tags=["ATS Heatmap V2"])

class ATSScoreRequest(BaseModel):
    cv_text: str = Field(..., example="Senior Software Engineer with expertise in Python, FastAPI, Docker, and PostgreSQL.")
    jd_text: str = Field(..., example="Seeking Senior Software Engineer with Python, FastAPI, Kubernetes, Docker, Redis, and PostgreSQL.")
    is_arabic: bool = Field(False, example=False)

class MetadataInjectRequest(BaseModel):
    candidate_name: str = Field("Sami Mansour", example="Sami Mansour")
    target_role: str = Field("Senior Cloud Architect", example="Senior Cloud Architect")
    keywords: List[str] = Field(..., example=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "AWS"])

@router.post("/score-and-heatmap")
def score_cv_and_generate_heatmap(req: ATSScoreRequest) -> Dict[str, Any]:
    """Calculate dual-language ATS score and return keyword density heatmap nodes."""
    return ats_dual_heatmap_sculptor.analyze_dual_ats(
        cv_text=req.cv_text,
        jd_text=req.jd_text,
        is_arabic=req.is_arabic
    )

@router.post("/generate-xmp-metadata")
def generate_xmp_metadata(req: MetadataInjectRequest) -> Dict[str, Any]:
    """Generate stealth XMP XML metadata tags for PDF/DOCX indexing."""
    return ats_dual_heatmap_sculptor.generate_stealth_xmp_metadata(
        candidate_name=req.candidate_name,
        target_role=req.target_role,
        keywords=req.keywords
    )
