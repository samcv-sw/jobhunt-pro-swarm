"""
FastAPI Router for L402 Bitcoin Lightning Autonomous Micro-Payments.
"""

from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Optional
from core.x402_lightning_protocol import lightning_engine

router = APIRouter(prefix="/api/l402", tags=["L402 Lightning Monetization"])

@router.post("/challenge")
async def create_challenge(resource_id: str, amount_sats: int = 100):
    """Generate an L402 invoice challenge for premium AI services."""
    return lightning_engine.create_invoice(resource_id=resource_id, amount_sats=amount_sats)

@router.post("/verify")
async def verify_challenge(macaroon: str, preimage: str):
    """Verify LN preimage and redeem access to AI services."""
    result = lightning_engine.verify_payment(macaroon=macaroon, preimage=preimage)
    if not result.get("valid"):
        raise HTTPException(status_code=402, detail=result.get("error", "Payment verification failed"))
    return result
