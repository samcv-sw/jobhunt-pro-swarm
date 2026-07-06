## 2026-07-06T06:38:59Z
You are the Security Hardening Worker (worker_security_v5_gen3) for JobHunt Pro.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_security_v5_gen3

Objective:
Audit the codebase and ensure that the following security requirements from SCOPE.md are fully implemented and robustly verified:
1. WebSocket auth: Protect the WebSocket route `/ws/war-room` in `backend/main.py` by requiring verification of a JWT Bearer token (passed either as a query parameter `?token=...` or in custom WebSocket subprotocols/headers). Reject connections if missing or invalid.
2. Protect all unauthenticated `/api/v1/*` endpoints in the monolith `web/app_v2.py` (daily login rewards `/api/v1/daily-login` and `/api/v1/login-streak`, ATS scoring `/api/v1/ats-score` and `/api/v1/ats-score-bulk`, CV roast `/api/v1/roast`, and collector feed `/api/nodriver-feed`) using token verification.
3. Fix the `NameError` in `/api/v1/roast` (define/pass `mock_score` or replace with correct variable name).
4. SSRF Redirect Bypass: Fix the redirect bypass in `/api/v1/fetch-url` in `web/app_v2.py`. Disable `follow_redirects` in the HTTPX client (`follow_redirects=False`) or implement custom redirect handling that re-validates the hostname/IP blocklist for every redirection hop.
5. FastAPI Rate Limiting: Configure a rate-limiting middleware or dependency in `backend/main.py` to protect FastAPI routes (`/api/v1/scrape`, `/api/v1/generate-cover-letter`, `/api/v1/ai/generate-cover-letter/stream`) from volumetric abuse.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Scope boundaries:
- Limit your changes to the files `backend/main.py` and `web/app_v2.py`.
- Do not introduce unrelated modifications.
- Conform to logical CSS properties, Arabic typography, and other general rules if making any UI/UX changes (though this task is backend-heavy).

Inputs:
- Existing codebase in `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`.
- Security tests in `tests/test_security_hardening.py`, `tests/test_backend_secured.py`, `tests/e2e/test_unauthorized.py`.

Outputs:
- Perform the audit, make fixes if any are missing or incorrect, and run pytest to verify correctness.
- Write a detailed `handoff.md` file inside your working directory (`c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_security_v5_gen3\handoff.md`) showing:
  - Observation: current status of each requirement.
  - Logic Chain: what changes were confirmed or applied.
  - Verification: command run (pytest) and test results showing all tests pass.
- Send a message to your parent when completed.
