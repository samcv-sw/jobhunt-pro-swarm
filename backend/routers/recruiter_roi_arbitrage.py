"""
Recruiter ROI Arbitrage & Viral Lead Magnet Router
Provides endpoints to generate embeddable widgets, issue Golden Tickets,
and calculate B2B recruitment cost savings.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from core.viral_lead_magnet_engine import viral_lead_magnet_engine

router = APIRouter(prefix="/api/recruiter-roi", tags=["Recruiter ROI & Viral Lead Magnet"])

class WidgetRequest(BaseModel):
    affiliate_code: str = Field("PARTNER_PRO", example="PARTNER_PRO")
    primary_color: str = Field("#0ea5e9", example="#0ea5e9")
    lang: str = Field("ar", example="ar")

class GoldenTicketRequest(BaseModel):
    user_id: str = Field("user_777", example="user_777")

class ROICalculateRequest(BaseModel):
    hires_per_year: int = Field(10, example=10)
    avg_annual_salary_usd: float = Field(80000.0, example=80000.0)

@router.post("/generate-widget")
def get_embed_widget(req: WidgetRequest) -> Dict[str, Any]:
    """Generate embeddable ATS lead magnet widget snippet."""
    return viral_lead_magnet_engine.generate_embeddable_widget(
        affiliate_code=req.affiliate_code,
        primary_color=req.primary_color,
        lang=req.lang
    )

@router.post("/issue-golden-ticket")
def issue_golden_ticket(req: GoldenTicketRequest) -> Dict[str, Any]:
    """Issue a viral golden ticket for referral rewards."""
    return viral_lead_magnet_engine.generate_golden_ticket(user_id=req.user_id)

@router.post("/calculate-savings")
def calculate_roi_savings(req: ROICalculateRequest) -> Dict[str, Any]:
    """Calculate annual agency recruitment fee savings vs JobHunt Pro."""
    return viral_lead_magnet_engine.calculate_recruiter_roi(
        hires_per_year=req.hires_per_year,
        avg_annual_salary_usd=req.avg_annual_salary_usd
    )

@router.get("/referral-tiers")
def get_referral_tiers() -> Dict[str, Any]:
    """Get viral referral tiers and token reward breakdown."""
    return {
        "tiers": viral_lead_magnet_engine.REFERRAL_TIERS,
        "token_economy": "Zero-Cost Autonomous Growth Engine"
    }
