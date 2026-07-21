"""
FastAPI Router for Autonomous Freelance Arbitrage Swarm
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from core.freelance_arbitrage_swarm import freelance_swarm

router = APIRouter(prefix="/api/v1/freelance-arbitrage", tags=["Freelance Arbitrage Swarm"])

class ProposalRequest(BaseModel):
    lead_id: str
    title: str
    budget_usd: float

class LightningPaymentRequest(BaseModel):
    proposal_id: str
    satoshis: Optional[int] = 150000

@router.get("/scan")
def scan_leads(category: str = "fullstack"):
    """Scan freelance job platforms for high-value micro-projects."""
    leads = freelance_swarm.scan_freelance_leads(category=category)
    return {"status": "success", "leads": leads}

@router.post("/proposal")
def generate_proposal(req: ProposalRequest):
    """Generate an autonomous winning bid proposal."""
    proposal = freelance_swarm.generate_autonomous_proposal(
        lead_id=req.lead_id,
        title=req.title,
        budget_usd=req.budget_usd
    )
    return {"status": "success", "proposal": proposal}

@router.post("/settle-payment")
def settle_payment(req: LightningPaymentRequest):
    """Settle an HTTP 402 Lightning crypto payout."""
    res = freelance_swarm.Settle_lightning_invoice(
        proposal_id=req.proposal_id,
        satoshis=req.satoshis
    )
    return {"status": "success", "settlement": res}

@router.get("/telemetry")
def get_telemetry():
    """Retrieve telemetry metrics for the freelance arbitrage swarm."""
    return {"status": "success", "telemetry": freelance_swarm.get_swarm_telemetry()}
