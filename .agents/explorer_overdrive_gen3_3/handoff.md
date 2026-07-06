# Handoff Report — Explorer 3 (Scraper & Security Auditor)

## 1. Observation

### A. Scraper Spoofing & Structured Output (`scrapers/stealth_ingest.py`)
1. **TLS Fingerprinting & Profiles**: `STEALTH_PROFILES` defines headers aligned with browser profiles:
   ```python
   STEALTH_PROFILES = [
       {
           "id": "chrome131",
           "impersonate": "chrome120",
           "headers": {
               "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
               "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,...",
               ...
           }
       },
       ...
   ]
   ```
   If `curl_cffi` is installed, it initializes a session using browser impersonation:
   ```python
   async with requests.AsyncSession(
       impersonate=profile["impersonate"],
       proxies=proxy_config,
       headers=headers,
       cookies=cookies,
   ) as session:
   ```
2. **Anti-Bot Bypass & Progressive Fallbacks**:
   - **Check screen challenge**: Checks if response contains challenge pages:
     ```python
     if any(k in response_text.lower() for k in ["just a moment", "attention required", "turnstile", "ddg-captcha"]):
     ```
   - **Browser Fallback 1**: `NodriverFallback.get_page_content(url)` (using headless Chromium).
   - **Browser Fallback 2**: `ApexCamoufoxFallback.get_page_content(url, proxy=proxy_str)` (using C++ Firefox-mod engine-level stealth).
   - **Parser Fallback**: Generative LLM parser `_parse_html_with_llm` uses `AITailor` if traditional BeautifulSoup selectors yield `"Unknown Position"`.
3. **Guaranteed Structured Output**:
   - `process_single_job` standardizes parsed data keys:
     ```python
     cleaned_jobs = []
     for job in jobs:
         if isinstance(job, dict):
             cleaned_job = {
                 "title": job.get("title") or "Unknown Position",
                 "url": job.get("url") or url,
                 "company": job.get("company"),
                 "description_snippet": job.get("description_snippet", "")
             }
             cleaned_jobs.append(cleaned_job)
     return cleaned_jobs
     ```
   - `stealth_scrape_jobs` merges gathered lists of dicts into a single `list[dict]` using a flat-map pattern (lines 520-532).
4. **⚠️ Stealth / Security Gap**: `NodriverFallback.get_page_content(url)` does not accept proxy configurations:
   ```python
   class NodriverFallback:
       @staticmethod
       async def get_page_content(url: str, timeout_seconds: int = 20) -> str:
           # ...
           browser = await uc.start(headless=True)
           page = await browser.get(url)
           # ...
   ```
   If `curl_cffi` fails (which it does when proxy settings are broken or blocked), the script falls back to `NodriverFallback` and executes the request directly from the host IP without proxying, leaking the server's identity.

---

### B. Backend Endpoint Protection & Auth Checks

#### 1. Python API Backend (`backend/main.py` & `backend/billing.py`)
- `/api/v1/scrape`, `/api/v1/generate-cover-letter`, `/api/v1/ai/generate-cover-letter/stream`, `/api/v1/accounts`, and `/api/v1/checkout` are protected via FastAPI dependency: `dependencies=[Depends(verify_jwt)]`.
- `verify_jwt` (in `backend/auth.py`, lines 30-55) checks `Authorization: Bearer <token>` and raises HTTP 401 when:
  - Header is missing: `raise HTTPException(status_code=401, detail="Authorization header missing or invalid scheme")`
  - Token is expired: `raise HTTPException(status_code=401, detail="Token has expired")`
  - Token is invalid: `raise HTTPException(status_code=401, detail="Invalid token")`
- **⚠️ Protection Gap (WebSocket)**: The WebSocket war-room route in `backend/main.py` is NOT protected by JWT or any auth mechanism:
  ```python
  @app.websocket("/ws/war-room")
  async def websocket_war_room(websocket: WebSocket):
      await manager.connect(websocket)
      ...
  ```

#### 2. Monolith Backend (`web/app_v2.py`)
We observed several `/api/v1/*` endpoints that completely bypass token verification:
- `/api/v1/daily-login` & `/api/v1/login-streak` (lines 5509-5520) accept user ID as a query parameter and do not perform authentication:
  ```python
  @app.get("/api/v1/daily-login")
  def api_daily_login(user_id: str = ""):
      # No auth check!
  ```
- `/api/v1/ats-score` & `/api/v1/ats-score-bulk` (lines 9546-9595) are public endpoints that accept input data and run LLM operations without session or cookie verification.
- `/api/v1/roast` (lines 10359-10376) is public and contains a **critical bug**:
  ```python
  @app.post("/api/v1/roast")
  async def api_roast_cv(file: UploadFile = File(...)):
      # ...
      score = random.randint(12, 45)
      return {"status": "ok", "roast": roast_text, "score": mock_score}
  ```
  `mock_score` is undefined, raising a `NameError` crash upon call.
- `/api/nodriver-feed` (lines 10378-10420) accepts unauthenticated JSON payloads and inserts jobs directly into the database.

#### 3. Cloudflare Worker Webhook (`olympus_webhook/src/index.js`)
- `/api/v1/checkout` (POST, line 29) accepts raw POST payloads and generates crypto invoices via NOWPayments without JWT validation. It defaults to `"anon"` user:
  ```javascript
  if (url.pathname === "/api/v1/checkout" && request.method === "POST") {
      const body = await readBody(request);
      const userId = body.userId || "anon";
  ```

---

### C. Rate Limiting, Input Validation & CSRF

#### 1. Rate Limiting Configurations
- `web/app_v2.py` implements:
  - IP-based rate limiting via `edge_cache_rate_limit` (line 528) capped at 100 requests/minute.
  - Endpoint-specific limits (e.g. `/contact` and `/register`) backed by the `system_config` database table (line 3023).
- **⚠️ Protection Gap**: `backend/main.py` has **no rate-limiting middleware** configured. FastAPI endpoints (`/api/v1/scrape`, `/api/v1/generate-cover-letter`, `/api/v1/ai/generate-cover-letter/stream`) can be spammed continuously if a valid JWT is acquired.

#### 2. Input Validation Gaps
- `backend/main.py`: `ScrapeRequest` accepts a list of strings (`target_urls`) with no URI validation, enabling SSRF (e.g. targeting `http://localhost:8000/api/v1/accounts`).
- `web/app_v2.py`: `/api/v1/fetch-url` parses and validates URLs against internal IP ranges (`localhost`, `127.0.0.1`, `169.254.169.254`), but HTTPX is configured to follow redirects (`follow_redirects=True`). An attacker can input a URL like `http://attacker.com/redirect` which redirects to `http://localhost:8000/api/v1/accounts`, bypassing the hostname filter.

#### 3. CSRF Validation
- `web/app_v2.py` implements `csrf_middleware` (line 829), but it only validates `Origin`/`Referer` headers, which can be spoofed or stripped. Furthermore, all `/api/` paths are exempted:
  ```python
  if path.startswith("/api/"):
      return await call_next(request)
  ```

---

### D. Test Suite Audit

1. **Exact Test Command**:
   ```powershell
   python -m pytest tests/
   ```
2. **Current Test Status**: We ran the full test suite and verified that all tests pass:
   ```
   collected 218 items
   tests\e2e\test_database.py ....                                          [  1%]
   ...
   ====================== 218 passed, 3 warnings in 59.77s =======================
   ```
3. **⚠️ Missing Test Coverage**:
   The following endpoints have NO test coverage in the `tests/` directory:
   - `/api/v1/checkout` (Stripe billing session)
   - `/ws/war-room` (WebSocket in main)
   - `/api/v1/ats-score` & `/api/v1/ats-score-bulk` (AI score endpoints)
   - `/api/v1/roast` (NameError-crashing endpoint)
   - `/api/v1/daily-login` & `/api/v1/login-streak` (Auth bypass rewards)
   - `/api/nodriver-feed` (Unauthenticated collector feed)

---

## 2. Logic Chain

1. **Host IP Leak via Nodriver**:
   - `scrapers/stealth_ingest.py` has a progressive fallback chain: curl_cffi -> Nodriver -> Camoufox -> LLM.
   - `NodriverFallback.get_page_content()` in `core/stealth.py` starts a browser instance using `uc.start(headless=True)` but does not specify proxy configurations.
   - If `curl_cffi` encounters proxy connectivity errors or is blocked, the fallback executes the scraping target directly.
   - **Conclusion**: The host's real IP is leaked to target servers, bypassing residential proxy configuration.

2. **WebSocket & Worker Auth Bypasses**:
   - `backend/main.py` applies JWT Bearer checks (`Depends(verify_jwt)`) individually to REST routes. However, `/ws/war-room` uses `@app.websocket` and does not apply any security dependency.
   - Similarly, the Cloudflare worker (`olympus_webhook/src/index.js`) processes POST checkout requests anonymously, defaulting user identification to `"anon"`.
   - **Conclusion**: Crucial system entry points are exposed to unauthenticated operations.

3. **Public API Resource Exhaustion**:
   - Multiple REST endpoints under `web/app_v2.py` (daily login rewards, ATS scoring, CV roasting) are public.
   - `/api/v1/ats-score` executes expensive AI tasks via Groq/OpenAI.
   - `/api/v1/roast` contains a bug where `mock_score` is returned but never defined (NameError).
   - **Conclusion**: Attackers can abuse public endpoints to exhaust LLM budgets, insert spam records, or cause NameError runtime crashes.

4. **SSRF Redirect Bypass**:
   - `/api/v1/fetch-url` uses a list of blacklisted hostnames (e.g. `localhost`, `127.0.0.1`, `169.254.169.254`) to prevent SSRF.
   - However, the HTTPX client is initiated with `follow_redirects=True`.
   - **Conclusion**: Attackers can bypass the blacklist by redirecting requests through an external domain to internal IP endpoints.

5. **Testing Blindspot**:
   - The test suite reports 100% pass status (218 tests).
   - However, grep checks show that several critical endpoints (/api/v1/checkout, /ws/war-room, /api/v1/roast, etc.) are completely missing from unit/E2E test files.
   - **Conclusion**: High test coverage claims are invalid since critical transaction routes are not tested.

---

## 3. Caveats

- We assumed that `web/app_v2.py` is the primary monolith serving web pages and user-facing APIs, while `backend/main.py` serves the Celery task orchestration layer.
- We did not perform live penetration tests on Stripe checkout callbacks or NOWPayments IPN verify signatures; we relied on code review of signature verification algorithms.

---

## 4. Conclusion

The stealth scraping mechanics and JWT Bearer guards are architected well but have high-severity bypasses and implementation gaps:
1. **Proxy Leak**: Nodriver executes headless browser instances without routing through proxies, exposing the server IP.
2. **WebSocket & API Auth Bypasses**: WebSocket connections and multiple public REST APIs (rewards, scoring, roasting, collector feeds) have no authentication.
3. **API Crash**: Calling `/api/v1/roast` raises an unhandled `NameError`.
4. **WAF & Rate Limiting Disconnection**: The Python agent backend lacks security headers, WAF filters, or request rate limits.
5. **SSRF Filter Bypass**: Redirect following in `/api/v1/fetch-url` allows internal endpoint scraping.
6. **Testing Gaps**: Key endpoints are completely untested in the main test suite.

---

## 5. Verification Method

To verify our observations independently:
1. **SSRF Redirect**: Deploy a public server that redirects `http://[your_ip]/redirect` to `http://localhost:8000/healthz`. Call the `/api/v1/fetch-url` endpoint passing this URL and verify if it returns the health JSON.
2. **NameError Roast Bug**: Send a POST request with any small file to `/api/v1/roast` and observe if the server crashes with `500 Internal Server Error` and logs `NameError: name 'mock_score' is not defined`.
3. **Nodriver Proxy Leak**: Disable `curl_cffi` (by renaming the package import) and scrape `https://httpbin.org/ip`. Observe if the returned IP is the host IP rather than the proxy IP.
4. **Run Test Suite**:
   ```powershell
   python -m pytest tests/
   ```
   Verify that all 218 tests pass successfully, but note the lack of files referencing `/api/v1/checkout` or `/api/v1/roast`.
