"""
Viral SDR Router
Exposes APIs for automated corporate lead scoring, cold pitch generation, and viral referral loops.
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from core.viral_sdr_swarm import viral_sdr_swarm

router = APIRouter(prefix="/api/v1/viral-sdr", tags=["Viral SDR Swarm"])

@router.post("/scan-lead")
def scan_lead(payload: Dict[str, Any] = Body(...)):
    """Ranks and scores target corporate lead."""
    company_name = str(payload.get("company_name", "Tech Corp"))
    job_title = str(payload.get("job_title", "Software Engineer"))
    estimated_budget = float(payload.get("estimated_budget", 10000))
    lead = viral_sdr_swarm.scan_and_rank_lead(company_name, job_title, estimated_budget)
    return {"status": "success", "lead": lead}

@router.post("/generate-pitch")
def generate_pitch(payload: Dict[str, Any] = Body(...)):
    """Generates hyper-personalized outreach pitch for hiring manager."""
    company_name = str(payload.get("company_name", "Tech Corp"))
    job_title = str(payload.get("job_title", "Software Engineer"))
    candidate_name = str(payload.get("candidate_name", "Alex Developer"))
    pitch = viral_sdr_swarm.generate_personalized_pitch(company_name, job_title, candidate_name)
    return {"status": "success", "pitch": pitch}

@router.post("/viral-campaign")
def viral_campaign(payload: Dict[str, Any] = Body(...)):
    """Generates viral referral campaign asset."""
    user_id = str(payload.get("user_id", "user_123"))
    referral_code = str(payload.get("referral_code", "EMP2026"))
    campaign = viral_sdr_swarm.generate_viral_campaign_link(user_id, referral_code)
    return {"status": "success", "campaign": campaign}
