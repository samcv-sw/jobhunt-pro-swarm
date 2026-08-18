import asyncio
import os

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import verify_jwt
from backend.limiter import rate_limiter

router = APIRouter()

stripe.api_key = os.environ.get("STRIPE_API_KEY")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "https://jhfguf.pythonanywhere.com").rstrip("/")


class CheckoutRequest(BaseModel):
    tier: str  # 'starter', 'basic', 'pro', 'enterprise'
    user_id: str


@router.post("/api/v1/checkout", dependencies=[Depends(rate_limiter)])
async def create_checkout_session(request: CheckoutRequest, payload: dict = Depends(verify_jwt)):
    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    tier_prices = {
        "starter": os.environ.get("STRIPE_PRICE_STARTER", "price_starter_mock_id"),
        "basic": os.environ.get("STRIPE_PRICE_BASIC", "price_basic_mock_id"),
        "pro": os.environ.get("STRIPE_PRICE_PRO", "price_pro_mock_id"),
        "enterprise": os.environ.get("STRIPE_PRICE_ENTERPRISE", "price_ent_mock_id"),
    }

    tier_key = request.tier.lower().strip()
    price_id = tier_prices.get(tier_key)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid subscription or campaign tier")

    if not stripe.api_key:
        # Sovereign MENA / Lebanon Crypto & Direct Card Rails (NOWPayments, ChangeNOW, MoonPay, Wallet)
        return {
            "checkout_url": f"{APP_BASE_URL}/wallet?plan={tier_key}&user_id={user_id}",
            "payment_rails": ["nowpayments", "changenow", "moonpay", "crypto_usdt"],
            "note": "Routed to sovereign crypto & MoonPay card onramp checkout"
        }

    checkout_mode = "subscription" if tier_key == "enterprise" else "payment"

    try:
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode=checkout_mode,
            success_url=f"{APP_BASE_URL}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{APP_BASE_URL}/dashboard",
            client_reference_id=user_id,
        )
        return {"checkout_url": session.url}
    except Exception as e:
        # Secure fallback logic to prevent bypass in production
        is_production = (
            os.environ.get("ENV") == "production" or os.environ.get("INTEGRITY_MODE") == "benchmark"
        )
        is_mock_allowed = os.environ.get("INTEGRITY_MODE") == "development" and not is_production
        if is_mock_allowed and "Invalid API Key provided" in str(e):
            return {"checkout_url": f"{APP_BASE_URL}/dashboard?mock_session={user_id}"}
        raise HTTPException(status_code=500, detail=str(e))
