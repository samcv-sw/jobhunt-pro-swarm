# Handoff Report

## 1. Observation
* **Database Sync Pattern**: `backend/database.py` utilizes SQLite locally (`jobhunt_local.db`) and PostgreSQL remotely (`NEON_DATABASE_URL`).
  ```python
  LOCAL_DB_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./jobhunt_local.db")
  REMOTE_PG_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/jobhunt_pro")
  ```
  `backend/sync_worker.py` queries unsynced records from the `SyncOutbox` table and pushes them to PostgreSQL:
  ```python
  result = await session.execute(
      select(SyncOutbox)
      .where(SyncOutbox.synced == False)
      .limit(100)
  )
  ```
* **Authentication Structure**: `backend/auth.py` defines a JWT Bearer security scheme:
  ```python
  async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
  ```
  Returning a decoded dictionary payload containing user identity claims (`user_id`, `email`, etc.).
* **API Endpoints**: `backend/main.py` processes routes like `/api/v1/scrape` and `/api/v1/generate-cover-letter`, which queue Celery background tasks:
  ```python
  task = await asyncio.to_thread(scrape_jobs.delay, req.target_urls, req.user_id)
  ```
  They lack tier checking or usage limit validation before queuing.

---

## 2. Logic Chain
1. **Local-First Consistency**: Since the backend writes locally to SQLite and syncs asynchronously to remote Neon PostgreSQL via the outbox pattern (Observation 1), any updates to subscription tier levels or usage quotas must be written to local SQLite and registered in the `SyncOutbox` (`ps_crud_outbox` table) inside the same database transaction.
2. **Auth Integration**: The Bearer token validation provides `tenant_id` (`user_id`) and `email` properties (Observation 2). These can be used to resolve the subscription status for incoming requests.
3. **Usage Enforcing**: By checking the user's active tier limits and current usage count in `backend/main.py` before delegating to Celery (Observation 3), we prevent unauthorized resource execution and return a clean `402 Payment Required` response when limits are exceeded.
4. **Mock Redirection Loop**: By checking for `STRIPE_MOCK=true` or missing API keys, we can safely bypass the Stripe API during local development. By returning a local GET endpoint (`/api/v1/billing/mock-checkout-redirect`) that directly updates the user's database records and redirects to `success_url`, we replicate the payment completion callback fully without using internet connections.

---

## 3. Caveats
* **Network Isolation**: Under `CODE_ONLY` network mode, we could not connect to external Stripe endpoints. The Stripe API logic was designed based on the official SDK specifications and validated through local mock logic.
* **Celery Task Quota Rollbacks**: If a Celery task fails after the limit is incremented in the HTTP endpoint, the limit count is not rolled back in this proposal. A failure recovery queue handler would be needed to restore usage credits if failed tasks are not retried.

---

## 4. Conclusion
Integrating Stripe billing requires creating the new `Subscription` and `Usage` tables in both local SQLite and remote Neon PostgreSQL databases. Enforcing limits can be implemented via helper functions inside `backend/billing.py` that check limits and log changes to the database and `SyncOutbox` table. Complete code models, endpoint implementations, and a mock checkout simulation have been generated in `proposed_billing.py` and documented in `analysis.md` in the working directory.

---

## 5. Verification Method
* **Inspect Proposed Files**:
  * Review the structured report in `analysis.md` in this directory.
  * Inspect the copy-paste-ready FastAPI router and handlers in `proposed_billing.py` in this directory.
* **Run Tests**:
  * Once implemented, the test suite can be run using the standard pytest command:
    `pytest tests/` (or running backend unit tests if available).
  * Assert that a mock checkout request to `POST /api/v1/checkout` returns `mocked=True` and redirects to the simulation endpoint, which successfully activates the user's subscription and logs the outbox update.
