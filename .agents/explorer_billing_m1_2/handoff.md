# Handoff Report — Stripe Billing Integration Strategy

## 1. Observation
We explored the codebase and observed the following:

- **Local Schema Setup**: `backend/models.py` (lines 17-25) defines the `Account` model representing the billing entity per tenant:
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
- **Outbox Synchronization**: `backend/models.py` (lines 48-61) and `backend/sync_worker.py` (lines 11-29) establish an asynchronous synchronization pipeline from SQLite `SyncOutbox` to Neon Postgres using generic JSON payloads:
  ```python
  INSERT INTO sync_outbox_log (table_name, record_id, operation, payload, created_at)
  VALUES ($1, $2, $3, $4::jsonb, $5)
  ```
- **FastAPI Core Routing**: `backend/main.py` contains endpoints authenticated with `verify_jwt` dependency (e.g. `/api/v1/scrape` and `/api/v1/generate-cover-letter`).
- **Pricing Management**: `core/pricing_manager.py` contains pre-existing arrays of static pricing configurations (`PRICING_TIERS`, `SERVICE_PACKAGES`).
- **Web Payment Layer**: `web/routers/payments.py` handles Web UI order processing and has a basic Stripe Webhook listener for order fulfillment.

---

## 2. Logic Chain
Based on our observations, we derived the following implementation path:
- **Zero-Latency Usage Enforcement**: Since the core scraping and AI cover letter endpoints (`/api/v1/scrape` and `/api/v1/generate-cover-letter`) need to run at zero latency (observing `backend/main.py`), usage limit checks must happen against the local SQLite database.
- **Local Database Extension**: To store the active subscription tier and track daily usage limits, we must add `tier`, `stripe_customer_id`, `stripe_subscription_id`, `usage_limit_daily`, `usage_count_daily`, and `last_usage_reset` to the local `Account` table (defined in `backend/models.py`).
- **Outbox Replication**: When an account tier is modified (e.g., via Stripe webhook) or usage is incremented, the local-first node updates SQLite and appends a `SyncOutbox` entry. The `sync_worker.py` streams these updates to the cloud Postgres automatically, maintaining schema synchronization.
- **Robust Mock Fallback**: In offline development or programmatic testing, if `STRIPE_MOCK_MODE=true` or `STRIPE_API_KEY` is not present, the checkout session creator should intercept API calls and return a simulated checkout URL (`https://checkout.stripe.dev/preview/cs_test_...`), while the webhook parser bypasses signature verification and validates the payload directly using `stripe.Event.construct_from`.

---

## 3. Caveats
- **Replication Direction**: We assumed cloud-to-local replication is handled by a secondary sync stream (out of scope for this task). If a webhook hits the central server directly, local nodes will fetch the updated account tiers during their next sync cycle or read from PostgreSQL.
- **JWT Format**: We assumed token claims contain either `tenant_id` or `sub` to map users to their ledger account.

---

## 4. Conclusion
Integrating Stripe Billing in `backend/billing.py` aligns perfectly with the local-first dual-database architecture. By modifying the `Account` model and writing a localized FastAPI dependency, the system can perform zero-latency limit checks locally on SQLite, replicate modifications asynchronously via `SyncOutbox`, and support developer productivity through a robust offline mock fallback mechanism.

---

## 5. Verification Method
1. **Model Check**: Inspect SQLite schema changes after model updates:
   ```powershell
   # Open SQLite shell on database
   sqlite3 jobhunt_local.db "PRAGMA table_info(accounts);"
   ```
2. **Programmatic Checkout Test**: Create `tests/test_billing.py` to hit the checkout endpoint and verify mock behavior:
   ```bash
   pytest tests/test_billing.py
   ```
3. **Manual Endpoint Verification**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/checkout \
     -H "Authorization: Bearer <JWT_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"tier": "pro", "success_url": "http://localhost:8000/success", "cancel_url": "http://localhost:8000/cancel"}'
   ```
   Ensure it returns a successful URL redirection containing a mock session.
