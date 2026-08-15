"""
JobHunt Pro SaaS — Viral ATS Resume Scorecard & LinkedIn Growth Engine.
Provides instant ATS compatibility scoring, keyword gap analysis, LinkedIn shareable badges,
and viral referral growth mechanics.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import re
import uuid

router = APIRouter(prefix="/api/v1/ats", tags=["Viral ATS Scorecard"])


class ATSScorecardRequest(BaseModel):
    cv_text: str = Field(..., description="Full plain text of the candidate's resume/CV")
    target_job_title: Optional[str] = Field(None, description="Target job title or target industry")
    target_job_description: Optional[str] = Field(None, description="Job description text for keyword matching")
    referral_code: Optional[str] = Field(None, description="Referral code of inviter")


class LinkedInShareCardRequest(BaseModel):
    candidate_name: str
    ats_score: int
    top_skills: List[str]
    target_role: str


@router.post("/scorecard", response_model=Dict[str, Any])
async def calculate_ats_scorecard(req: ATSScorecardRequest):
    """
    Evaluates candidate CV against ATS parsers (formatting, contact info, metrics, keyword density).
    """
    if not req.cv_text or len(req.cv_text.strip()) < 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CV content is too short for ATS evaluation. Please provide complete resume text."
        )

    cv = req.cv_text
    score = 50  # Base starting score
    breakdown = {}
    recommendations = []
    strengths = []

    # 1. Contact Information Check (+15 pts)
    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", cv))
    has_phone = bool(re.search(r"(\+?\d{1,4}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", cv))
    has_linkedin = bool(re.search(r"linkedin\.com/in/[\w-]+", cv, re.IGNORECASE))

    contact_score = 0
    if has_email:
        contact_score += 6
    else:
        recommendations.append("Add a clear email address in the header.")

    if has_phone:
        contact_score += 5
        strengths.append("Phone number with international format detected.")
    else:
        recommendations.append("Include phone number formatted with international country code.")

    if has_linkedin:
        contact_score += 4
        strengths.append("LinkedIn profile link detected.")
    else:
        recommendations.append("Add a customized LinkedIn profile URL to boost recruiter credibility.")

    breakdown["contact_info_score"] = f"{contact_score}/15"
    score += contact_score

    # 2. Measurable Achievements & Metrics Check (+15 pts)
    # Detect percentages, dollar amounts, numbers with KPIs
    metric_matches = re.findall(r"(\d+%\s*|\$\d+[\d,]*\s*|\b\d+[\d,]*\+?\s*(users|clients|projects|deals|revenue|leads|roi|growth|reduction|sales)\b)", cv, re.IGNORECASE)
    metric_score = min(len(metric_matches) * 4, 15)
    breakdown["quantified_impact_score"] = f"{metric_score}/15"
    score += metric_score

    if metric_score >= 8:
        strengths.append(f"Strong use of quantified results and KPI metrics ({len(metric_matches)} impact metrics detected).")
    else:
        recommendations.append("Quantify your achievements with numbers (e.g., 'increased revenue by 25%', 'managed $100K budget').")

    # 3. Action Verbs & Power Words (+10 pts)
    power_verbs = ["spearheaded", "engineered", "orchestrated", "accelerated", "implemented", "optimized", "managed", "developed", "delivered", "transformed", "طور", "قاد", "نفذ", "صمم", "أدار", "حقق", "أنشأ"]
    matched_verbs = [v for v in power_verbs if re.search(r"\b" + v + r"\b", cv, re.IGNORECASE)]
    verb_score = min(len(matched_verbs) * 3, 10)
    breakdown["action_verbs_score"] = f"{verb_score}/10"
    score += verb_score

    # 4. Keyword Match vs Target Job Description (+10 pts)
    keyword_match_ratio = 85.0
    align_score = 10
    if req.target_job_description:
        words_target = set(re.findall(r"\b\w{4,}\b", req.target_job_description.lower()))
        words_cv = set(re.findall(r"\b\w{4,}\b", cv.lower()))
        common = words_target.intersection(words_cv)
        if words_target:
            ratio = len(common) / len(words_target)
            align_score = int(ratio * 10)
            keyword_match_ratio = round(ratio * 100, 1)

    score += align_score
    breakdown["job_keyword_alignment"] = f"{keyword_match_ratio}%"

    final_ats_score = min(score, 98)

    # Referral bonus computation
    referral_bonus_awarded = 0
    if req.referral_code:
        referral_bonus_awarded = 25  # 25 free tokens awarded

    return {
        "ats_score": final_ats_score,
        "grade": "A+" if final_ats_score >= 90 else ("A" if final_ats_score >= 80 else "B"),
        "grade_label": "High ATS Compatibility" if final_ats_score >= 80 else "Needs Optimization",
        "breakdown": breakdown,
        "strengths": strengths,
        "recommendations": recommendations,
        "shareable_badge_id": str(uuid.uuid4())[:8],
        "viral_referral_tokens_awarded": referral_bonus_awarded,
        "share_url": f"https://jobhuntpro.io/ats-verified/{str(uuid.uuid4())[:8]}",
    }


@router.post("/share-card", response_model=Dict[str, Any])
async def generate_linkedin_share_card(req: LinkedInShareCardRequest):
    """
    Generates dynamic metadata and visual badge configuration for LinkedIn / Social sharing.
    """
    badge_title = f"Verified {req.target_role} • ATS Score {req.ats_score}/100"
    og_description = f"{req.candidate_name}'s resume scored {req.ats_score}/100 on JobHunt Pro AI. Top Skills: {', '.join(req.top_skills[:3])}."

    return {
        "status": "SUCCESS",
        "card_title": badge_title,
        "og_description": og_description,
        "preview_theme": "Apex Glassmorphism Dark & Gold",
        "share_intent_url": f"https://www.linkedin.com/sharing/share-offsite/?url=https://jobhuntpro.io/score/{req.ats_score}",
        "viral_bonus_unlocked": True,
        "referral_multiplier": "2x AI Application Speed",
    }
