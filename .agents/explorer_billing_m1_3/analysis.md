# Stripe Billing Integration Strategy - JobHunt Pro

## Executive Summary
This document defines the integration strategy for Stripe API and subscription billing inside the JobHunt Pro backend. It addresses the definition of subscription tiers (Free, Pro, Enterprise), enforcement of usage limits for scraping and cover letter generation, design of API endpoints for Checkout and Webhooks (with a complete local mock mode fallback), and specific instructions for database updates adhering to the Local-First Outbox Synchronization architecture.

---

## 1. Existing System Architecture Analysis

### 1.1 FastAPI Structure (`backend/main.py`)
- **Routing**: API endpoints (e.g. `/api/v1/scrape`, `/api/v1/generate-cover-letter`) handle client requests, queue Celery tasks, and return immediate status responses.
- **Authentication**: JWT token verification is handled via the `verify_jwt` dependency in `backend/auth.py`. When parsed, it returns the decoded token payload where the `"sub"` claim represents the user's `tenant_id`.
- **Database Context**: Endpoint logic opens database sessions using the local-first SQLite session manager (`async_session` in `backend/database.py`).

### 1.2 Local-First SQLite Database & Outbox Pattern (`backend/models.py`)
- **Current Tables**:
  - `Account`: Stores balance and status information mapped to `tenant_id`.
  - `Transaction`: Records financial ledger actions.
  - `LedgerEntry`: Details transaction debits/credits.
  - `SyncOutbox` (`ps_crud_outbox`): Stores local mutations (INSERT, UPDATE, DELETE) which are pushed asynchronously to cloud Neon Postgres by `sync_worker.py` every 5 seconds.
- **Key Insight**: To maintain consistency between local and cloud databases, any billing and subscription changes applied locally to the `Account` table MUST write a corresponding event log to the `SyncOutbox` table.

---

## 2. Subscription Tiers & Limit Enforcement Design

### 2.1 Tier Definitions and Constraints
We define three subscription plans:
1. **FREE**: $0/month. Limit: 5 scrapes and 5 cover letters per monthly cycle.
2. **PRO**: $19/month. Limit: 100 scrapes and 100 cover letters per monthly cycle.
3. **ENTERPRISE**: $99/month. Limit: 999,999 scrapes and 999,999 cover letters per monthly cycle (unlimited).

### 2.2 Model Schema Updates (`backend/models.py`)
To store subscription statuses and track usage counters, the `Account` database model is extended with the following columns:

```python
# To be added to backend/models.py (under Class Account)
subscription_tier = Column(String, default="FREE", nullable=False)
subscription_status = Column(String, default="active", nullable=False) # active, trialing, unpaid, past_due, canceled
stripe_customer_id = Column(String, unique=True, index=True, nullable=True)
stripe_subscription_id = Column(String, unique=True, index=True, nullable=True)
subscription_period_end = Column(DateTime, nullable=True)
scrapes_used = Column(Integer, default=0, nullable=False)
cover_letters_used = Column(Integer, default=0, nullable=False)
cycle_reset_at = Column(DateTime, nullable=True)
```

### 2.3 Limits Verification and Auto-Reset Flow
1. **Dynamic Check**: When a user triggers an action (scrape or cover letter generation), a check is run. If the active time exceeds `cycle_reset_at`, the counters `scrapes_used` and `cover_letters_used` are reset to `0`, and `cycle_reset_at` is pushed forward 30 days.
2. **Tier Grace Downgrades**: If a subscription's status is not `"active"` or `"trialing"`, the user's tier is temporarily evaluated as `FREE` for limit-enforcement, regardless of their stored `subscription_tier` string.
3. **HTTP 402 Handling**: If usage exceeds limits, a `402 Payment Required` exception is raised, requesting an upgrade.

---

## 3. Stripe Integration Design (`backend/billing.py`)

A new module `backend/billing.py` will be created to house all billing operations, Checkout Session generation, Webhook processing, limit verification utilities, and the developer mock system.

### 3.1 Complete Module Implementation
Below is the complete, production-ready source code for `backend/billing.py` containing no placeholder implementation details.

```python
import os
import enum
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel, Field
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import get_db
from .models import Account, SyncOutbox
from .auth import verify_jwt

logger = logging.getLogger(__name__)

# Config Env Vars
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_MOCK_ENABLED = os.environ.get("STRIPE_MOCK_ENABLED", "false").lower() in ("true", "1", "yes")

# Auto-enable Mock mode if credentials are missing
if not STRIPE_SECRET_KEY or STRIPE_SECRET_KEY.startswith("mock_"):
    STRIPE_MOCK_ENABLED = True
else:
    stripe.api_key = STRIPE_SECRET_KEY

class SubscriptionTier(str, enum.Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

# Stripe Price IDs mapped to Tiers
TIER_PRICES = {
    SubscriptionTier.FREE: None,
    SubscriptionTier.PRO: os.environ.get("STRIPE_PRICE_PRO", "price_1mock_pro_1900"),
    SubscriptionTier.ENTERPRISE: os.environ.get("STRIPE_PRICE_ENTERPRISE", "price_1mock_ent_9900"),
}

# Plan limits
TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "max_scrapes_per_month": 5,
        "max_cover_letters_per_month": 5,
    },
    SubscriptionTier.PRO: {
        "max_scrapes_per_month": 100,
        "max_cover_letters_per_month": 100,
    },
    SubscriptionTier.ENTERPRISE: {
        "max_scrapes_per_month": 999999,
        "max_cover_letters_per_month": 999999,
    }
}

class CheckoutRequest(BaseModel):
    tier: SubscriptionTier
    success_url: str
    cancel_url: str

router = APIRouter(tags=["billing"])

@router.post("/api/v1/checkout", dependencies=[Depends(verify_jwt)])
async def create_checkout_session(
    req: CheckoutRequest,
    token_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a Stripe Checkout Session for subscription tier purchase.
    If STRIPE_MOCK_ENABLED is True, generates a mock checkout redirection URL.
    """
    tenant_id = token_payload.get("sub")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token payload is missing sub claim (tenant_id)"
        )

    if req.tier == SubscriptionTier.FREE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create a checkout session for the FREE tier."
        )

    price_id = TIER_PRICES.get(req.tier)
    if not price_id and not STRIPE_MOCK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe Price ID for tier {req.tier.value} is not configured."
        )

    # Resolve or initialize account
    result = await db.execute(select(Account).where(Account.tenant_id == tenant_id))
    account = result.scalars().first()
    
    if not account:
        account = Account(
            tenant_id=tenant_id,
            currency="USD",
            balance_cents=0,
            status="ACTIVE",
            subscription_tier=SubscriptionTier.FREE.value,
            subscription_status="active"
        )
        db.add(account)
        await db.flush()
        
        # Log local outbox
        outbox = SyncOutbox(
            table_name="accounts",
            record_id=str(account.id),
            operation="INSERT",
            payload={
                "id": account.id,
                "tenant_id": account.tenant_id,
                "currency": account.currency,
                "balance_cents": account.balance_cents,
                "subscription_tier": account.subscription_tier,
                "subscription_status": account.subscription_status
            },
            synced=False
        )
        db.add(outbox)
        await db.commit()

    # Handle Mock mode fallback
    if STRIPE_MOCK_ENABLED:
        logger.info(f"[MOCK MODE] Generating mock checkout session for tenant={tenant_id}, tier={req.tier.value}")
        mock_session_id = f"mock_sess_{tenant_id}_{int(datetime.now(timezone.utc).timestamp())}"
        
        # Generates redirect URL that invokes a dev helper path to finalize mock subscription
        mock_checkout_url = (
            f"/api/v1/checkout/mock-success?tenant_id={tenant_id}"
            f"&tier={req.tier.value}&session_id={mock_session_id}"
            f"&success_url={req.success_url}"
        )
        return {
            "checkout_url": mock_checkout_url,
            "session_id": mock_session_id,
            "is_mock": True
        }

    # Live Stripe mode
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=req.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=req.cancel_url,
            client_reference_id=tenant_id,
            customer_email=token_payload.get("email"),
            metadata={
                "tenant_id": tenant_id,
                "tier": req.tier.value
            }
        )
        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "is_mock": False
        }
    except Exception as e:
        logger.error(f"Failed to generate Stripe checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe session creation failed: {str(e)}"
        )

@router.get("/api/v1/checkout/mock-success")
async def mock_checkout_success(
    tenant_id: str,
    tier: str,
    session_id: str,
    success_url: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Developer-only endpoint to process and redirect mock checkouts.
    Immediately upgrades DB and redirects browser to success_url.
    """
    if not STRIPE_MOCK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock checkout helper is only accessible in development mock mode."
        )

    logger.info(f"[MOCK MODE] Mock checkout activation: tenant={tenant_id}, tier={tier}")
    
    result = await db.execute(select(Account).where(Account.tenant_id == tenant_id))
    account = result.scalars().first()
    
    if not account:
        account = Account(
            tenant_id=tenant_id,
            currency="USD",
            balance_cents=0,
            status="ACTIVE"
        )
        db.add(account)
        await db.flush()

    # Update subscription
    account.subscription_tier = tier
    account.subscription_status = "active"
    account.stripe_subscription_id = f"sub_mock_{session_id}"
    account.stripe_customer_id = f"cus_mock_{tenant_id}"
    period_end = datetime.now(timezone.utc) + timedelta(days=30)
    account.subscription_period_end = period_end
    account.cycle_reset_at = period_end

    outbox = SyncOutbox(
        table_name="accounts",
        record_id=str(account.id),
        operation="UPDATE",
        payload={
            "id": account.id,
            "tenant_id": account.tenant_id,
            "subscription_tier": account.subscription_tier,
            "subscription_status": account.subscription_status,
            "stripe_subscription_id": account.stripe_subscription_id,
            "stripe_customer_id": account.stripe_customer_id,
            "subscription_period_end": account.subscription_period_end.isoformat(),
            "cycle_reset_at": account.cycle_reset_at.isoformat()
        },
        synced=False
    )
    db.add(outbox)
    await db.commit()

    return RedirectResponse(url=success_url)

@router.post("/api/v1/webhook/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handles inbound Stripe Webhook events.
    Skips signature validation if mock mode is active.
    """
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    event = None

    if STRIPE_MOCK_ENABLED:
        logger.info("[MOCK MODE] Decoding webhook payload directly.")
        try:
            event_data = json.loads(payload.decode("utf-8"))
            event = stripe.Event.construct_from(event_data, key=None)
        except Exception as e:
            logger.error(f"Failed to decode mock payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Malformed mock payload: {str(e)}"
            )
    else:
        if not STRIPE_WEBHOOK_SECRET:
            logger.error("STRIPE_WEBHOOK_SECRET env var is missing.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Webhook secret not configured on backend."
            )
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload structure"
            )
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Signature verification failed"
            )

    event_type = event.get("type")
    logger.info(f"Processing Stripe Webhook Event: {event_type}")

    if event_type == "checkout.session.completed":
        session = event.get("data", {}).get("object", {})
        await handle_checkout_session_completed(session, db)
    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        subscription = event.get("data", {}).get("object", {})
        await handle_subscription_updated(subscription, db)
    elif event_type == "customer.subscription.deleted":
        subscription = event.get("data", {}).get("object", {})
        await handle_subscription_deleted(subscription, db)
    else:
        logger.debug(f"Unhandled Stripe webhook event type: {event_type}")

    return {"status": "success"}

@router.post("/api/v1/webhook/stripe/mock-trigger")
async def mock_stripe_webhook_trigger(
    event_type: str,
    tenant_id: str,
    tier: Optional[SubscriptionTier] = SubscriptionTier.PRO,
    db: AsyncSession = Depends(get_db)
):
    """
    Developer test utility to trigger simulated subscription states.
    Available exclusively in development mock environments.
    """
    if not STRIPE_MOCK_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock webhook trigger is only available when STRIPE_MOCK_ENABLED is True."
        )

    logger.info(f"[MOCK MODE] Simulated webhook triggered: {event_type} for tenant={tenant_id}")
    
    mock_id = f"evt_mock_{int(datetime.now(timezone.utc).timestamp())}"
    mock_sub_id = f"sub_mock_{tenant_id}"
    mock_cus_id = f"cus_mock_{tenant_id}"
    
    if event_type == "checkout.session.completed":
        obj = {
            "id": f"cs_mock_{tenant_id}",
            "client_reference_id": tenant_id,
            "customer": mock_cus_id,
            "subscription": mock_sub_id,
            "metadata": {
                "tenant_id": tenant_id,
                "tier": tier.value
            }
        }
        await handle_checkout_session_completed(obj, db)
        
    elif event_type in ("customer.subscription.created", "customer.subscription.updated"):
        obj = {
            "id": mock_sub_id,
            "customer": mock_cus_id,
            "status": "active",
            "current_period_end": int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp()),
            "metadata": {
                "tier": tier.value
            }
        }
        await handle_subscription_updated(obj, db)
        
    elif event_type == "customer.subscription.deleted":
        obj = {
            "id": mock_sub_id,
            "customer": mock_cus_id,
            "status": "canceled"
        }
        await handle_subscription_deleted(obj, db)
        
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported mock event type: {event_type}"
        )
        
    return {"status": "triggered", "event_id": mock_id, "type": event_type}


# Webhook Handlers
async def handle_checkout_session_completed(session: dict, db: AsyncSession):
    tenant_id = session.get("client_reference_id")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    
    metadata = session.get("metadata", {})
    if not tenant_id:
        tenant_id = metadata.get("tenant_id")
        
    tier = metadata.get("tier", SubscriptionTier.PRO.value)

    if not tenant_id:
        logger.error(f"No tenant_id mapped to Stripe Checkout Session {session.get('id')}")
        return

    result = await db.execute(select(Account).where(Account.tenant_id == tenant_id))
    account = result.scalars().first()
    
    if not account:
        account = Account(
            tenant_id=tenant_id,
            currency="USD",
            balance_cents=0,
            status="ACTIVE"
        )
        db.add(account)
        await db.flush()

    account.stripe_customer_id = customer_id
    account.stripe_subscription_id = subscription_id
    account.subscription_tier = tier
    account.subscription_status = "active"

    outbox = SyncOutbox(
        table_name="accounts",
        record_id=str(account.id),
        operation="UPDATE",
        payload={
            "id": account.id,
            "tenant_id": account.tenant_id,
            "stripe_customer_id": account.stripe_customer_id,
            "stripe_subscription_id": account.stripe_subscription_id,
            "subscription_tier": account.subscription_tier,
            "subscription_status": account.subscription_status
        },
        synced=False
    )
    db.add(outbox)
    await db.commit()
    logger.info(f"Checkout completed. Upgraded tenant={tenant_id} to tier={tier}")


async def handle_subscription_updated(subscription: dict, db: AsyncSession):
    subscription_id = subscription.get("id")
    customer_id = subscription.get("customer")
    status_str = subscription.get("status")
    period_end_ts = subscription.get("current_period_end")
    
    metadata = subscription.get("metadata", {})
    tier = metadata.get("tier")
    
    if not tier:
        items = subscription.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
            for t, p_id in TIER_PRICES.items():
                if p_id == price_id:
                    tier = t.value
                    break
    
    if not tier:
        tier = SubscriptionTier.PRO.value

    result = await db.execute(
        select(Account).where(
            (Account.stripe_subscription_id == subscription_id) | 
            (Account.stripe_customer_id == customer_id)
        )
    )
    account = result.scalars().first()
    
    if not account:
        logger.error(f"Subscription event lookup failed for sub={subscription_id}, customer={customer_id}")
        return

    account.stripe_subscription_id = subscription_id
    account.stripe_customer_id = customer_id
    account.subscription_tier = tier
    account.subscription_status = status_str
    
    if period_end_ts:
        period_dt = datetime.fromtimestamp(period_end_ts, tz=timezone.utc)
        account.subscription_period_end = period_dt
        account.cycle_reset_at = period_dt

    outbox = SyncOutbox(
        table_name="accounts",
        record_id=str(account.id),
        operation="UPDATE",
        payload={
            "id": account.id,
            "tenant_id": account.tenant_id,
            "stripe_subscription_id": account.stripe_subscription_id,
            "stripe_customer_id": account.stripe_customer_id,
            "subscription_tier": account.subscription_tier,
            "subscription_status": account.subscription_status,
            "subscription_period_end": account.subscription_period_end.isoformat() if account.subscription_period_end else None,
            "cycle_reset_at": account.cycle_reset_at.isoformat() if account.cycle_reset_at else None
        },
        synced=False
    )
    db.add(outbox)
    await db.commit()
    logger.info(f"Subscription updated: sub={subscription_id}, status={status_str}")


async def handle_subscription_deleted(subscription: dict, db: AsyncSession):
    subscription_id = subscription.get("id")
    
    result = await db.execute(select(Account).where(Account.stripe_subscription_id == subscription_id))
    account = result.scalars().first()
    
    if not account:
        logger.error(f"Deletion event lookup failed for sub={subscription_id}")
        return

    account.subscription_tier = SubscriptionTier.FREE.value
    account.subscription_status = "canceled"
    account.subscription_period_end = None

    outbox = SyncOutbox(
        table_name="accounts",
        record_id=str(account.id),
        operation="UPDATE",
        payload={
            "id": account.id,
            "tenant_id": account.tenant_id,
            "subscription_tier": account.subscription_tier,
            "subscription_status": account.subscription_status,
            "subscription_period_end": None
        },
        synced=False
    )
    db.add(outbox)
    await db.commit()
    logger.info(f"Subscription deleted. Downgraded tenant={account.tenant_id} to FREE.")


# Check and Increment Usage Helper
async def check_and_increment_usage(
    tenant_id: str,
    action: str,  # "scrapes" or "cover_letters"
    db: AsyncSession
) -> bool:
    """
    Validates user usage limit. If within bounds, increments counter and syncs state.
    """
    result = await db.execute(select(Account).where(Account.tenant_id == tenant_id))
    account = result.scalars().first()
    
    if not account:
        # Create an account immediately with FREE defaults
        account = Account(
            tenant_id=tenant_id,
            currency="USD",
            balance_cents=0,
            status="ACTIVE",
            subscription_tier=SubscriptionTier.FREE.value,
            subscription_status="active",
            scrapes_used=0,
            cover_letters_used=0,
            cycle_reset_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db.add(account)
        await db.flush()
        
        outbox = SyncOutbox(
            table_name="accounts",
            record_id=str(account.id),
            operation="INSERT",
            payload={
                "id": account.id,
                "tenant_id": account.tenant_id,
                "subscription_tier": account.subscription_tier,
                "subscription_status": account.subscription_status,
                "scrapes_used": account.scrapes_used,
                "cover_letters_used": account.cover_letters_used,
                "cycle_reset_at": account.cycle_reset_at.isoformat()
            },
            synced=False
        )
        db.add(outbox)

    # Check reset
    now = datetime.now(timezone.utc)
    # Ensure cycle_reset_at is timezone-aware
    reset_dt = account.cycle_reset_at
    if reset_dt:
        if reset_dt.tzinfo is None:
            reset_dt = reset_dt.replace(tzinfo=timezone.utc)
        if reset_dt < now:
            account.scrapes_used = 0
            account.cover_letters_used = 0
            account.cycle_reset_at = now + timedelta(days=30)

    # Downgrade evaluation if subscription is unpaid/past_due/expired
    active_tier = SubscriptionTier(account.subscription_tier)
    if account.subscription_status not in ("active", "trialing"):
        active_tier = SubscriptionTier.FREE

    limits = TIER_LIMITS[active_tier]

    if action == "scrapes":
        max_allowed = limits["max_scrapes_per_month"]
        if account.scrapes_used >= max_allowed:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Scraping limit of {max_allowed} exceeded for tier {active_tier.value}. Please upgrade."
            )
        account.scrapes_used += 1
    elif action == "cover_letters":
        max_allowed = limits["max_cover_letters_per_month"]
        if account.cover_letters_used >= max_allowed:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Cover letter generation limit of {max_allowed} exceeded for tier {active_tier.value}. Please upgrade."
            )
        account.cover_letters_used += 1
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown verification action: {action}"
        )

    outbox = SyncOutbox(
        table_name="accounts",
        record_id=str(account.id),
        operation="UPDATE",
        payload={
            "id": account.id,
            "tenant_id": account.tenant_id,
            "scrapes_used": account.scrapes_used,
            "cover_letters_used": account.cover_letters_used,
            "cycle_reset_at": account.cycle_reset_at.isoformat() if account.cycle_reset_at else None
        },
        synced=False
    )
    db.add(outbox)
    await db.commit()
    return True
```

---

## 4. Specific Code Change Proposals

### 4.1 Changes to `backend/models.py`
Add the subscription columns to the `Account` model.

**Before (Lines 17-26):**
```python
class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    currency = Column(String, default="CREDITS")
    balance_cents = Column(Integer, default=0) 
    locked_cents = Column(Integer, default=0)  
    status = Column(String, default="ACTIVE")
```

**After:**
```python
class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    currency = Column(String, default="CREDITS")
    balance_cents = Column(Integer, default=0) 
    locked_cents = Column(Integer, default=0)  
    status = Column(String, default="ACTIVE")

    # Subscription updates
    subscription_tier = Column(String, default="FREE", nullable=False)
    subscription_status = Column(String, default="active", nullable=False)
    stripe_customer_id = Column(String, unique=True, index=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=True)
    subscription_period_end = Column(DateTime, nullable=True)
    scrapes_used = Column(Integer, default=0, nullable=False)
    cover_letters_used = Column(Integer, default=0, nullable=False)
    cycle_reset_at = Column(DateTime, nullable=True)
```

---

### 4.2 Changes to `backend/main.py`
Modify `backend/main.py` to:
1. Import and mount the `billing` router.
2. Inject usage limits verification checks into the `/api/v1/scrape`, `/api/v1/generate-cover-letter`, and `/api/v1/ai/generate-cover-letter/stream` endpoints.

#### 4.2.1 Router Integration
**Before (Lines 1-17):**
```python
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .websocket import manager
from .tasks import scrape_jobs, generate_cover_letter
from .database import async_session
from .models import Account, SyncOutbox
from .auth import verify_jwt
from .ai_engine import generate_smart_cover_letter_stream

app = FastAPI(
    title="JobHunt Pro Enterprise API",
    description="Enterprise API powering autonomous AI Agents with Celery Task Queues.",
    version="3.0.0"
)
```

**After:**
```python
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .websocket import manager
from .tasks import scrape_jobs, generate_cover_letter
from .database import async_session, get_db
from .models import Account, SyncOutbox
from .auth import verify_jwt
from .ai_engine import generate_smart_cover_letter_stream
from .billing import router as billing_router, check_and_increment_usage
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI(
    title="JobHunt Pro Enterprise API",
    description="Enterprise API powering autonomous AI Agents with Celery Task Queues.",
    version="3.0.0"
)

# Register the billing routes (Checkout, Webhooks, Mock Trigger)
app.include_router(billing_router)
```

#### 4.2.2 Endpoints Limit Verification
Update endpoints to extract the token payload and run `check_and_increment_usage`.

##### `/api/v1/scrape` Endpoint
**Before (Lines 49-55):**
```python
@app.post("/api/v1/scrape", dependencies=[Depends(verify_jwt)])
async def trigger_scrape(req: ScrapeRequest, request: Request = None):
    """
    Instantly returns 200 OK and sends the scraping task to Celery.
    """
    task = await asyncio.to_thread(scrape_jobs.delay, req.target_urls, req.user_id)
    return {"status": "queued", "task_id": task.id}
```

**After:**
```python
@app.post("/api/v1/scrape")
async def trigger_scrape(
    req: ScrapeRequest, 
    request: Request = None, 
    token_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies subscription scraping limits, increments count, and dispatches task to Celery.
    """
    tenant_id = token_payload.get("sub", req.user_id) # Falls back to payload claim
    
    # 1. Enforce usage limits
    await check_and_increment_usage(tenant_id=tenant_id, action="scrapes", db=db)
    
    # 2. Queue background task
    task = await asyncio.to_thread(scrape_jobs.delay, req.target_urls, tenant_id)
    return {"status": "queued", "task_id": task.id}
```

##### `/api/v1/generate-cover-letter` Endpoint
**Before (Lines 57-60):**
```python
@app.post("/api/v1/generate-cover-letter", dependencies=[Depends(verify_jwt)])
async def trigger_cover_letter(req: CoverLetterRequest, request: Request = None):
    task = await asyncio.to_thread(generate_cover_letter.delay, req.job_description, req.user_cv)
    return {"status": "queued", "task_id": task.id}
```

**After:**
```python
@app.post("/api/v1/generate-cover-letter")
async def trigger_cover_letter(
    req: CoverLetterRequest, 
    request: Request = None,
    token_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies subscription cover letter limits, increments count, and dispatches generation task.
    """
    tenant_id = token_payload.get("sub")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="JWT payload is missing sub claim.")

    # 1. Enforce usage limits
    await check_and_increment_usage(tenant_id=tenant_id, action="cover_letters", db=db)
    
    # 2. Queue background task
    task = await asyncio.to_thread(generate_cover_letter.delay, req.job_description, req.user_cv)
    return {"status": "queued", "task_id": task.id}
```

##### `/api/v1/ai/generate-cover-letter/stream` Endpoint
**Before (Lines 62-67):**
```python
@app.post("/api/v1/ai/generate-cover-letter/stream", dependencies=[Depends(verify_jwt)])
async def stream_cover_letter(req: CoverLetterRequest, request: Request = None):
    return StreamingResponse(
        generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
        media_type="text/event-stream"
    )
```

**After:**
```python
@app.post("/api/v1/ai/generate-cover-letter/stream")
async def stream_cover_letter(
    req: CoverLetterRequest, 
    request: Request = None,
    token_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies subscription cover letter limits, increments count, and streams response.
    """
    tenant_id = token_payload.get("sub")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="JWT payload is missing sub claim.")

    # 1. Enforce usage limits
    await check_and_increment_usage(tenant_id=tenant_id, action="cover_letters", db=db)
    
    # 2. Return streaming generator response
    return StreamingResponse(
        generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
        media_type="text/event-stream"
    )
```

---

### 4.3 Changes to `requirements.txt`
Add `stripe` to requirements to ensure the Python Stripe SDK is installed:
```text
stripe>=9.0.0
```

---

## 5. Local Development & Mock Validation Guide
Since network presence or Stripe access credentials might be absent in development environments, mock mode acts as a functional sandbox.

### 5.1 Verification Checklist
1. **No Stripe Key Mode**: Leave `STRIPE_SECRET_KEY` empty or set to `mock_secret_key`. Setting `STRIPE_MOCK_ENABLED=True` forces the fallback.
2. **Checkout Flow**: 
   - Post to `/api/v1/checkout` requesting the `PRO` plan.
   - Assert the endpoint returns `"is_mock": true` and a `checkout_url` path mapping to `/api/v1/checkout/mock-success?...`.
   - Accessing `/api/v1/checkout/mock-success` redirects the client browser, upgrades the database record immediately, and records a SyncOutbox UPDATE row for PostgreSQL.
3. **Simulating Stripe Actions**:
   - Issue a HTTP POST to `/api/v1/webhook/stripe/mock-trigger` with `event_type="customer.subscription.deleted"` and `tenant_id="test_user"`.
   - Verify the database row for `"test_user"` is downgraded to `"FREE"` and status is changed to `"canceled"`.
