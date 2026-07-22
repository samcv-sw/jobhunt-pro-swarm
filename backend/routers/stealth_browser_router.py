"""
FastAPI Router for Playwright Stealth Browser Auto-Apply Pool Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from core.playwright_stealth_pool import PlaywrightStealthPool, get_stealth_pool_status

router = APIRouter(prefix="/api/v2/stealth-browser", tags=["Stealth Browser Auto-Apply"])

class StealthApplyRequest(BaseModel):
    job_url: str
    candidate_profile: Dict[str, Any]

@router.get("/status")
def status_endpoint():
    return get_stealth_pool_status()

@router.post("/auto-apply")
async def auto_apply_endpoint(req: StealthApplyRequest):
    pool = PlaywrightStealthPool()
    return await pool.execute_stealth_auto_apply(req.job_url, req.candidate_profile)
