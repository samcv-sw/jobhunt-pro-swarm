import os
import time
import stripe
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .auth import verify_jwt
from .database import get_db
from .models import Base, SyncOutbox, Account  # Assume Base and Account are imported

# Import the new models defined in models.py (proposed)
# We define them here inline in case they aren't imported or to show their structure.
# They will be proposed in models.py.
from .models import Subscription, Usage

router = APIRouter(prefix="/api/v1", tags=["billing"])

# Stripe setup
stripe.api_key = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_MOCK = os.getenv("STRIPE_MOCK", "true").lower() == "true" or not stripe.api_key

# Subscription Tier Config
SUBSCRIPTION_TIERS: Dict[str, Dict[str, Any]] = {
    "Free": {
        "price_id": None,
        "scraping_limit": 10,
        "cover_letter_limit": 5,
        "price_usd": 0.00
    },
    "Pro": {
        "price_id": os.getenv("STRIPE_PRICE_PRO", "price_pro_mock_123"),
        "scraping_limit": 200,
        "cover_letter_limit": 100,
        "price_usd": 19.00
    },
    "Enterprise": {
        "price_id": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_enterprise_mock_123"),
        "scraping_limit": 999999,  # practically unlimited
        "cover_letter_limit": 999999,
        "price_usd": 99.00
    }
}

class CheckoutRequest(BaseModel):
    tier: str  # "Pro" or "Enterprise"
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    session_id: str
    checkout_url: str
    mocked: bool

async def activate_subscription_locally(
    db: AsyncSession,
    tenant_id: str,
    tier: str,
    stripe_sub_id: Optional[str] = None,
    stripe_cust_id: Optional[str] = None
) -> Subscription:
    """
    Updates or inserts the local SQLite subscription record,
    then logs a mutation to the SyncOutbox table for PostgreSQL syncing.
    """
    now = datetime.now(timezone.utc)
    period_end = now + timedelta(days=30)
    
    # 1. Look up existing subscription
    stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
    result = await db.execute(stmt)
    subscription = result.scalar_one_or_none()
    
    if subscription:
        subscription.tier = tier
        subscription.status = "active"
        subscription.stripe_subscription_id = stripe_sub_id
        subscription.stripe_customer_id = stripe_cust_id
        subscription.current_period_start = now
        subscription.current_period_end = period_end
        subscription.updated_at = now
        op_type = "UPDATE"
    else:
        subscription = Subscription(
            tenant_id=tenant_id,
            tier=tier,
            status="active",
            stripe_subscription_id=stripe_sub_id,
            stripe_customer_id=stripe_cust_id,
            current_period_start=now,
            current_period_end=period_end,
            created_at=now,
            updated_at=now
        )
        db.add(subscription)
        await db.flush()
        op_type = "INSERT"
        
    # 2. Write to local Outbox table so the changes stream to remote cloud PG
    outbox = SyncOutbox(
        table_name="subscriptions",
        record_id=str(subscription.id) if subscription.id else tenant_id,
        operation=op_type,
        payload={
            "id": subscription.id,
            "tenant_id": subscription.tenant_id,
            "stripe_customer_id": subscription.stripe_customer_id,
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "tier": subscription.tier,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "created_at": subscription.created_at.isoformat() if subscription.created_at else now.isoformat(),
            "updated_at": subscription.updated_at.isoformat() if subscription.updated_at else now.isoformat()
        },
        synced=False
    )
    db.add(outbox)
    await db.commit()
    return subscription


async def check_and_increment_usage(
    db: AsyncSession,
    tenant_id: str,
    feature: str,
    amount: int = 1
) -> bool:
    """
    Validates user usage against active tier limits.
    Increments count locally and creates outbox log if allowed.
    """
    # 1. Fetch active subscription
    stmt_sub = select(Subscription).where(Subscription.tenant_id == tenant_id)
    result_sub = await db.execute(stmt_sub)
    sub = result_sub.scalar_one_or_none()
    
    tier = "Free"
    current_period_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_period_end = current_period_start + timedelta(days=30)
    
    if sub and sub.status == "active":
        tier = sub.tier
        if sub.current_period_start:
            current_period_start = sub.current_period_start
        if sub.current_period_end:
            current_period_end = sub.current_period_end
            
    tier_config = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["Free"])
    limit = tier_config.get(f"{feature}_limit", 0)
    
    # 2. Fetch usage within current billing period
    stmt_usage = select(Usage).where(
        Usage.tenant_id == tenant_id,
        Usage.feature == feature,
        Usage.billing_period_start == current_period_start
    )
    result_usage = await db.execute(stmt_usage)
    usage_rec = result_usage.scalar_one_or_none()
    
    current_count = usage_rec.count if usage_rec else 0
    
    if current_count + amount > limit:
        return False
        
    # 3. Update or Insert usage record
    if usage_rec:
        usage_rec.count += amount
        usage_rec.updated_at = datetime.now(timezone.utc)
        op_type = "UPDATE"
    else:
        usage_rec = Usage(
            tenant_id=tenant_id,
            feature=feature,
            count=amount,
            billing_period_start=current_period_start,
            billing_period_end=current_period_end,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(usage_rec)
        await db.flush()
        op_type = "INSERT"
        
    # 4. Stream mutation to cloud Postgres via outbox
    outbox = SyncOutbox(
        table_name="usages",
        record_id=str(usage_rec.id) if usage_rec.id else f"{tenant_id}_{feature}_{current_period_start.isoformat()}",
        operation=op_type,
        payload={
            "id": usage_rec.id,
            "tenant_id": usage_rec.tenant_id,
            "feature": usage_rec.feature,
            "count": usage_rec.count,
            "billing_period_start": usage_rec.billing_period_start.isoformat(),
            "billing_period_end": usage_rec.billing_period_end.isoformat(),
            "created_at": usage_rec.created_at.isoformat() if usage_rec.created_at else None,
            "updated_at": usage_rec.updated_at.isoformat() if usage_rec.updated_at else None
        },
        synced=False
    )
    db.add(outbox)
    await db.commit()
    return True


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    req: CheckoutRequest,
    jwt_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a Stripe checkout session or a mocked simulation session.
    """
    tenant_id = jwt_payload.get("user_id") or jwt_payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token: Missing tenant_id/user_id")
        
    tier = req.tier
    if tier not in ["Pro", "Enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid subscription tier requested")
        
    price_id = SUBSCRIPTION_TIERS[tier]["price_id"]
    
    # Check if Stripe Mock Mode is Enabled
    if STRIPE_MOCK:
        # Mock Session URL routing to mock-checkout-redirect
        # When triggered, this endpoint will update the database directly to simulate a successful purchase callback.
        mock_session_id = f"mock_sess_{int(time.time())}_{tenant_id}"
        mock_redirect_url = (
            f"http://localhost:8000/api/v1/billing/mock-checkout-redirect?"
            f"tenant_id={tenant_id}&tier={tier}&success_url={req.success_url}"
        )
        return CheckoutResponse(
            session_id=mock_session_id,
            checkout_url=mock_redirect_url,
            mocked=True
        )
        
    try:
        # 1. Get or Create Stripe Customer
        stmt_sub = select(Subscription).where(Subscription.tenant_id == tenant_id)
        res_sub = await db.execute(stmt_sub)
        sub = res_sub.scalar_one_or_none()
        
        customer_id = sub.stripe_customer_id if sub else None
        if not customer_id:
            # Look up email in JWT payload or fallback
            email = jwt_payload.get("email", f"{tenant_id}@local-jobhunt.pro")
            stripe_customer = stripe.Customer.create(
                email=email,
                metadata={"tenant_id": tenant_id}
            )
            customer_id = stripe_customer.id
            
        # 2. Create Stripe Checkout Session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=req.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url,
            metadata={
                "tenant_id": tenant_id,
                "tier": tier
            }
        )
        return CheckoutResponse(
            session_id=session.id,
            checkout_url=session.url,
            mocked=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stripe Session Creation Failed: {str(e)}"
        )


@router.get("/billing/mock-checkout-redirect")
async def mock_checkout_redirect(
    tenant_id: str,
    tier: str,
    success_url: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Simulation redirect that directly updates user sub status,
    mimicking webhook activation in non-production/offline setups.
    """
    await activate_subscription_locally(
        db=db,
        tenant_id=tenant_id,
        tier=tier,
        stripe_sub_id=f"mock_sub_{int(time.time())}",
        stripe_cust_id=f"mock_cust_{int(time.time())}"
    )
    # Redirect back to user success URL
    return RedirectResponse(url=success_url)


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Listens to incoming Stripe Webhook events and manages lifecycle.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature verification")
        
    event_type = event["type"]
    data_object = event["data"]["object"]
    
    if event_type == "checkout.session.completed":
        session = data_object
        tenant_id = session.get("metadata", {}).get("tenant_id")
        tier = session.get("metadata", {}).get("tier", "Pro")
        stripe_sub_id = session.get("subscription")
        stripe_cust_id = session.get("customer")
        
        if tenant_id:
            await activate_subscription_locally(
                db=db,
                tenant_id=tenant_id,
                tier=tier,
                stripe_sub_id=stripe_sub_id,
                stripe_cust_id=stripe_cust_id
            )
            
    elif event_type in ["customer.subscription.updated", "customer.subscription.deleted"]:
        subscription = data_object
        stripe_sub_id = subscription.get("id")
        stripe_cust_id = subscription.get("customer")
        status_str = subscription.get("status")
        
        # Look up sub by stripe subscription id or customer
        stmt = select(Subscription).where(
            (Subscription.stripe_subscription_id == stripe_sub_id) | 
            (Subscription.stripe_customer_id == stripe_cust_id)
        )
        res = await db.execute(stmt)
        local_sub = res.scalar_one_or_none()
        
        if local_sub:
            tenant_id = local_sub.tenant_id
            
            # Map Stripe statuses to tiers
            if event_type == "customer.subscription.deleted" or status_str in ["canceled", "unpaid"]:
                tier = "Free"
                local_sub.status = "canceled"
            else:
                # Keep active, resolve updated tier if tier was changed
                # Stripe metadata can hold the tier
                tier = subscription.get("metadata", {}).get("tier", local_sub.tier)
                local_sub.status = "active"
                
            period_end = datetime.fromtimestamp(subscription.get("current_period_end", time.time() + 86400 * 30), timezone.utc)
            period_start = datetime.fromtimestamp(subscription.get("current_period_start", time.time()), timezone.utc)
            
            local_sub.tier = tier
            local_sub.current_period_start = period_start
            local_sub.current_period_end = period_end
            local_sub.updated_at = datetime.now(timezone.utc)
            
            # Push changes to sync outbox
            outbox = SyncOutbox(
                table_name="subscriptions",
                record_id=str(local_sub.id),
                operation="UPDATE",
                payload={
                    "id": local_sub.id,
                    "tenant_id": local_sub.tenant_id,
                    "stripe_customer_id": local_sub.stripe_customer_id,
                    "stripe_subscription_id": local_sub.stripe_subscription_id,
                    "tier": local_sub.tier,
                    "status": local_sub.status,
                    "current_period_start": local_sub.current_period_start.isoformat(),
                    "current_period_end": local_sub.current_period_end.isoformat(),
                    "updated_at": local_sub.updated_at.isoformat()
                },
                synced=False
            )
            db.add(outbox)
            await db.commit()
            
    return {"status": "success"}
