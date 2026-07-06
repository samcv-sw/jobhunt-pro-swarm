## 2026-07-05T19:01:24Z
You are Worker 1 (Security Worker) - Generation 2.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_security_v5_gen2

Your mission is to implement the API security, WebSocket verification, SSRF protection, and rate-limiting controls defined in the scope:
1. Protect the WebSocket route `/ws/war-room` in `backend/main.py` by requiring verification of a JWT Bearer token (passed either as a query parameter `?token=...` or in custom WebSocket subprotocols/headers). Reject connections if missing or invalid. Use JWT_SECRET_KEY and JWT_ALGORITHM to decode it.
2. Protect all unauthenticated `/api/v1/*` endpoints in the monolith `web/app_v2.py` (daily login rewards `/api/v1/daily-login` and `/api/v1/login-streak`, ATS scoring `/api/v1/ats-score` and `/api/v1/ats-score-bulk`, CV roast `/api/v1/roast`, and collector feed `/api/nodriver-feed`) using token verification. Since `jwt` is not imported or used in `web/app_v2.py`, you should import/use it and implement a secure token verification dependency/check.
3. Fix the `NameError` in `/api/v1/roast` (define/pass `mock_score` or replace with correct variable name).
4. Fix the SSRF Redirect Bypass in `/api/v1/fetch-url` in `web/app_v2.py`. Disable `follow_redirects` in the HTTPX client (`follow_redirects=False`) or implement custom redirect handling that manually re-validates the hostname/IP blocklist for every redirection hop.
5. Configure a rate-limiting middleware or dependency in `backend/main.py` to protect FastAPI routes (`/api/v1/scrape`, `/api/v1/generate-cover-letter`, `/api/v1/ai/generate-cover-letter/stream`) from volumetric abuse. Implement a custom, lightweight, in-memory rate limiter to avoid using external/uninstalled packages like `slowapi`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Verification:
- Run tests (e.g. `tests/test_backend_secured.py` and `tests/e2e/test_unauthorized.py`) to confirm that all security checks pass.
- Write a handoff.md in your working directory with details of your changes and test outcomes.
- Message me back with the absolute path to your handoff.md when complete.
