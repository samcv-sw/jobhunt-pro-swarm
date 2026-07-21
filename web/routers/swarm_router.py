"""
Swarm Router for JobHunt Pro
API routes for starting, stopping, and monitoring the Autonomous Job Hunter Swarm.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
from services.auto_swarm import swarm_engine

router = APIRouter(prefix="/api/swarm", tags=["Swarm"])

def get_current_user_id() -> str:
    return "user_demo_pro"

@router.post("/start")
async def start_job_swarm(
    roles: List[str] = Body(default=["Software Engineer", "Backend Developer"]),
    locations: List[str] = Body(default=["Remote", "Dubai", "Riyadh"]),
    daily_limit: int = Body(default=25),
    user_id: str = Depends(get_current_user_id)
):
    """Start the autonomous job hunter swarm."""
    status = swarm_engine.start_swarm(user_id=user_id, target_roles=roles, locations=locations, daily_limit=daily_limit)
    return {"status": "success", "data": status}

@router.get("/status")
async def get_swarm_status(user_id: str = Depends(get_current_user_id)):
    """Retrieve current swarm status and stats."""
    status = swarm_engine.get_swarm_status(user_id=user_id)
    return {"status": "success", "data": status}

@router.post("/stop")
async def stop_job_swarm(user_id: str = Depends(get_current_user_id)):
    """Stop the active swarm."""
    stopped = swarm_engine.stop_swarm(user_id=user_id)
    return {"status": "success" if stopped else "not_found", "stopped": stopped}

@router.post("/tailor")
async def tailor_resume(
    resume_text: str = Body(...),
    job_description: str = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """Tailor resume for a target job description."""
    res = swarm_engine.tailor_resume_for_job(resume_text=resume_text, job_description=job_description)
    return {"status": "success", "data": res}
