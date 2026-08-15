"""
Monetization & Growth Router
JobHunt Pro SaaS - REST endpoints for dynamic upgrade triggers, discount vouchers, and referral reward loops.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from core.monetization_growth_engine import monetization_engine

router = APIRouter(prefix="/api/v2/monetization", tags=["Monetization & Referral Engine"])


@router.get("/check-upgrade-trigger")
def check_upgrade(user_id: str = Query("usr_demo", description="User ID"), tokens: int = Query(1, ge=0)):
    """Evaluates whether to show a high-converting flash upgrade modal."""
    return monetization_engine.evaluate_upgrade_trigger(user_id, tokens)


@router.get("/referral-profile/{user_id}")
def get_referral(user_id: str):
    """Fetches user referral link and reward statistics."""
    return monetization_engine.generate_referral_profile(user_id)
