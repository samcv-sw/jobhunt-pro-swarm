"""
FastAPI Router for ATS Reverse-Engineering 100% Penetration Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.ats_penetration_engine import ATSPenetrationEngine, get_ats_engine_status

router = APIRouter(prefix="/api/v2/ats-penetration", tags=["ATS Reverse Engineering"])

class ATSOptimizeRequest(BaseModel):
    original_resume: str
    job_description: str
    target_ats: Optional[str] = None

@router.get("/status")
def status_endpoint():
    return get_ats_engine_status()

@router.post("/optimize")
def optimize_endpoint(req: ATSOptimizeRequest):
    engine = ATSPenetrationEngine()
    return engine.optimize_resume_for_ats(req.original_resume, req.job_description, req.target_ats)
