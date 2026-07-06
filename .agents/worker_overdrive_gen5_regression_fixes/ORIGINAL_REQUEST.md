## 2026-07-06T10:53:42Z
Role: Overdrive Swarm Regression Fixes Worker
Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_overdrive_gen5_regression_fixes
Task:
Please implement the following regression and test isolation fixes:

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

1. WebSocket Database Validation Fix:
   - In `tests/test_backend_secured.py::test_websocket_auth`, insert the test user `'authorized-user'` into the database before establishing the websocket connection:
     ```python
     import sqlite3
     conn = sqlite3.connect("./jobhunt_local.db")
     conn.execute("INSERT OR REPLACE INTO users (user_id, email, password_hash, is_active) VALUES ('authorized-user', 'auth@example.com', 'hash', 1)")
     conn.commit()
     conn.close()
     ```
     This fixes the regression where WebSocket auth database validation checks for active status but the user wasn't registered in the test database.

2. Scraper Proxy Fallback Test Fix:
   - In `get_stabilized_proxy` in `scrapers/stealth_ingest.py`:
     Check if testing mode is active before performing the dynamic proxyscrape fetch. Specifically, check if `os.environ.get("TESTING") == "true"` or `"pytest" in sys.modules`.
     If so, set `active_proxies = ["http://jobhunt-stub-proxy:8080"]` directly and bypass the dynamic fetch. This keeps tests isolated and prevents failures due to live proxy fetches.

3. Global Rate Limiter Reset Fixture:
   - Create a new file `tests/conftest.py` (if it does not exist) containing a global autouse fixture that resets the rate limiter state before every test case to prevent cross-test rate limit pollution:
     ```python
     import pytest
     from backend.main import rate_limiter

     @pytest.fixture(autouse=True)
     def reset_rate_limiter_global():
         rate_limiter.reset()
         yield
         rate_limiter.reset()
     ```

Verification:
- Compile frontend Next.js production build using `node .\node_modules\next\dist\bin\next build`.
- Run tests:
  `pytest tests/test_sync_reconnection_stress.py tests/test_sync_dlq_poison_pill_stress.py tests/test_stealth_parser_and_fallbacks.py tests/test_adversarial_security.py tests/test_backend_secured.py tests/e2e/test_r3_scraper.py`
- Run the full test suite `pytest tests/` to confirm that all tests pass cleanly.
Write a detailed handoff.md in your working directory summarizing the changes made and the build and test results.
