"""
FastAPI Router for Multi-Channel Autonomous Social Outreach Swarms.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from core.omni_outreach_swarm import OmniOutreachSwarm, get_outreach_swarm_status

router = APIRouter(prefix="/api/v2/outreach-swarm", tags=["Omni Outreach Swarm"])

class OutreachTarget(BaseModel):
    name: str
    role: str
    company: str
    platform: str
    handle: Optional[str] = None

class CampaignRequest(BaseModel):
    candidate_profile: Dict[str, Any]
    targets: List[OutreachTarget]

@router.get("/status")
def status_endpoint():
    return get_outreach_swarm_status()

@router.post("/dispatch")
async def dispatch_campaign(req: CampaignRequest):
    swarm = OmniOutreachSwarm()
    target_dicts = [t.model_dump() for t in req.targets]
    result = await swarm.execute_swarm_campaign(req.candidate_profile, target_dicts)
    return result
