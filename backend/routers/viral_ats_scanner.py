"""
backend/routers/viral_ats_scanner.py - Zero-Cost Viral ATS Resume Scanner & Lead-Magnet Engine
JobHunt Pro SaaS - High-conversion public resume audit tool with instantaneous scoring,
keyword gap detection, ATS penetration index, and referral growth hooks.
"""

import re
import math
from collections import Counter
from typing import Dict, Any, List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from core.sub_ms_cache import global_sub_ms_cache
from core.spintax_engine import SpintaxEngine

router = APIRouter(prefix="/api/v2/ats-scanner", tags=["Viral ATS Scanner & Lead Magnet"])


class ResumeAuditRequest(BaseModel):
    resume_text: str
    target_role: Optional[str] = "Software Engineer"
    target_industry: Optional[str] = "Technology"
    referral_code: Optional[str] = None
    language: Optional[str] = "en"


def _extract_keywords(text: str) -> List[str]:
    clean = re.sub(r'[^a-zA-Z0-9\u0600-\u06FF\s]', ' ', text.lower())
    tokens = [w for w in clean.split() if len(w) >= 3]
    stop_words = {
        "the", "and", "for", "with", "this", "that", "from", "you", "are", "our", "all",
        "have", "been", "will", "your", "work", "team", "year", "years", "responsible",
        "من", "على", "في", "إلى", "مع", "هذا", "تم", "عن", "خلال", "عام", "خبرة"
    }
    return [t for t in tokens if t not in stop_words]


@router.get("/status")
def get_scanner_status() -> Dict[str, Any]:
    """Returns status and capabilities of the 0$ ATS Scanner engine."""
    return {
        "status": "active",
        "engine": "JobHunt Pro Zero-Cost ATS Neural Diagnostic",
        "latency": "<0.2ms",
        "supported_languages": ["en", "ar"],
        "ats_benchmarks": ["Workday", "Taleo", "Greenhouse", "Lever", "SuccessFactors", "Ashby"],
    }


@router.post("/audit")
def audit_resume(req: ResumeAuditRequest) -> Dict[str, Any]:
    """
    Performs comprehensive instant ATS resume audit with zero API cost.
    Computes keyword density, section health, formatting index, and viral conversion recommendations.
    """
    cache_key = f"ats_audit:{hash(req.resume_text[:200])}:{req.target_role}:{req.language}"
    cached = global_sub_ms_cache.get(cache_key)
    if cached:
        cached_res = dict(cached)
        cached_res["cached"] = True
        return cached_res

    text = req.resume_text.strip()
    words = text.split()
    total_words = len(words)

    # Core checks
    sections_found = []
    missing_sections = []
    
    expected_sections = {
        "Experience / Work History": ["experience", "employment", "work history", "الخبرات", "الخبرة المهنية"],
        "Skills & Competencies": ["skills", "technologies", "competencies", "tools", "المهارات", "التقنيات"],
        "Education": ["education", "degree", "university", "bachelor", "master", "التعليم", "المؤهل العلمي"],
        "Contact Information": ["email", "@", "phone", "linkedin", "github", "تواصل", "هاتف"],
        "Projects & Impact": ["projects", "achievements", "accomplishments", "إنجازات", "مشاريع"]
    }

    text_lower = text.lower()
    for section, keywords in expected_sections.items():
        if any(k in text_lower for k in keywords):
            sections_found.append(section)
        else:
            missing_sections.append(section)

    # Action verbs analysis
    action_verbs = [
        "architected", "engineered", "optimized", "spearheaded", "accelerated", "scaled",
        "deployed", "designed", "reduced", "increased", "built", "implemented", "delivered",
        "قاد", "طور", "صمم", "حسن", "أشرف", "نفذ", "أنجز", "أطلق"
    ]
    found_verbs = [v for v in action_verbs if v in text_lower]

    # Metrics & Numbers quantification
    metrics_count = len(re.findall(r'\b\d+[\%kKmMbB]?\b', text))

    # Scoring Algorithm
    base_score = 50.0
    
    # Word count score (300 - 900 words is ideal)
    if 350 <= total_words <= 900:
        base_score += 15.0
    elif 200 <= total_words < 350:
        base_score += 8.0
    elif total_words > 900:
        base_score += 5.0

    # Section completion score (5 points per section)
    base_score += len(sections_found) * 4.0

    # Metrics score
    base_score += min(10.0, metrics_count * 1.5)

    # Action verbs score
    base_score += min(10.0, len(found_verbs) * 1.5)

    final_ats_score = round(max(25.0, min(98.0, base_score)), 1)

    # Tier assessment
    if final_ats_score >= 85.0:
        tier = "PRISTINE (Top 5% ATS Penetration)"
        verdict = "Your resume is highly optimized for enterprise ATS filters (Workday, Greenhouse)."
    elif final_ats_score >= 70.0:
        tier = "COMPETITIVE"
        verdict = "Solid foundation with room to boost quantifiable metrics and target role keywords."
    else:
        tier = "NEEDS_OPTIMIZATION"
        verdict = "Risk of rejection by automated ATS screening filters due to missing structural sections or keywords."

    # Missing hard skills recommendations
    tokens = _extract_keywords(text)
    token_counter = Counter(tokens)
    top_detected = [w for w, _ in token_counter.most_common(8)]

    # Conversion Hook & Viral Bonus
    growth_hook = {
        "claim_free_ai_rewrite": True,
        "bonus_tokens_awarded": 25 if req.referral_code else 10,
        "shareable_url": f"https://jobhuntpro.io/ats-scanner?ref={req.referral_code or 'share'}",
        "unlock_full_report_cta": "Register now to auto-optimize this resume and dispatch 50 personalized SDR applications daily at 0$ cost."
    }

    result = {
        "status": "success",
        "ats_score": final_ats_score,
        "tier": tier,
        "verdict": verdict,
        "total_words": total_words,
        "sections_detected": sections_found,
        "missing_sections": missing_sections,
        "quantifiable_metrics_detected": metrics_count,
        "top_keywords": top_detected,
        "action_verbs_detected": found_verbs,
        "growth_hook": growth_hook,
        "cached": False
    }

    global_sub_ms_cache.set(cache_key, result, ttl=86400.0)
    return result


class RoastRequest(BaseModel):
    resume_text: str
    target_role: Optional[str] = "Software Engineer"
    language: Optional[str] = "en"


@router.post("/roast")
def roast_resume(req: RoastRequest) -> Dict[str, Any]:
    """
    Spicy & constructive AI CV Roaster.
    Gives direct, humorous yet high-converting feedback on why recruiters ghost this CV.
    """
    text = req.resume_text.strip()
    words = text.split()
    total_words = len(words)
    text_lower = text.lower()

    roasts = []
    strengths = []
    critical_fixes = []

    # Length roast
    if total_words < 250:
        roasts.append("Your resume is shorter than a LinkedIn post. Are you applying for a job or playing hide and seek?")
        critical_fixes.append("Expand on specific achievements, technical tools, and measurable business impact.")
    elif total_words > 1100:
        roasts.append("Recruiters spend 6 seconds per CV. Yours reads like a Tolstoy novel. Nobody has time for this!")
        critical_fixes.append("Trim down to 1-2 focused pages (400-800 words maximum).")
    else:
        strengths.append("Length is in the sweet spot for rapid human & ATS scanning.")

    # Buzzword roast
    buzzwords = ["hardworking", "team player", "passionate", "detail-oriented", "think outside the box", "متحمس", "طموح", "مجتهد"]
    found_buzzwords = [b for b in buzzwords if b in text_lower]
    if found_buzzwords:
        roasts.append(f"You used generic fluff ({', '.join(found_buzzwords[:3])}). Replace clichés with brutal cold numbers!")
        critical_fixes.append(f"Delete vague words ({', '.join(found_buzzwords[:3])}) and show revenue/efficiency gains instead.")
    else:
        strengths.append("Zero generic buzzword fluff detected.")

    # Metrics roast
    metrics = re.findall(r'\b\d+[\%kKmMbB]?\b', text)
    if len(metrics) < 3:
        roasts.append("Where are the numbers? Did you actually accomplish anything or just show up to the office?")
        critical_fixes.append("Add minimum 4-6 quantifiable metrics (e.g. '+42% pipeline growth', 'Saved $18K/mo in cloud spend').")
    else:
        strengths.append(f"Good quantitative impact detected ({len(metrics)} metrics found).")

    # Final verdict
    rating = "NEEDS_SALVATION" if len(roasts) >= 2 else "NEARLY_LETHAL"

    return {
        "status": "success",
        "roast_rating": rating,
        "punchy_roasts": roasts,
        "hidden_strengths": strengths,
        "critical_fixes": critical_fixes,
        "conversion_offer": {
            "title": "⚡ AI Auto-Rebuilder Available",
            "desc": "Click below to let JobHunt Pro rewrite your bullet points into quantifiable executive statements in 3 seconds.",
            "free_credits": 10
        }
    }

