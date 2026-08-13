"""
routers/global_benchmarks.py — Global Institutional Benchmarks Router
Provides API endpoints for BlackRock Aladdin Risk Telemetry, SHREK Executive Search,
Publicis Epsilon DCO Hyper-Personalization, and Omnichannel Dispatching.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel

from core.aladdin_telemetry import aladdin_telemetry
from core.shrek_executive_matcher import shrek_executive_matcher
from core.epsilon_personalizer import epsilon_personalizer
from services.omnichannel_dispatcher import omnichannel_dispatcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/benchmarks", tags=["global_benchmarks"])

class ExecutiveEvalRequest(BaseModel):
    candidate_name: str
    current_title: str
    company: str
    years_experience: Optional[float] = 5.0
    skills: Optional[List[str]] = []
    bio: Optional[str] = ""

class DCOCopyRequest(BaseModel):
    lead_name: str
    company_name: str
    job_title: str
    company_summary: Optional[str] = ""
    custom_notes: Optional[str] = ""

class OmnichannelPayloadRequest(BaseModel):
    lead_name: str
    email: str
    company: str
    title: str
    channels: Optional[List[str]] = ["email", "linkedin"]

@router.get("/aladdin-telemetry")
async def get_aladdin_telemetry(
    total_leads: int = 250,
    emails_sent: int = 180,
    bounces: int = 1,
    replies: int = 24,
    conversions: int = 6
):
    """
    Returns BlackRock Aladdin multi-factor campaign risk and ROI telemetry.
    """
    return aladdin_telemetry.compute_campaign_health_index(
        total_leads=total_leads,
        emails_sent=emails_sent,
        bounces=bounces,
        replies=replies,
        conversions=conversions
    )

@router.post("/shrek-eval")
async def evaluate_shrek_executive(req: ExecutiveEvalRequest):
    """
    Evaluates candidate against Korn Ferry / Spencer Stuart SHREK Executive Search standards.
    """
    profile = {
        "title": req.current_title,
        "bio": req.bio,
        "skills": req.skills,
        "years_experience": req.years_experience
    }
    score_data = shrek_executive_matcher.calculate_executive_score(profile, {})
    dossier = shrek_executive_matcher.generate_confidential_dossier(
        candidate_name=req.candidate_name,
        current_title=req.current_title,
        company=req.company,
        score_data=score_data
    )
    return {
        "status": "success",
        "scores": score_data,
        "confidential_dossier": dossier
    }

@router.post("/epsilon-dco")
async def generate_epsilon_dco(req: DCOCopyRequest):
    """
    Generates Publicis Epsilon / Dentsu Merkle Dynamic Creative Optimization (DCO) outreach copy.
    """
    copy_res = epsilon_personalizer.generate_dco_copy(
        lead_name=req.lead_name,
        company_name=req.company_name,
        job_title=req.job_title,
        company_summary=req.company_summary,
        custom_notes=req.custom_notes
    )
    return {
        "status": "success",
        "dco_payload": copy_res
    }

@router.post("/omnichannel-dispatch")
async def prepare_omnichannel_dispatch(req: OmnichannelPayloadRequest):
    """
    Prepares omnichannel dispatch payload with strict live MX validation and 365-day cooldown check.
    """
    lead_data = {
        "name": req.lead_name,
        "email": req.email,
        "company": req.company,
        "title": req.title
    }
    payload = omnichannel_dispatcher.prepare_omnichannel_payload(lead_data, req.channels)
    return {
        "status": "success",
        "dispatch_payload": payload
    }
