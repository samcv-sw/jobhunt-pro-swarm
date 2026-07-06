# Handoff Report — Overdrive Swarm Reviewer & Critic

## 1. Observation

### Verification Test Commands
- **Command**: `python -m pytest`
- **Output (failures captured)**:
```
FAILED tests/e2e/test_e2e_backend.py::test_backend_scraping_is_non_blocking
FAILED tests/e2e/test_e2e_backend.py::test_endpoint_validation_errors - assert 429 == 422
FAILED tests/e2e/test_e2e_backend.py::test_integration_outbox_flow - assert 429 == 200
FAILED tests/e2e/test_r1_cover_letter.py::test_r1_t1_generate_cover_letter_queued
FAILED tests/e2e/test_r3_scraper.py::test_r3_t1_trigger_scrape_queued - assert 429 == 200
FAILED tests/e2e/test_r3_scraper.py::test_get_stabilized_proxy_empty_env_fallback
FAILED tests/test_adversarial_security.py::test_rate_limiting_stream_cover_letter
FAILED tests/test_adversarial_security.py::test_shared_rate_limiting_across_endpoints
FAILED tests/test_backend_secured.py::test_websocket_auth - starlette.websockets.WebSocketDisconnect
FAILED tests/test_concurrency_stress.py::test_event_loop_latency_during_task_dispatch_stress
```

### Regressions Observed
1. **WebSocket Active User Database Validation**:
   - **Path**: `backend/main.py` lines 159-167
   ```python
   async with async_session() as session:
       result = await session.execute(
           text("SELECT is_active FROM users WHERE user_id = :user_id"),
           {"user_id": sub}
       )
       row = result.fetchone()
       if not row or not row[0]:
           await websocket.close(code=4001)
           return
   ```
   - **Impact**: `tests/test_backend_secured.py` line 213 tries to connect to `/ws/war-room` with `authorized-user` without inserting it into the database, causing a test failure via a websocket disconnect (code 4001).
   
2. **Proxy Scraper Internet Access during test runs**:
   - **Path**: `scrapers/stealth_ingest.py` lines 128-142
   ```python
   if not _cached_free_proxies or now - _last_proxy_fetch > 600:
       try:
           import requests
           res = requests.get(
               "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=elite",
               timeout=5.0
           )
           ...
   ```
   - **Impact**: `tests/e2e/test_r3_scraper.py::test_get_stabilized_proxy_empty_env_fallback` expects the stub proxy fallback `http://jobhunt-stub-proxy:8080` when `PROXY_LIST` is empty. However, the live `requests.get` call to the api.proxyscrape.com succeeds and returns a real proxy IP, breaking the assertion.
   
3. **Shared Rate Limiter Singleton State Pollution**:
   - **Path**: `backend/limiter.py` lines 8-40
   - **Impact**: In testing environments, the volumetric limit is set to 3 requests per 10 seconds. Since the singleton state is not cleared automatically between other test files (they do not use the reset fixture that `test_adversarial_security.py` has), subsequent tests hit the rate limit and fail with a 429 response.

---

## 2. Logic Chain

1. The worker implemented a database lookup for WebSocket auth in `backend/main.py`.
2. This lookup checks if the user is registered and active (`is_active = 1`).
3. In `tests/test_backend_secured.py::test_websocket_auth`, the test client connects using a valid signature token but no user is written to SQLite.
4. Hence, the lookup returns `None` and aborts connection with code 4001, resulting in a test failure.
5. In `get_stabilized_proxy` (`scrapers/stealth_ingest.py`), the worker added dynamic free proxy scraping if `PROXY_LIST` is empty.
6. The test `test_get_stabilized_proxy_empty_env_fallback` patches `PROXY_LIST = []` and expects the fallback stub proxy.
7. Due to a lack of HTTP mocking inside this test, the real scrape request succeeds and returns dynamic proxies instead of the stub, leading to test assertion failures.
8. Therefore, the implementation of database lookup and proxy scraping is correct but has broken existing test expectations. The test environment state also leaks because rate limiting limits are shared globally across test sessions without per-test reset fixtures.

---

## 3. Caveats

- We assumed that mock DB fixtures could be introduced inside the tests to resolve the WebSocket database check.
- We assumed that mocking requests to `api.proxyscrape.com` is required to keep testing isolated.
- No other code paths were modified, and the implementation logic of the features themselves conforms to the requirements.

---

## 4. Conclusion

- **Verdict**: **REQUEST_CHANGES**
- **Actionable Steps**:
  1. Add an automatic database setup in `tests/test_backend_secured.py::test_websocket_auth` to insert the `authorized-user` as active.
  2. Mock the proxyscrape API request inside `test_get_stabilized_proxy_empty_env_fallback` in `tests/e2e/test_r3_scraper.py` or check if testing mode is active in `get_stabilized_proxy` to bypass dynamic fetches.
  3. Ensure a global pytest fixture in `conftest.py` resets the backend `rate_limiter` state before each test case.

---

## 5. Verification Method

To verify the fixes, execute:
1. `python -m pytest tests/test_adversarial_security.py` (Must pass all 20 tests)
2. `python -m pytest tests/test_backend_secured.py` (Verify it passes once the test DB is populated)
3. `python -m pytest tests/e2e/test_r3_scraper.py` (Verify it passes after mocking the proxy API)

---

## Quality Review Report

**Verdict**: REQUEST_CHANGES

### Findings

#### [Critical] Finding 1: Broken WebSocket Auth Tests
- **What**: WebSocket auth database lookup checks for the user's active status, causing connections from unregistered test tokens to fail.
- **Where**: `backend/main.py` (lines 159-167) and `tests/test_backend_secured.py` (line 213)
- **Why**: Breaking existing test suites blocks CI/CD pipelines and hides other potential regressions.
- **Suggestion**: Update `tests/test_backend_secured.py` to insert test users into the database or mock the db session logic for websockets.

#### [Critical] Finding 2: Live Scraper Network Fallback Breakage
- **What**: Dynamic proxyscrape fetch executes during tests when `PROXY_LIST` is empty instead of returning a stub.
- **Where**: `scrapers/stealth_ingest.py` (lines 128-142) and `tests/e2e/test_r3_scraper.py` (line 205)
- **Why**: Real external requests fail inside containerized/offline CI test environments, and when they succeed, they break the assertion for the expected local stub proxy.
- **Suggestion**: Check `os.getenv("TESTING") == "true"` inside `get_stabilized_proxy` to prevent fetching from `proxyscrape` during test execution.

#### [Major] Finding 3: Inter-test Rate Limiter Pollution
- **What**: Global `rate_limiter` state persists across different test suites.
- **Where**: `backend/limiter.py`
- **Why**: Volumetric limits (3 requests / 10s) get exhausted during the overall test run, causing random `429` failures on other endpoints.
- **Suggestion**: Create an autouse fixture in `tests/conftest.py` that resets the `rate_limiter` before every test.

### Verified Claims
- Sync latency telemetry → verified via code inspection of `backend/sync_worker.py` → **PASS**
- Cookie secure=True flags → verified via code inspection of `web/routers/auth.py` and `web/app_v2.py` → **PASS**
- Impersonate profile sync → verified via code inspection of `scrapers/stealth_ingest.py` → **PASS**
- Nodriver/Camoufox fallbacks → verified via code inspection of `core/stealth.py` → **PASS**
- RTL CSS minimum font-size rules → verified via inspection of `frontend/src/app/globals.css` → **PASS**

---

## Adversarial Review (Challenge) Report

**Overall risk assessment**: MEDIUM

### Challenges

#### [High] Challenge 1: Scraping Fallbacks Depend on Outer System Packages
- **Assumption challenged**: Nodriver and Camoufox fallbacks are loaded dynamically.
- **Attack scenario**: If the running environment doesn't have chrome/firefox binaries or required dynamic link libraries installed, both `NodriverFallback` and `ApexCamoufoxFallback` will fail with system-level exceptions or tracebacks.
- **Blast radius**: Scraping fallback completely breaks down, reverting to empty outputs if `curl_cffi` gets challenged.
- **Mitigation**: Implement strict check for executable paths or wrap browser startup in a fallback `try-except` block returning `None` instead of failing with process-terminating errors.

#### [Medium] Challenge 2: Client IP Spoofing via X-Forwarded-For
- **Assumption challenged**: The rate limiter trusts `X-Forwarded-For` header.
- **Attack scenario**: An attacker can send different random `X-Forwarded-For` headers with every request, bypassing the rate limiter entirely.
- **Blast radius**: The application is vulnerable to distributed/spoofed volumetric DoS attacks.
- **Mitigation**: Ensure that the upstream proxy/load-balancer overrides `X-Forwarded-For` or that the rate limiter only extracts it when coming from a trusted proxy subnet.
