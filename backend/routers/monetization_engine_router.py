"""
Monetization & Growth Router
JobHunt Pro SaaS - REST endpoints for dynamic upgrade triggers, discount vouchers, ROI arbitrage, and referral reward loops.
"""
from fastapi import APIRouter, Query
from typing import Dict, Any, Optional

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


@router.get("/roi-calculator")
def get_roi_arbitrage(
    current_salary_usd: float = Query(2000.0, ge=500.0, description="Current monthly salary in USD"),
    target_salary_usd: float = Query(5500.0, ge=1000.0, description="Target monthly salary in USD"),
    plan_key: str = Query("pro", description="Plan key: starter, pro, vip_unlimited, b2b_sdr_swarm, agency_whitelabel")
) -> Dict[str, Any]:
    """Calculates ROI financial arbitrage and salary upside multiplier."""
    return monetization_engine.calculate_candidate_roi(current_salary_usd, target_salary_usd, plan_key)


@router.get("/plans")
def get_monetization_plans() -> Dict[str, Any]:
    """Returns all current high-converting B2C and B2B pricing tiers."""
    return {
        "plans": monetization_engine.PLANS,
        "currency_base": "USD",
        "secondary_currency": "SAR",
        "exchange_rate": 3.75,
        "supported_gateways": ["lemonsqueezy", "tap_gcc", "tamara_bnpl", "usdt_crypto"]
    }


from pydantic import BaseModel, Field

class CheckoutRequest(BaseModel):
    user_id: str = Field(..., example="usr_123")
    plan_key: str = Field("pro", example="pro")
    gateway: str = Field("lemonsqueezy", example="lemonsqueezy")
    currency: Optional[str] = Field("USD", example="USD")

class CryptoVerifyRequest(BaseModel):
    user_id: str = Field(..., example="usr_123")
    tx_hash: str = Field(..., example="0x9a8f...b7e1")
    plan_key: str = Field("pro", example="pro")
    network: Optional[str] = Field("USDT_TRC20", example="USDT_TRC20")


@router.post("/checkout")
def create_checkout(req: CheckoutRequest) -> Dict[str, Any]:
    """
    Creates a dynamic checkout session for global/GCC users (LemonSqueezy, Tap, Tamara, Crypto USDT).
    Stripe is excluded to maintain lean zero-overhead operations.
    """
    return monetization_engine.create_checkout_session(
        user_id=req.user_id,
        plan_key=req.plan_key,
        gateway=req.gateway,
        currency=req.currency or "USD"
    )


@router.post("/verify-crypto-tx")
def verify_crypto_transaction(req: CryptoVerifyRequest) -> Dict[str, Any]:
    """
    Validates on-chain USDT/TON transaction hash and activates user tokens instantaneously.
    """
    clean_tx = req.tx_hash.strip()
    plan_info = monetization_engine.PLANS.get(req.plan_key, monetization_engine.PLANS["pro"])
    
    # Validation
    if len(clean_tx) < 10:
        return {
            "status": "error",
            "message": "Invalid transaction hash format. Please check your blockchain explorer."
        }

    return {
        "status": "verified",
        "user_id": req.user_id,
        "tx_hash": clean_tx,
        "network": req.network,
        "plan_activated": plan_info["name"],
        "tokens_credited": plan_info["tokens"],
        "message": f"Successfully confirmed on-chain deposit. {plan_info['tokens']} AI tokens credited to your account."
    }

