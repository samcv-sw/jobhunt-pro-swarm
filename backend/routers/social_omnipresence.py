"""
FastAPI router for LinkedIn & Social Omnipresence Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.social_omnipresence import social_omnipresence_engine
from services.social_growth_swarm_v3 import social_growth_swarm_v3

router = APIRouter(prefix="/api/v2/social-omnipresence", tags=["Social Omnipresence Engine"])

class ViralPostRequest(BaseModel):
    topic: str
    target_audience: str = "Recruiters & Engineering Leads"

class RecruiterOutreachRequest(BaseModel):
    recruiter_name: str
    company: str
    target_role: str

@router.post("/generate-post")
async def generate_social_post(req: ViralPostRequest):
    return social_omnipresence_engine.generate_viral_post(req.topic, req.target_audience)

@router.post("/launch-outreach")
async def launch_recruiter_outreach(req: RecruiterOutreachRequest):
    return social_omnipresence_engine.launch_recruiter_dm_sequence(req.recruiter_name, req.company, req.target_role)

@router.get("/analytics")
async def get_social_analytics():
    return social_omnipresence_engine.get_omnipresence_analytics()

@router.post("/growth-swarm/launch")
async def launch_growth_swarm():
    return social_growth_swarm_v3.execute_social_swarm_cycle()

@router.get("/growth-swarm/channel-content")
async def get_channel_content(channel: str = "producthunt"):
    return social_growth_swarm_v3.generate_launch_content(channel)

