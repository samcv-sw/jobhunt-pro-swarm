"""
FastAPI Router for Sovereign Viral Growth & Affiliate Flywheel Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from core.sovereign_viral_flywheel import SovereignViralFlywheel, get_flywheel_status

router = APIRouter(prefix="/api/v2/viral-flywheel", tags=["Viral Growth & Affiliate Flywheel"])

class InviteProcessRequest(BaseModel):
    referrer_id: str
    new_user_email: str

@router.get("/status")
def status_endpoint():
    return get_flywheel_status()

@router.get("/affiliate-link/{user_id}")
def affiliate_link_endpoint(user_id: str):
    engine = SovereignViralFlywheel()
    return engine.generate_affiliate_link(user_id)

@router.post("/process-invite")
def process_invite_endpoint(req: InviteProcessRequest):
    engine = SovereignViralFlywheel()
    return engine.process_viral_invite(req.referrer_id, req.new_user_email)
