"""
Viral Growth & Referral Engine Router for JobHunt Pro.
Exposes referral link tracking, Golden Ticket (Hongbao) redemption, and viral social cards.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from core.viral_engine import (
    get_referral_tiers,
    get_share_text,
    generate_golden_ticket,
    redeem_golden_ticket,
    get_share_card,
    generate_social_hook_card,
    get_ph_assets,
    get_random_social_proof
)

router = APIRouter(prefix="/api/growth", tags=["Viral Growth & Referrals"])


class TicketRedeemRequest(BaseModel):
    ticket_id: str
    user_email: str


@router.get("/referral-tiers")
async def get_tiers() -> List[Dict[str, Any]]:
    """Return all referral tier rewards."""
    return get_referral_tiers()


@router.get("/share-text")
async def get_viral_share_text() -> Dict[str, str]:
    """Get random high-converting viral share message."""
    return {"share_text": get_share_text()}


@router.post("/golden-ticket/generate")
async def create_golden_ticket(user_id: int = Query(default=1)) -> Dict[str, Any]:
    """Generate a shareable 'Red Envelope' Golden Ticket granting free applications."""
    return generate_golden_ticket(user_id)


@router.post("/golden-ticket/redeem")
async def claim_golden_ticket(req: TicketRedeemRequest) -> Dict[str, Any]:
    """Redeem a Golden Ticket for bonus AI applications."""
    return redeem_golden_ticket(req.ticket_id, req.user_email)


@router.get("/social-card")
async def get_social_card(tool: str = "ats_score", score: int = 88, user_id: str = "user_1") -> Dict[str, Any]:
    """Generate viral social proof cards for sharing on LinkedIn, Twitter, or WhatsApp."""
    return generate_social_hook_card(tool=tool, user_id=user_id, score=score)


@router.get("/live-proof")
async def get_social_proof() -> Dict[str, Any]:
    """Return live dynamic social proof updates for landing page widgets."""
    return get_random_social_proof()


@router.get("/product-hunt-kit")
async def get_product_hunt_assets() -> Dict[str, Any]:
    """Return Product Hunt launch kit assets."""
    return get_ph_assets()
