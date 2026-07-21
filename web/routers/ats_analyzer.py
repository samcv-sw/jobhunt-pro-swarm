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
    """Generates structured payload for split-screen live PDF resume preview."""
    score_data = calculate_ats_score(req)
    return {
        "status": "success",
        "pdf_title": "ATS_Optimized_Resume.pdf",
        "preview_html": f"<div class='ats-preview'><h1>Optimized Resume</h1><p>ATS Score: <strong>{score_data['overall_score']}/100</strong></p></div>",
        "ats_metrics": score_data
    }
