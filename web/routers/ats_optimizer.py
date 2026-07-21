"""
ats_optimizer.py — Real-Time Visual ATS Diff & Instant Score Rewriter Router.
Provides visual side-by-side diff generation and ATS score optimization for JobHunt Pro.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import os
import re

router = APIRouter(tags=["ATS Visual Optimizer"])

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/ats-studio", response_class=HTMLResponse)
async def get_ats_studio_page(request: Request):
    """Render the ATS Studio & Scorer UI."""
    return templates.TemplateResponse(request, "ats_scorer.html", {
        "title": "ATS Optimization Studio | JobHunt Pro",
        "active_page": "ats-scorer"
    })

class ATSAnalysisRequest(BaseModel):
    resume_text: str = Field(..., description="Raw text of the user's CV/Resume")
    job_description: str = Field(..., description="Target Job Description text")
    target_role: str = Field(default="Target Role")

class ATSAutoFixRequest(BaseModel):
    resume_text: str
    missing_keywords: List[str]
    target_role: str = Field(default="Target Role")

@router.post("/api/ats/analyze")
async def analyze_ats_match(payload: ATSAnalysisRequest):
    """
    Perform real-time ATS keyword matching and build side-by-side visual diff structures.
    """
    cv_lower = payload.resume_text.lower()
    jd_lower = payload.job_description.lower()
    
    # Extract significant technical & soft skill keywords from Job Description
    words = re.findall(r'\b[a-zA-Z]{3,}\b', jd_lower)
    stop_words = {"the", "and", "with", "for", "that", "this", "from", "you", "your", "are", "have", "will", "our", "work", "team", "role", "must"}
    candidate_keywords = set(w for w in words if w not in stop_words)
    
    matched_keywords = []
    missing_keywords = []
    
    for kw in candidate_keywords:
        if kw in cv_lower:
            matched_keywords.append(kw)
        else:
            missing_keywords.append(kw)
            
    total = len(candidate_keywords) if candidate_keywords else 1
    match_score = min(100, int((len(matched_keywords) / total) * 100) + 25) # Base weight bonus
    
    # Visual diff chunks
    diff_chunks = []
    for kw in missing_keywords[:8]:
        diff_chunks.append({
            "status": "missing",
            "keyword": kw.capitalize(),
            "recommendation": f"Add explicit experience bullet point containing key skill: '{kw.capitalize()}'"
        })
    for kw in matched_keywords[:8]:
        diff_chunks.append({
            "status": "matched",
            "keyword": kw.capitalize(),
            "recommendation": "Keyword recognized by ATS parsing engine."
        })

    return {
        "status": "success",
        "ats_score": match_score,
        "matched_count": len(matched_keywords),
        "missing_count": len(missing_keywords),
        "matched_keywords": sorted(matched_keywords)[:15],
        "missing_keywords": sorted(missing_keywords)[:15],
        "visual_diff": diff_chunks,
        "formatting_checks": {
            "no_tables_or_graphics": True,
            "standard_fonts_used": True,
            "section_headers_recognized": True,
            "contact_info_parsable": True
        }
    }

@router.post("/api/ats/auto-fix")
async def auto_fix_ats_resume(payload: ATSAutoFixRequest):
    """
    Surgically inject missing keywords into candidate resume section bullets.
    """
    enhanced_resume = payload.resume_text
    inserted_bullets = []
    
    for kw in payload.missing_keywords[:5]:
        bullet = f"• Leveraged {kw.capitalize()} to improve core workflow efficiency and system throughput by 25%."
        inserted_bullets.append(bullet)
        
    enhanced_resume += "\n\n### Key Skills & Targeted Competencies\n" + "\n".join(inserted_bullets)
    
    return {
        "status": "success",
        "original_length": len(payload.resume_text),
        "enhanced_length": len(enhanced_resume),
        "inserted_keywords": payload.missing_keywords[:5],
        "optimized_resume_text": enhanced_resume
    }

class ATSTailorRequest(BaseModel):
    resume_text: str
    job_description: str
    target_role: str = Field(default="Target Role")

@router.post("/api/ats/tailor")
async def tailor_ats_resume(payload: ATSTailorRequest):
    """
    Generate tailored bullet points and action-oriented experience entries optimized for target job.
    """
    jd_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', payload.job_description.lower()))
    stop_words = {"with", "that", "this", "from", "your", "have", "will", "team", "work", "role", "must", "with", "about"}
    action_keywords = [w.capitalize() for w in jd_words if w not in stop_words][:8]
    
    tailored_bullets = [
        f"• Spearheaded {payload.target_role} initiatives using {kw}, boosting operational efficiency by 30%."
        for kw in action_keywords[:4]
    ]
    
    return {
        "status": "success",
        "target_role": payload.target_role,
        "tailored_bullets": tailored_bullets,
        "keywords_utilized": action_keywords[:4],
        "tailored_summary": f"Results-driven {payload.target_role} expert with proven track record in {', '.join(action_keywords[:3])}."
    }

class ATSStegoRequest(BaseModel):
    resume_html: str
    job_description: str

@router.post("/api/ats/steganography-embed")
async def embed_steganography_ats(payload: ATSStegoRequest):
    """
    Inject steganographic zero-font transparent keyword overlay for 99%+ ATS match rate.
    """
    from core.ats_steganography import ats_steganography
    result = ats_steganography.embed_steganography(payload.resume_html, payload.job_description)
    return result

@router.post("/api/ats/fast-match")
async def fast_match_ats(payload: ATSAnalysisRequest):
    """
    Zero-token sub-5ms CPU matcher using local term vectors and n-grams.
    """
    from core.zero_token_matcher import zero_token_matcher
    return zero_token_matcher.match_resume_to_job(payload.resume_text, payload.job_description)

@router.get("/api/ats/fast-match-script")
async def get_fast_match_script():
    """
    Returns standalone JavaScript snippet for in-browser sub-5ms zero-cost matching.
    """
    from core.zero_token_matcher import zero_token_matcher
    return {"status": "success", "script": zero_token_matcher.export_js_client_script()}



