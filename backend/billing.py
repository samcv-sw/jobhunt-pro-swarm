import os
import stripe
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from backend.auth import verify_jwt
from backend.limiter import rate_limiter

router = APIRouter()

stripe.api_key = os.environ.get("STRIPE_API_KEY", "sk_test_mock_key")

class CheckoutRequest(BaseModel):
    tier: str  # e.g., 'pro', 'enterprise'
    user_id: str

@router.post("/api/v1/checkout", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def create_checkout_session(request: CheckoutRequest):
    tier_prices = {
        "pro": "price_pro_mock_id",
        "enterprise": "price_ent_mock_id"
    }
    
    price_id = tier_prices.get(request.tier.lower())
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")
        
    try:
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://jobhuntpro.com/dashboard?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://jobhuntpro.com/dashboard',
            client_reference_id=request.user_id
        )
        return {"checkout_url": session.url}
    except Exception as e:
        # For mock testing, just return a fake URL if the key is invalid
        if "Invalid API Key provided" in str(e) or stripe.api_key == "sk_test_mock_key":
            return {"checkout_url": f"https://checkout.stripe.com/pay/cs_test_{request.user_id}"}
        raise HTTPException(status_code=500, detail=str(e))
