# Stripe Integration Strategy & Analysis Report

## Executive Summary
This report outlines the proposed integration strategy for introducing Stripe billing and subscription lifecycle management into the local-first architecture of the JobHunt Pro application. The design introduces two new models (`Subscription` and `Usage`), implements an API router in `backend/billing.py` (including a zero-network mock environment), updates `backend/main.py` to enforce limits, and integrates with the local-first outbox synchronization pattern (`SyncOutbox`) to propagate state changes to the remote Neon PostgreSQL database.

---

## 1. Current FastAPI & Database Structure Analysis
The backend of JobHunt Pro is built on FastAPI and follows a local-first architecture:
* **Local SQLite DB with Outbox Sync**: Read/write operations occur with zero latency on a local SQLite database (`jobhunt_local.db` / WAL mode). Mutations are logged to the `SyncOutbox` (`ps_crud_outbox` table) and synchronised to the Neon PostgreSQL database via a background worker (`backend/sync_worker.py`).
* **Authentication**: Managed via JWT verification (`verify_jwt` in `backend/auth.py`), yielding a token payload containing a unique user/tenant identifier (`user_id` or `tenant_id`).
* **Existing Models**: `models.py` uses SQLAlchemy declarative models (`Account`, `Transaction`, `LedgerEntry`, and `SyncOutbox`). The billing system uses ledger-based credits, but lacks subscription tier management.

---

## 2. Subscription Tiers & Resource Limits
We define three subscription tiers: **Free**, **Pro**, and **Enterprise**. The limits cover active scraped URLs and generated cover letters (both standard and streaming):

| Subscription Tier | Monthly Price (USD) | Scrape URL Limit / Month | Cover Letter Limit / Month | Stripe Price ID (Example) |
|---|---|---|---|---|
| **Free** | $0.00 | 10 | 5 | None |
| **Pro** | $19.00 | 200 | 100 | `price_1ProMockPriceID` |
| **Enterprise** | $99.00 | Unlimited (999,999) | Unlimited (999,999) | `price_1EntMockPriceID` |

### Limit Storage & Verification Design
1. **`Subscription` Model**: Stores the active subscription metadata (current tier, status, Stripe subscription ID, customer ID, and current period start/end timestamps).
2. **`Usage` Model**: Stores feature consumption logs grouped by billing cycle start date.
3. **Usage Check Middleware/Helper**: Before any scraping or AI generation task runs, the system queries the user's active tier, checks current usage in the billing period, increments it if allowed, logs a `SyncOutbox` entry, and commits. If the limit is exceeded, it raises `HTTPException(402, detail="Payment Required: Usage limit exceeded.")`.

---

## 3. Stripe Checkout & Webhook Lifecycle Design

### `/api/v1/checkout`
* **Purpose**: Generates a Stripe Checkout Session URL or a mock simulation URL.
* **Authentication**: Requires a verified JWT Bearer token.
* **Metadata**: Passes `tenant_id` and `tier` in the Stripe Session `metadata` to preserve user association during async webhook callbacks.
* **Customer Reuse**: Reuses existing `stripe_customer_id` from the `Subscription` table if available; otherwise, creates a new Stripe Customer.

### `/api/v1/webhook/stripe`
* **Purpose**: Processes events from Stripe.
* **Security**: Validates the payload signature using the `stripe-signature` header and `STRIPE_WEBHOOK_SECRET`.
* **Events Handled**:
  * `checkout.session.completed`: Provisions the subscription, updates the local DB, and writes an outbox log.
  * `customer.subscription.updated`: Syncs active/past_due statuses, updates current period end, and logs an outbox mutation.
  * `customer.subscription.deleted`: Drops the tier to "Free" (status "canceled") and logs an outbox mutation.

---

## 4. Graceful Fallback & Offline Mock Strategy
To facilitate developer testing and support zero-network local operations:
* **Mock Detection**: If `STRIPE_MOCK=true` or `STRIPE_API_KEY` is empty, mock mode is activated.
* **Mock Checkout Redirect**:
  1. The `/checkout` endpoint returns a mock checkout session ID and a local redirection URL:
     `http://localhost:8000/api/v1/billing/mock-checkout-redirect?tenant_id={tenant_id}&tier={tier}&success_url={success_url}`
  2. Clicking this URL calls a GET endpoint `/api/v1/billing/mock-checkout-redirect` which simulates the webhook by directly invoking the local subscription activation logic.
  3. It then redirects the user to their original `success_url`.
* This mechanism ensures checkout testing requires zero internet connection, mock webhooks, or configuration keys.

---

## 5. Recommended Implementation Code Changes

### A. Database Migrations (PostgreSQL & SQLite)
Add the `subscriptions` and `usages` tables.

#### SQL Migration Script:
```sql
-- 1. Create subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    tier VARCHAR(50) DEFAULT 'Free',
    status VARCHAR(50) DEFAULT 'active',
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tenant ON subscriptions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_sub ON subscriptions(stripe_subscription_id);

-- 2. Create usages table
CREATE TABLE IF NOT EXISTS usages (
    id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    feature VARCHAR(50) NOT NULL,
    count INTEGER DEFAULT 0,
    billing_period_start TIMESTAMP NOT NULL,
    billing_period_end TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, feature, billing_period_start)
);
CREATE INDEX IF NOT EXISTS idx_usages_tenant_feature ON usages(tenant_id, feature);
```

### B. SQLAlchemy Models (`backend/models.py`)
Append these models at the end of the file:
```python
# --- NEW: Subscription & Usage Models for Billing Integration ---

class Subscription(Base):
    """
    SaaS subscription details per tenant, synced to remote cloud PG.
    """
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False, unique=True)
    stripe_customer_id = Column(String, nullable=True, index=True)
    stripe_subscription_id = Column(String, nullable=True, index=True)
    tier = Column(String, default="Free")  # Free, Pro, Enterprise
    status = Column(String, default="active")  # active, trialing, past_due, canceled
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Usage(Base):
    """
    Tracks resource utilization (scraping, AI letter generation) per tenant per billing period.
    """
    __tablename__ = "usages"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, index=True, nullable=False)
    feature = Column(String, nullable=False)  # "scraping", "cover_letter"
    count = Column(Integer, default=0)
    billing_period_start = Column(DateTime, nullable=False)
    billing_period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
```

### C. FastAPI Application Integration (`backend/main.py`)
Add imports, include the router, and inject limits checking in endpoints.

```python
# 1. New imports to add at the top of backend/main.py
from .database import get_db
from .billing import router as billing_router
from .billing import check_and_increment_usage

# 2. Register the router in backend/main.py
app.include_router(billing_router)

# 3. Update /api/v1/scrape in backend/main.py
@app.post("/api/v1/scrape", dependencies=[Depends(verify_jwt)])
async def trigger_scrape(
    req: ScrapeRequest,
    jwt_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    Instantly returns 200 OK and sends the scraping task to Celery.
    Checks and increments subscription limits before queueing.
    """
    tenant_id = jwt_payload.get("user_id") or jwt_payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token: tenant_id missing")
        
    allowed = await check_and_increment_usage(db, tenant_id, "scraping", len(req.target_urls))
    if not allowed:
        raise HTTPException(
            status_code=402,
            detail="Payment Required: Scraping URL limit exceeded for this billing cycle."
        )
        
    task = await asyncio.to_thread(scrape_jobs.delay, req.target_urls, req.user_id)
    return {"status": "queued", "task_id": task.id}

# 4. Update /api/v1/generate-cover-letter in backend/main.py
@app.post("/api/v1/generate-cover-letter", dependencies=[Depends(verify_jwt)])
async def trigger_cover_letter(
    req: CoverLetterRequest,
    jwt_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    Triggers cover letter generation, validating usage limits first.
    """
    tenant_id = jwt_payload.get("user_id") or jwt_payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token: tenant_id missing")
        
    allowed = await check_and_increment_usage(db, tenant_id, "cover_letter")
    if not allowed:
        raise HTTPException(
            status_code=402,
            detail="Payment Required: Cover letter generation limit exceeded for this billing cycle."
        )
        
    task = await asyncio.to_thread(generate_cover_letter.delay, req.job_description, req.user_cv)
    return {"status": "queued", "task_id": task.id}

# 5. Update /api/v1/ai/generate-cover-letter/stream in backend/main.py
@app.post("/api/v1/ai/generate-cover-letter/stream", dependencies=[Depends(verify_jwt)])
async def stream_cover_letter(
    req: CoverLetterRequest,
    jwt_payload: dict = Depends(verify_jwt),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    Streams cover letter generation, validating usage limits first.
    """
    tenant_id = jwt_payload.get("user_id") or jwt_payload.get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token: tenant_id missing")
        
    allowed = await check_and_increment_usage(db, tenant_id, "cover_letter")
    if not allowed:
        raise HTTPException(
            status_code=402,
            detail="Payment Required: Cover letter generation limit exceeded for this billing cycle."
        )
        
    return StreamingResponse(
        generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
        media_type="text/event-stream"
    )
```

---

## 6. Verification & Test Plan

1. **Verify Database Models**:
   Run schema updates on SQLite and assert the tables `subscriptions` and `usages` are successfully created.
2. **Verify Mock Checkout flow**:
   * Request checkout for "Pro" using a HTTP request:
     `POST /api/v1/checkout` with payload `{"tier": "Pro", "success_url": "http://localhost:3000/success", "cancel_url": "http://localhost:3000/cancel"}`.
   * Verify that the endpoint returns `mocked=True` and redirects to the simulation URL.
   * Call the redirect URL and verify it forwards to `http://localhost:3000/success` and that a subscription row is successfully written to the local database, including a corresponding `SyncOutbox` record.
3. **Verify Limit Enforcement**:
   * Put user in "Free" tier (default).
   * Invoke `POST /api/v1/scrape` repeatedly until the 10 limit is hit.
   * Assert the 11th request returns a `402 Payment Required` HTTP response.
4. **Verify Webhook Construction**:
   * Issue a post request with valid signature headers matching `STRIPE_WEBHOOK_SECRET` to `/api/v1/webhook/stripe`.
   * Assert that Stripe webhook responses match the expectations and update DB states correctly.
