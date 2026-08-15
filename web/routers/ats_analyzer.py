"""
Real-Time Live ATS Resume Analyzer & PDF Preview Data Router for JobHunt Pro.
Calculates keyword density, formatting compliance, section coverage, and overall ATS score (0-100).
"""

import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List

router = APIRouter(prefix="/api/ats", tags=["ATS Analyzer"])


class ATSAnalysisRequest(BaseModel):
    resume_text: str = Field(..., description="Raw text of the resume")
    job_description: str = Field(..., description="Target job description text")


@router.post("/score")
def calculate_ats_score(req: ATSAnalysisRequest) -> Dict[str, Any]:
    """Calculates granular ATS optimization metrics and overall score."""
    if not req.resume_text.strip() or not req.job_description.strip():
        raise HTTPException(status_code=400, detail="Resume text and job description cannot be empty.")

    # Extract target keywords from job description
    jd_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", req.job_description.lower()))
    resume_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", req.resume_text.lower()))

    # Calculate keyword match percentage
    matched_keywords = jd_words.intersection(resume_words)
    missing_keywords = jd_words.difference(resume_words)
    
    match_percentage = min(100, int((len(matched_keywords) / max(1, len(jd_words))) * 100))

    # Section Coverage check
    essential_sections = ["experience", "education", "skills", "projects", "summary"]
    resume_lower = req.resume_text.lower()
    covered_sections = [sec for sec in essential_sections if sec in resume_lower]
    section_score = int((len(covered_sections) / len(essential_sections)) * 100)

    # Action verbs check
    action_verbs = ["managed", "developed", "architected", "implemented", "scaled", "optimized", "built", "spearheaded", "engineered"]
    found_verbs = [verb for verb in action_verbs if verb in resume_lower]
    impact_score = min(100, len(found_verbs) * 12)

    # Overall Weighted ATS Score calculation
    overall_ats_score = int(
        (match_percentage * 0.50) + (section_score * 0.30) + (impact_score * 0.20)
    )

    # Actionable Recommendations
    recommendations = []
    if match_percentage < 70:
        recommendations.append(f"Add critical missing keywords: {', '.join(list(missing_keywords)[:5])}")
    if section_score < 100:
        missing_sections = [sec.capitalize() for sec in essential_sections if sec not in resume_lower]
        recommendations.append(f"Include missing sections: {', '.join(missing_sections)}")
    if impact_score < 60:
        recommendations.append("Use strong action verbs (e.g., Architected, Scaled, Spearheaded).")

    return {
        "status": "success",
        "overall_score": overall_ats_score,
        "grade": "A+" if overall_ats_score >= 85 else ("B" if overall_ats_score >= 70 else "Needs Optimization"),
        "breakdown": {
            "keyword_match_pct": match_percentage,
            "section_coverage_pct": section_score,
            "impact_score": impact_score,
        },
        "matched_keywords_count": len(matched_keywords),
        "missing_keywords": list(missing_keywords)[:10],
        "recommendations": recommendations or ["Your resume is highly optimized for ATS software!"]
    }


@router.post("/preview-pdf")
def generate_ats_pdf_preview(req: ATSAnalysisRequest) -> Dict[str, Any]:
    """Generates preview metadata and HTML scorecard for ATS optimized resume export."""
    score_data = calculate_ats_score(req)
    return {
        "status": "success",
        "pdf_title": "ATS_Optimized_Resume.pdf",
        "preview_html": f"<div class='ats-preview'><h1>Optimized Resume</h1><p>ATS Score: <strong>{score_data['overall_score']}/100</strong></p></div>",
        "ats_metrics": score_data
    }


class ATSTailorRequest(BaseModel):
    candidate_title: str = "Senior Engineer"
    candidate_summary: str = ""
    job_title: str = "Target Position"
    job_description: str = ""


@router.post("/tailor")
def tailor_resume_summary(req: ATSTailorRequest) -> Dict[str, Any]:
    """Generates an optimized professional summary tailored specifically for the target job."""
    from core.ats_tailor import ATSResumeTailor
    tailored_text = ATSResumeTailor.generate_tailored_summary(
        candidate_title=req.candidate_title,
        candidate_summary=req.candidate_summary,
        job_title=req.job_title,
        job_description=req.job_description
    )
    return {
        "status": "success",
        "tailored_summary": tailored_text
    }


class FreeAuditRequest(BaseModel):
    resume_text: str = Field(..., description="Resume content to analyze")
    target_role: str = Field(default="general", description="Target role or domain")


@router.post("/free-audit")
def run_free_ats_audit(req: FreeAuditRequest) -> Dict[str, Any]:
    """Instant Free ATS CV Score Lead Magnet with actionable gap analysis and upsell CTA."""
    if not req.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text cannot be empty.")
    
    from core.free_tools import check_ats_resume
    audit_data = check_ats_resume(req.resume_text, target_role=req.target_role)
    
    return {
        "status": "success",
        "lead_magnet": "JobHunt Pro Free ATS Audit",
        "data": audit_data
    }


@router.get("/upsell-packages")
def get_upsell_packages() -> Dict[str, Any]:
    """Fetch active micro-services and bouquet packages for checkout conversion."""
    from core.pricing_manager import BOUQUET_PACKAGES, PRICING_TIERS
    return {
        "status": "success",
        "starter_packages": [
            {
                "id": "quick-strike",
                "name": "⚡ Quick Strike",
                "price": 5,
                "badge": "BEST VALUE FOR CV FIX",
                "description": "ATS Dominator + Penetration Letter"
            },
            {
                "id": "basic",
                "name": "🦅 Basic Hunter",
                "price": 19,
                "badge": "MOST POPULAR",
                "description": "100 Verified Applications + Live MX Shield"
            }
        ],
        "all_bouquets": BOUQUET_PACKAGES,
        "all_tiers": PRICING_TIERS
    }


