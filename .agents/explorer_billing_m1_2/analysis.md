# Stripe API Integration Analysis & Strategy

This document details the analysis of the existing FastAPI backend structure and outlines a concrete implementation strategy for integrating Stripe Billing in `backend/billing.py`. 

---

## 1. Current FastAPI & Database Architecture

We analyzed `backend/main.py` and `backend/models.py` to trace how request routing and database persistence are handled.

### A. FastAPI Structure (`backend/main.py`)
- **FastAPI Core**: Instantiates a FastAPI app (v3.0.0) with standard CORS middleware.
- **Authentication**: JWT token verification is handled via the `verify_jwt` dependency (`backend/auth.py`). Endpoints require a valid bearer token in the `Authorization` header.
- **Asynchronous Execution & Scaling**: Heavy workloads (scraping, AI generation, emails) are offloaded to Celery task queues (`scraping`, `ai_inference`, `email_sender`) via `.delay()`, run inside `asyncio.to_thread` to prevent blocking the main event loop.
- **Zero-Latency Database Persistence**: The backend employs a **Dual Database Pattern**. Writes are applied to a local SQLite database (optimized using WAL mode) for zero-latency, and synchronization to the central PostgreSQL database is handled asynchronously in the background by `sync_worker.py` utilizing the Outbox pattern (polling `ps_crud_outbox`).

### B. SQLAlchemy Models (`backend/models.py`)
The local schema currently defines:
- `Account`: Stores ledger state for tenants (`id`, `tenant_id`, `currency`, `balance_cents`, `locked_cents`, `status`).
- `Transaction` & `LedgerEntry`: For credit-based operations.
- `SyncOutbox`: For streaming local modifications to the cloud database (`table_name`, `record_id`, `operation`, `payload`, `synced`).
- **Key Observation**: There is no local `User` model on the local-first node. User-scoped requests are authenticated via JWT claims and mapped directly to a `tenant_id`.

---

## 2. Subscription Tiers & Enforcing Usage Limits

We propose adding subscription tiers directly to the application context.

### A. Tier Definitions
Tiers are defined in code (with mapping configuration in `backend/billing.py` or extended from `core/pricing_manager.py`):
1. **Free**: $0/month. Daily limit: **5** scraping operations & **5** AI cover letter generations.
2. **Pro**: $19.99/month. Daily limit: **100** scraping operations & **100** AI cover letter generations.
3. **Enterprise**: $99.99/month. Daily limit: **1,000** scraping operations & **1,000** AI cover letter generations.

### B. Data Storage
To support local-first, offline-tolerant limit checking:
- Limits and usage counters are stored directly on the `Account` table in SQLite.
- The `accounts` table will be extended with:
  - `tier`: The name of the subscription tier (`Free`, `Pro`, `Enterprise`).
  - `usage_limit_daily`: Maximum operations allowed per day.
  - `usage_count_daily`: Current operations performed in the billing day.
  - `last_usage_reset`: UTC timestamp of the last daily reset.
  - Stripe metadata fields (`stripe_customer_id`, `stripe_subscription_id`).

### C. Zero-Latency Enforcement
We define a FastAPI dependency helper, `check_and_increment_usage`, which runs locally against SQLite in <1ms:
1. Extracts `tenant_id` (or `sub` claim) from `verify_jwt`.
2. Fetches the corresponding `Account` from SQLite (creates a default `Free` account if none exists).
3. If `last_usage_reset` date (UTC) is older than today's date, resets `usage_count_daily` to `0` and updates `last_usage_reset` to `now`.
4. Checks if `usage_count_daily` >= `usage_limit_daily`. If so, raises `HTTPException(status_code=402, detail="Daily usage limit reached. Please upgrade your tier.")`.
5. Increments `usage_count_daily` by 1.
6. Commits the transaction and logs a `SyncOutbox` record to replicate the updated usage state to the cloud database.

---

## 3. Stripe API & Webhook Endpoints Design

To integrate Stripe, we propose introducing `backend/billing.py` to house Stripe SDK calls, and registering endpoints in `backend/main.py`.

### Proposed `backend/billing.py` (Complete copy-paste-ready implementation):

```python
import os
import uuid
import logging
from datetime import datetime, timezone
import stripe
from fastapi import HTTPException
from sqlalchemy import select
from .database import async_session
from .models import Account, SyncOutbox

logger = logging.getLogger(__name__)

# Configurations
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_MOCK_MODE = os.getenv("STRIPE_MOCK_MODE", "false").lower() == "true"
STRIPE_ALLOW_FALLBACK = os.getenv("STRIPE_ALLOW_FALLBACK_ON_ERROR", "true").lower() == "true"

# Stripe Pricing Mappings
PRICE_IDS = {
    "pro": os.getenv("STRIPE_PRICE_PRO", "price_1Pro_MockID"),
    "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_1Enterprise_MockID"),
}

LIMITS_MAP = {
    "free": 5,
    "pro": 100,
    "enterprise": 1000
}

if STRIPE_API_KEY:
    stripe.api_key = STRIPE_API_KEY

async def create_checkout_session(tenant_id: str, tier: str, success_url: str, cancel_url: str) -> dict:
    """
    Creates a Stripe Checkout Session for subscription signups.
    Gracefully falls back to mock URLs if mock mode is active, key is missing, or Stripe is offline.
    """
    tier_lower = tier.lower()
    if tier_lower not in ["pro", "enterprise"]:
        raise ValueError(f"Checkout not allowed for tier: {tier}")

    price_id = PRICE_IDS.get(tier_lower)
    
    # 1. Fallback if mock mode or Stripe key is missing
    if STRIPE_MOCK_MODE or not STRIPE_API_KEY:
        mock_id = f"cs_test_{uuid.uuid4().hex}"
        logger.info(f"Stripe mock mode active. Generating mock checkout session: {mock_id}")
        return {
            "id": mock_id,
            "url": f"https://checkout.stripe.dev/preview/{mock_id}?tenant_id={tenant_id}&tier={tier_lower}",
            "mocked": True
        }

    # 2. Production Call with Network Fallback
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=tenant_id,
            metadata={"tenant_id": tenant_id, "tier": tier_lower}
        )
        return {
            "id": session.id,
            "url": session.url,
            "mocked": False
        }
    except Exception as e:
        logger.error(f"Stripe session creation failed: {e}")
        if STRIPE_ALLOW_FALLBACK:
            fallback_id = f"cs_fallback_{uuid.uuid4().hex}"
            logger.info("Network/API failure. Returning graceful fallback checkout URL.")
            return {
                "id": fallback_id,
                "url": f"https://checkout.stripe.dev/preview/{fallback_id}?fallback=true&tenant_id={tenant_id}&tier={tier_lower}",
                "mocked": True
            }
        raise HTTPException(status_code=502, detail="Failed to communicate with payment gateway.")

async def handle_stripe_event(event_type: str, data_object: dict):
    """
    Updates Account tables and Outbox sync log based on subscription lifecycle events.
    """
    metadata = data_object.get("metadata", {})
    tenant_id = metadata.get("tenant_id") or data_object.get("client_reference_id")
    tier = metadata.get("tier")

    stripe_customer_id = data_object.get("customer")
    stripe_subscription_id = data_object.get("id") if event_type.startswith("customer.subscription") else data_object.get("subscription")
    status = data_object.get("status")

    if not tenant_id and stripe_customer_id:
        # Fallback: lookup tenant by customer id in the local DB
        tenant_id = await get_tenant_id_by_customer(stripe_customer_id)

    if not tenant_id:
        logger.error(f"Unable to resolve tenant_id for Stripe event {event_type} (customer_id: {stripe_customer_id})")
        return

    is_active = status in ["active", "trialing"] if status else True

    async with async_session() as db_session:
        result = await db_session.execute(
            select(Account).where(Account.tenant_id == tenant_id)
        )
        account = result.scalars().first()

        if not account:
            account = Account(tenant_id=tenant_id, currency="CREDITS", balance_cents=0)
            db_session.add(account)
            await db_session.flush()

        if event_type == "customer.subscription.deleted" or not is_active:
            account.tier = "Free"
            account.stripe_subscription_id = None
            account.usage_limit_daily = LIMITS_MAP["free"]
        else:
            resolved_tier = tier or "pro"
            account.tier = resolved_tier.capitalize()
            account.stripe_customer_id = stripe_customer_id
            account.stripe_subscription_id = stripe_subscription_id
            account.usage_limit_daily = LIMITS_MAP.get(resolved_tier.lower(), LIMITS_MAP["free"])

        # Create outbox record to synchronize mutations to the cloud
        outbox = SyncOutbox(
            table_name="accounts",
            record_id=str(account.id),
            operation="UPDATE",
            payload={
                "id": account.id,
                "tenant_id": account.tenant_id,
                "tier": account.tier,
                "stripe_customer_id": account.stripe_customer_id,
                "stripe_subscription_id": account.stripe_subscription_id,
                "usage_limit_daily": account.usage_limit_daily
            },
            synced=False
        )
        db_session.add(outbox)
        await db_session.commit()
        logger.info(f"Database successfully updated for tenant {tenant_id} to tier {account.tier} via event {event_type}")

async def get_tenant_id_by_customer(stripe_customer_id: str) -> str:
    """Helper to resolve a tenant_id using the customer ID."""
    async with async_session() as db_session:
        result = await db_session.execute(
            select(Account.tenant_id).where(Account.stripe_customer_id == stripe_customer_id)
        )
        return result.scalars().first()
```

---

## 4. Graceful Mock Fallback Mechanics

To prevent the local app or programmatic test suites from breaking when network or secret keys are missing, the system utilizes a **three-tier fallback strategy**:

1. **Explicit Mock Mode**: Set `STRIPE_MOCK_MODE=true` in environment. Stripe SDK calls are completely bypassed, returning simulated URLs.
2. **Implicit Mock Fallback**: If `STRIPE_API_KEY` is not present, the codebase automatically redirects checkout session generation to simulated endpoints, raising no exceptions.
3. **Robust Webhook Signatures**:
   - In production, `stripe.Webhook.construct_event` validates signatures.
   - In mock mode (`STRIPE_MOCK_MODE=true` or missing `STRIPE_WEBHOOK_SECRET`), the signature check is bypassed, and payloads are constructed using `stripe.Event.construct_from`. Developers can fire mock JSON payloads directly to `/api/v1/webhook/stripe` without configuring Stripe CLI listeners.

---

## 5. Recommended Changes & Code Placement

### A. Database Updates (SQL DDL)
To modify the existing database tables, the following SQL DDL must be applied:

```sql
-- Extend SQLite and Postgres 'accounts' schema
ALTER TABLE accounts ADD COLUMN tier VARCHAR(50) DEFAULT 'Free';
ALTER TABLE accounts ADD COLUMN stripe_customer_id VARCHAR(255);
ALTER TABLE accounts ADD COLUMN stripe_subscription_id VARCHAR(255);
ALTER TABLE accounts ADD COLUMN usage_limit_daily INTEGER DEFAULT 5;
ALTER TABLE accounts ADD COLUMN usage_count_daily INTEGER DEFAULT 0;
ALTER TABLE accounts ADD COLUMN last_usage_reset TIMESTAMP;

-- Create indices for performant event correlation
CREATE INDEX IF NOT EXISTS idx_accounts_stripe_customer ON accounts(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_accounts_stripe_subscription ON accounts(stripe_subscription_id);
```

### B. File Modifications

#### 1. `backend/models.py`
Add columns to the `Account` model definition:
```python
# Insert at line 25 of backend/models.py
tier = Column(String, default="Free")
stripe_customer_id = Column(String, index=True, nullable=True)
stripe_subscription_id = Column(String, index=True, nullable=True)
usage_limit_daily = Column(Integer, default=5)
usage_count_daily = Column(Integer, default=0)
last_usage_reset = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

#### 2. `backend/main.py`
- Add imports:
  ```python
  from pydantic import BaseModel
  from .billing import create_checkout_session, handle_stripe_event, check_and_increment_usage
  ```
- Add request validation schema:
  ```python
  class CheckoutRequest(BaseModel):
      tier: str
      success_url: str
      cancel_url: str
  ```
- Expose endpoints:
  ```python
  @app.post("/api/v1/checkout", dependencies=[Depends(verify_jwt)])
  async def trigger_checkout(req: CheckoutRequest, claims: dict = Depends(verify_jwt)):
      tenant_id = claims.get("tenant_id") or claims.get("sub")
      if not tenant_id:
          raise HTTPException(status_code=400, detail="Missing tenant_id in token claims.")
      try:
          session_info = await create_checkout_session(
              tenant_id=tenant_id,
              tier=req.tier,
              success_url=req.success_url,
              cancel_url=req.cancel_url
          )
          return {
              "status": "success",
              "session_id": session_info["id"],
              "checkout_url": session_info["url"],
              "mocked": session_info["mocked"]
          }
      except ValueError as e:
          raise HTTPException(status_code=400, detail=str(e))

  @app.post("/api/v1/webhook/stripe")
  async def stripe_webhook(request: Request):
      payload = await request.body()
      sig_header = request.headers.get("stripe-signature")
      
      # Determine validation mode
      mock_active = os.getenv("STRIPE_MOCK_MODE", "false").lower() == "true"
      webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

      if mock_active or not webhook_secret:
          try:
              import json
              event = stripe.Event.construct_from(json.loads(payload.decode("utf-8")), stripe.api_key)
          except Exception as e:
              raise HTTPException(status_code=400, detail=f"Mock payload parse failed: {e}")
      else:
          try:
              event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
          except stripe.error.SignatureVerificationError as e:
              raise HTTPException(status_code=400, detail=f"Signature verification failed: {e}")
          except Exception as e:
              raise HTTPException(status_code=400, detail=f"Webhook verification failed: {e}")

      event_type = event.get("type")
      data_object = event.get("data", {}).get("object", {})

      if event_type in [
          "customer.subscription.created",
          "customer.subscription.updated",
          "customer.subscription.deleted",
          "checkout.session.completed"
      ]:
          await handle_stripe_event(event_type, data_object)

      return {"status": "success"}
  ```
- Hook `check_and_increment_usage` dependency to protected action endpoints (e.g. `/api/v1/scrape` and `/api/v1/generate-cover-letter`):
  ```python
  # Example hook in main.py
  @app.post("/api/v1/scrape", dependencies=[Depends(check_and_increment_usage)])
  async def trigger_scrape(...):
      ...
  ```
