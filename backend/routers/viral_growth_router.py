"""Autonomous Viral Growth API Router

Exposes endpoints for generating viral social campaigns, interactive demo cards,
and real-time lead conversion analytics.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from core.viral_growth_engine import viral_growth_engine

router = APIRouter(prefix="/api/v3/viral", tags=["Autonomous Viral Client Acquisition"])


class CreateCampaignRequest(BaseModel):
    target_niche: str = "remote_engineers"


class CreateDemoCardRequest(BaseModel):
    candidate_name: str = "Alex Morgan"
    job_title: str = "Senior Full-Stack AI Engineer"


@router.post("/generate-campaign")
async def generate_campaign(req: CreateCampaignRequest):
    """Generates viral social proof posts and client acquisition hooks."""
    return viral_growth_engine.generate_viral_campaign(req.target_niche)


@router.post("/demo-card")
async def create_demo_card(req: CreateDemoCardRequest):
    """Creates a viral shareable interactive micro-portfolio card."""
    return viral_growth_engine.create_interactive_demo_card(req.candidate_name, req.job_title)


@router.get("/analytics")
async def get_growth_analytics():
    """Returns real-time analytics on viral acquisition metrics."""
    return viral_growth_engine.get_campaign_analytics()
