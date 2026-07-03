# Handoff Report - Stripe Billing Integration

## 1. Observation

- **Backend Routing Structure**: In `backend/main.py`, lines 49-67, the API routes `/api/v1/scrape`, `/api/v1/generate-cover-letter`, and `/api/v1/ai/generate-cover-letter/stream` protect their execution using the `verify_jwt` dependency without parsing the return value:
  ```python
  @app.post("/api/v1/scrape", dependencies=[Depends(verify_jwt)])
  ```
- **Database Models & Table Layout**: In `backend/models.py`, lines 17-26, the `Account` model stores local-first user details:
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
- **JWT Verification & Payload Extraction**: In `backend/auth.py`, lines 21-45, `verify_jwt` returns the full payload dictionary when decoded successfully:
  ```python
  async def verify_jwt(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
      ...
      payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
      return payload
  ```
- **Outbox Synchronization Pattern**: In `backend/sync_worker.py`, lines 11-33, local mutations are replicated to Neon Postgres by inserting into the outbox table `ps_crud_outbox` (represented by model `SyncOutbox`).
- **Dependencies List**: Ripgrep search for `stripe` in the root `requirements.txt` yielded `No results found`, implying Stripe is not yet defined in Python package requirements.

---

## 2. Logic Chain

- **Identifying User context**: Because `verify_jwt` returns a dictionary containing token claims, and since the `"sub"` claim represents the authenticated `tenant_id` (seen in testing setup inside `tests/e2e/test_e2e_backend.py` line 14), we can parse `token_payload: dict = Depends(verify_jwt)` inside the routes to extract the user's billing context without breaking JWT signatures or standard authentication flows.
- **Enforcing Subscriptions Local-First**: Since the platform relies on SQLite for zero-latency operations and synchronizes to cloud Neon Postgres asynchronously, adding subscription fields (`subscription_tier`, `subscription_status`, `scrapes_used`, `cover_letters_used`, `stripe_subscription_id`) directly to the `Account` table allows checking limits with SQLite read operations. To propagate these status updates to Neon, each update must insert a corresponding mutation record in the local `SyncOutbox` table.
- **Robust Dev Mock Fallback**: If Stripe keys are not configured or are set to `mock_`, we can switch to mock mode. In this mode, `/api/v1/checkout` yields a local redirection path `/api/v1/checkout/mock-success` containing state variables. Accessing this path immediately updates the tenant's record locally, simulating Stripe webhook delivery, and enabling developer integration testing without external dependencies. A dev-only `/api/v1/webhook/stripe/mock-trigger` POST endpoint is provided to fake other webhook lifecycles.

---

## 3. Caveats

- **External Stripe Sync Timing**: Because the sync worker (`sync_worker.py`) syncs SQLite changes to PostgreSQL every 5 seconds, changes to subscriptions will reflect locally instantly but may take up to 5 seconds to propagate to the cloud Postgres database.
- **Stripe Webhook Signature Verification**: In production, the Stripe Webhook signature must be verified using `STRIPE_WEBHOOK_SECRET`. This secret must be retrieved from Stripe CLI or Dashboard. Signature verification is bypassed ONLY when `STRIPE_MOCK_ENABLED` is `True`.

---

## 4. Conclusion

The Stripe billing integration strategy is fully detailed in `analysis.md` in the agent folder. It maps Stripe Checkout sessions and subscriptions directly to the `Account` model, defines tier limits, outlines how limit verification occurs dynamically, and supplies a robust, zero-network mock environment. Implementing the changes proposed in `analysis.md` will cleanly implement the Stripe billing lifecycle.

---

## 5. Verification Method

1. **Static Review**: Inspect `analysis.md` in the working directory to review the proposed changes for `backend/models.py`, `backend/main.py`, and the new `backend/billing.py`.
2. **Integration Verification**: 
   - Ensure `stripe` is added to `requirements.txt`.
   - Run the FastAPI backend application.
   - Set `STRIPE_MOCK_ENABLED=True` and run tests.
   - Run the project's E2E test suite to verify no existing auth/DB tests are broken:
     `pytest tests/e2e/test_e2e_backend.py`
