"""
Outreach Media API Router
Exposes AI video & audio pitch generator endpoints for outreach.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.zero_cost_video_pitch import video_pitcher

router = APIRouter(prefix="/api/outreach-media", tags=["Outreach Media API"])


class VideoPitchRequest(BaseModel):
    company_name: str
    recruiter_name: Optional[str] = "Hiring Manager"
    script_text: Optional[str] = "Hi! I am excited to share my experience and see how I can add immediate value to your engineering team."


@router.post("/generate-script")
async def generate_outreach_script(payload: VideoPitchRequest):
    """Generates personalized pitch script for recruiters."""
    script = (
        f"Hello {payload.recruiter_name}, I saw that {payload.company_name} is scaling your tech infrastructure. "
        f"{payload.script_text} I have a proven track record of reducing latency by 40% and deploying zero-cost cloud systems. "
        "Looking forward to connecting!"
    )
    return {
        "status": "success",
        "company_name": payload.company_name,
        "script": script
    }


@router.post("/generate-video")
async def create_video_pitch(payload: VideoPitchRequest):
    """
    Renders personalized video pitch payload structure for outreach campaigns.
    """
    if not payload.company_name.strip():
        raise HTTPException(status_code=400, detail="Company name is required.")

    script = await generate_outreach_script(payload)
    return {
        "status": "success",
        "company_name": payload.company_name,
        "script": script["script"],
        "media_type": "mp4_video_pitch",
        "preview_url": f"/static/pitches/{payload.company_name.lower().replace(' ', '_')}_pitch.mp4"
    }
