## 2026-07-06T07:37:53Z

Role: Overdrive Swarm Fixes Implementer
Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_overdrive_gen5_fixes
Task:
You are tasked with implementing the code fixes, optimizations, and security hardening measures identified during the database sync, security, scraper, and frontend audits.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please execute the following fixes step-by-step:

1. DB Sync Telemetry:
   - Edit `backend/sync_worker.py` and `backend/database.py` (if relevant) to log remote Neon PostgreSQL query latencies. Track query execution time using `time.perf_counter()` and log the latency for each remote push or query.

2. WebSocket Auth & Claims Check:
   - Edit `backend/main.py` in the WebSocket endpoint `/ws/war-room` (lines 170-176).
   - Ensure the token's signature is decoded using `jwt.decode`.
   - Inspect the decoded claims: check that a valid `"sub"` claim is present and not empty.
   - Perform a database query to verify that the user associated with the `"sub"` claim exists and is active in the SQLite database.
   - If validation fails or the claim is missing, close the WebSocket connection with code `4001`.
   - Update the test `test_websocket_auth_claim_bypass` in `tests/test_adversarial_security.py` so it expects the connection to be rejected (raise `WebSocketDisconnect` with code `4001` or assert that validation fails), since we are closing the security gap.

3. Remove Hardcoded Secret Fallback in app_v2.py:
   - Edit `web/app_v2.py`. Check lines 73-83 where `JWT_SECRET_KEY` is retrieved.
   - If `JWT_SECRET_KEY` is missing from `os.environ` in production (meaning `TESTING` is not true, and not running under pytest/unittest), raise a `ValueError("JWT_SECRET_KEY environment variable is not set")` instead of falling back to a hardcoded string.

4. Proxy-Aware API Rate Limiter:
   - Edit `RateLimiter` in `backend/main.py`.
   - Update client IP resolution to check for `X-Forwarded-For` or `X-Real-IP`. If present, parse and use the first IP address. Otherwise, use `request.client.host`.
   - Add a key pruning cleanup logic inside the rate limit check to periodically remove old keys from the `self.history` dictionary (keys older than `window_seconds`) to prevent memory leaks in long-running processes.
   - Apply the rate limiter dependency to the `/api/v1/accounts` (`create_account`) and `/api/v1/checkout` (`create_checkout_session`) endpoints.

5. Rate Limiting Database Key:
   - Edit `_check_rate_limit` in `web/shared.py`.
   - Replace `id(store)` in `db_key = f"rl:{id(store)}:{ip}"` with a stable static string (e.g. `"web_store"`) or remove it entirely, so that different worker processes (Uvicorn worker replicas) synchronize rate limits correctly.

6. Secure Auth Cookie:
   - Edit `web/routers/auth.py` and `web/app_v2.py`. Wherever `resp.set_cookie("user_id", ...)` is called, add `secure=True` to the attributes list.

7. Scraper Stealth Profile UA Mismatch Fix:
   - Edit `scrapers/stealth_ingest.py`. Update the User-Agent strings in the `STEALTH_PROFILES` array to exactly match their corresponding `impersonate` targets:
     - For `impersonate: "chrome120"`, use a Chrome 120 User-Agent.
     - For `impersonate: "firefox120"`, use a Firefox 120 User-Agent.
     - For `impersonate: "safari17_2_1"`, use a Safari 17.2.1 User-Agent.

8. Stealth Fallback Enhancements:
   - Install `camoufox` dependency using `uv pip install camoufox` or `pip install camoufox`, and run `python -m camoufox fetch`. Make sure `ApexCamoufoxFallback` is fully functional and not raising `ImportError`.
   - In `core/stealth.py`, update `NodriverFallback` to inject the WebGL, Canvas, and browser attribute stealth spoofing scripts before returning content, and execute human mouse simulation events.
   - In `scrapers/stealth_ingest.py`, if `RESIDENTIAL_PROXIES` is empty, generate or rotate proxies from a list of free public proxies (similar to `core/stealth.py`) instead of relying solely on the single stub proxy.

9. Next.js Frontend Fonts size check:
   - Edit `frontend/src/app/globals.css`. Add a CSS override rule to enforce a minimum 16px font size on sub-16px Tailwind classes when rendering in RTL (Arabic):
     ```css
     [dir="rtl"] .text-sm, [dir="rtl"] .text-xs, [dir="rtl"] .text-\[10px\] {
       font-size: 16px !important;
     }
     ```

Verification:
- Compile frontend Next.js production build using `node .\node_modules\next\dist\bin\next build` to verify it compiles.
- Run tests:
  `pytest tests/test_sync_reconnection_stress.py tests/test_sync_dlq_poison_pill_stress.py tests/test_stealth_parser_and_fallbacks.py tests/test_adversarial_security.py`
- Run the full test suite to ensure all tests pass.
Write a detailed handoff.md in your working directory summarizing the changes made and the build and test results.
