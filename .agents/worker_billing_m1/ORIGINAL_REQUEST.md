## 2026-07-03T13:19:02Z
Your role: teamwork_preview_worker
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_billing_m1

Your mission is to implement Stripe API billing and subscription integration in the FastAPI backend.

Specifically, perform these tasks:
1. Read the strategy and proposed code files in the explorer directories:
   - Analysis: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_billing_m1_1\analysis.md
   - Proposed code: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_billing_m1_1\proposed_billing.py
2. Edit `backend/models.py` to add `Subscription` and `Usage` models. Ensure the datetime defaults use timezone-aware datetime (UTC) as done in other models.
3. Create `backend/billing.py` with the complete router implementation, subscription tiers definitions, mock checkout redirect endpoint, Stripe webhook callback endpoint, and local SQLite DB persistence/outbox logic.
4. Edit `backend/main.py` to include `billing_router` and wrap `/api/v1/scrape`, `/api/v1/generate-cover-letter`, and `/api/v1/ai/generate-cover-letter/stream` with check_and_increment_usage limit checking (raise HTTP 402 if exceeded).
5. Write `tests/test_billing.py` to verify the checkout endpoint, the mock redirect upgrading logic, the webhook event lifecycle, and the limit checking enforcement.
6. Run the test suite:
   pytest tests/test_billing.py
   Ensure the tests pass successfully and report build/test commands and results in your handoff report.

DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
