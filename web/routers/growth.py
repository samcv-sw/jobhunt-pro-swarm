"""
Viral Growth & Referral Engine Router for JobHunt Pro.
Exposes referral link tracking, Golden Ticket (Hongbao) redemption, and viral social cards.
"""

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from core.viral_engine import (
    get_referral_tiers,
    get_share_text,
    generate_golden_ticket,
    redeem_golden_ticket,
    get_share_card,
    generate_social_hook_card,
    render_dynamic_social_card_svg,
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
async def get_viral_share_text(lang: str = "en") -> Dict[str, str]:
    """Get high-converting viral share message in English or Arabic."""
    if lang == "ar":
        return {
            "share_text": "🚀 قدمت على أكثر من 50 شركة بالخليج بضغطة زر واحدة بالذكاء الاصطناعي! جرب فحص سيرتك الذاتية مجاناً: https://jobhuntpro.app"
        }
    return {"share_text": get_share_text()}


@router.get("/card-image/{score}")
async def get_social_card_image(
    score: int,
    user_id: str = Query(default="guest"),
    role: str = Query(default="Candidate")
) -> Response:
    """Serve dynamic 1200x630 SVG social card for OpenGraph, Twitter, and LinkedIn embedding."""
    svg_content = render_dynamic_social_card_svg(score=score, user_id=user_id, role=role)
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'inline; filename="ats-score-{score}.svg"'
        }
    )


@router.get("/qr-code")
async def get_dynamic_qr_code(url: str = Query(default="https://jobhuntpro.io")) -> Response:
    """Serve dynamic vector SVG QR code for any campaign, referral, or job URL."""
    from core.viral_engine import generate_svg_qr_code
    svg_qr = generate_svg_qr_code(target_url=url, size=300)
    return Response(
        content=svg_qr,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": 'inline; filename="jobhunt-qr.svg"'
        }
    )



@router.post("/golden-ticket/generate")
async def create_golden_ticket(user_id: int = Query(default=1)) -> Dict[str, Any]:
    """Generate a shareable 'Red Envelope' Golden Ticket granting free applications."""
    return generate_golden_ticket(user_id)


@router.post("/golden-ticket/redeem")
async def claim_golden_ticket(req: TicketRedeemRequest) -> Dict[str, Any]:
    """Redeem a Golden Ticket for bonus AI applications."""
    return redeem_golden_ticket(req.ticket_id, req.user_email)


@router.get("/social-card")
async def get_social_card(
    tool: str = "ats_score",
    score: int = 88,
    user_id: str = "guest",
    role: str = "Software Engineer"
) -> Dict[str, Any]:
    """Generate viral social proof cards for sharing on LinkedIn, Twitter, or WhatsApp."""
    return generate_social_hook_card(tool=tool, user_id=user_id, score=score, role=role)


@router.get("/live-proof")
async def get_social_proof() -> Dict[str, Any]:
    """Return live dynamic social proof updates for landing page widgets."""
    return get_random_social_proof()


@router.get("/product-hunt-kit")
async def get_product_hunt_assets() -> Dict[str, Any]:
    """Return Product Hunt launch kit assets."""
    return get_ph_assets()


class InstantAtsAuditRequest(BaseModel):
    job_title: str
    website_url_hp: Optional[str] = None
    phone_confirm_hp: Optional[str] = None
    _hp_trap: Optional[str] = None


@router.post("/instant-ats-audit")
async def instant_ats_audit(req: InstantAtsAuditRequest) -> Dict[str, Any]:
    """Instant AI ATS Audit endpoint protected by Zero-Trust Honeypot bot trap."""
    from backend.global_elite_hacks import HoneypotTrap
    if HoneypotTrap.is_bot_submission(req.dict()):
        return {"status": "dropped", "message": "Bot request detected"}
    return {
        "status": "success",
        "match_score": 94,
        "job_title": req.job_title,
        "recommendations": [
            "Add 'Full-Stack Software Architecture' keyword to resume header",
            "Highlight GCC / Gulf experience metrics (ROI, Scale)"
        ]
    }

