"""
FastAPI Router for Autonomous Enterprise B2B Lead & Bounty Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.b2b_lead_empire import B2BLeadEmpireEngine, get_b2b_empire_status

router = APIRouter(prefix="/api/v2/b2b-lead-empire", tags=["Enterprise B2B Lead & Bounty Engine"])

class BountyPitchRequest(BaseModel):
    candidate_profile: Dict[str, Any]
    lead_company: str
    bounty_usd: float

@router.get("/status")
def status_endpoint():
    return get_b2b_empire_status()

@router.get("/discover-leads")
def discover_leads_endpoint(industry: Optional[str] = "Technology"):
    engine = B2BLeadEmpireEngine()
    return {"industry": industry, "leads": engine.discover_bounty_leads(industry or "Technology")}

@router.post("/submit-pitch")
def submit_pitch_endpoint(req: BountyPitchRequest):
    engine = B2BLeadEmpireEngine()
    return engine.submit_candidate_bounty_pitch(req.candidate_profile, req.lead_company, req.bounty_usd)
