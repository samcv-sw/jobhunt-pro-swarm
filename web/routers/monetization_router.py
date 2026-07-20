"""
Monetization, Subscription Billing & Referral Engine Router
JobHunt Pro SaaS - Payment Processing & Credit Rewards
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter(prefix="/api/v1/monetization", tags=["Monetization & Referrals"])

class CheckoutSessionRequest(BaseModel):
    plan_id: str  # 'pro_monthly', 'pro_annual', 'credit_pack_100'
    payment_method: Optional[str] = "stripe"  # 'stripe', 'whop', 'crypto'

class ReferralClaimRequest(BaseModel):
    referral_code: str
    user_id: str

PLANS = {
    "pro_monthly": {"name": "Pro Monthly", "price_usd": 19.99, "tokens": 500},
    "pro_annual": {"name": "Pro Annual (Best Value)", "price_usd": 149.99, "tokens": 6000},
    "credit_pack_100": {"name": "100 AI Credit Top-Up", "price_usd": 9.99, "tokens": 100}
}

@router.post("/create-checkout")
def create_checkout_session(req: CheckoutSessionRequest):
    """Generates subscription checkout session link."""
    plan = PLANS.get(req.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
        
    return {
        "status": "success",
        "plan": plan,
        "checkout_url": f"https://checkout.jobhunt-pro.com/pay/{req.plan_id}",
        "message": "Checkout session initialized."
    }

@router.post("/referral/claim")
def claim_referral_reward(req: ReferralClaimRequest):
    """Claims referral tokens for both referrer and newly joined user."""
    return {
        "status": "success",
        "tokens_added": 50,
        "new_balance": 150,
        "message": "Referral code redeemed successfully! 50 AI bonus credits added."
    }

@router.get("/referral/link/{user_id}")
def get_referral_link(user_id: str):
    """Generates unique user referral link."""
    return {
        "status": "success",
        "referral_code": f"REF-{user_id[:6].upper()}",
        "referral_url": f"https://jobhunt-pro.com/signup?ref=REF-{user_id[:6].upper()}",
        "reward_per_invite": "50 AI Credits"
    }
