"""
God-Mode Router (FastAPI Backend)
Exposes REST endpoints for the 5-Engine God-Tier Autonomous Suite.
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from core.god_mode_orchestrator import god_mode_orchestrator

router = APIRouter(prefix="/api/v2/god-mode", tags=["God-Mode Autonomous Suite"])

class AutoApplyRequest(BaseModel):
    user_id: str
    job_query: str
    locations: List[str] = ["Remote", "Global"]

class VoiceCoachRequest(BaseModel):
    user_id: str
    role_title: str

class MessagingCommandRequest(BaseModel):
    user_id: str
    channel: str = "whatsapp"
    message: str

class SalaryNegotiateRequest(BaseModel):
    job_title: str
    current_offer: float
    currency: str = "USD"

@router.get("/status")
async def get_god_mode_status():
    """Returns telemetry across all 5 autonomous engines."""
    return await god_mode_orchestrator.get_system_telemetry()

@router.post("/auto-apply")
async def trigger_auto_apply(req: AutoApplyRequest):
    """Triggers autonomous Playwright/Selenium stealth application sweep."""
    return await god_mode_orchestrator.trigger_auto_apply_session(
        user_id=req.user_id,
        job_query=req.job_query,
        locations=req.locations
    )

@router.post("/voice-coach")
async def start_voice_coach(req: VoiceCoachRequest):
    """Initiates real-time voice interview simulator."""
    return await god_mode_orchestrator.initiate_voice_coach_session(
        user_id=req.user_id,
        role_title=req.role_title
    )

@router.post("/self-healing/check")
async def run_self_healing():
    """Executes AST + Vision scraper health verification."""
    return await god_mode_orchestrator.run_self_healing_check()

@router.post("/messaging/command")
async def process_messaging_command(req: MessagingCommandRequest):
    """Processes incoming WhatsApp or Telegram commands."""
    return await god_mode_orchestrator.process_messaging_command(
        user_id=req.user_id,
        channel=req.channel,
        message=req.message
    )

@router.post("/salary-negotiate")
async def calculate_salary(req: SalaryNegotiateRequest):
    """Generates market salary telemetry and automated negotiation scripts."""
    return await god_mode_orchestrator.calculate_salary_negotiation(
        job_title=req.job_title,
        current_offer=req.current_offer,
        currency=req.currency
    )
