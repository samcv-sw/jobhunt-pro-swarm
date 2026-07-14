# Cloud Optimization Sweep Investigation Report

## 1. Observation
Below are the direct observations from the codebase analysis:

### 1.1 Single-Container Web+Worker Fusion
- **Celery Invocation**: `start_cloud.py` (lines 53-58) starts Celery with:
  ```python
  celery_cmd = ["celery", "-A", "backend.tasks", "worker", "--loglevel=info", "--concurrency=2"]
  ```
- **Celery Configuration**: `backend/celery_app.py` (lines 7-15) hardcodes broker configuration to RabbitMQ:
  ```python
  RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://jobhunt:jobhunt_password@localhost:5672//")
  REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0") # Keep Redis for result backend
  celery_app = Celery("jobhunt_tasks", broker=RABBITMQ_URL, backend=REDIS_URL, include=["backend.tasks"])
  ```
- **Database Pooling**: `backend/database.py` (lines 58-63) configures PostgreSQL pooling:
  ```python
  engine_kwargs.update({
      "pool_size":     20,    # baseline concurrent connections
      "max_overflow":  10,    # burst headroom
      "pool_recycle":  1800,  # recycle stale connections (seconds)
      "pool_timeout":  30,    # max wait for a free slot
      "pool_pre_ping": True,  # heartbeat before checkout
  })
  ```
- **SQLite Performance Tuning**: `backend/database.py` (lines 73-77) configures SQLite pragma settings:
  ```python
  cursor.execute("PRAGMA journal_mode=WAL")
  cursor.execute("PRAGMA synchronous=NORMAL")
  cursor.execute("PRAGMA cache_size=-64000")
  cursor.execute("PRAGMA temp_store=MEMORY")
  ```

### 1.2 Edge-Cached Semantic Engine & Failover Pool
- **Semantic Caching**: `core/semantic_cache.py` (lines 35-56) calls Gemini's `text-embedding-004` to fetch a 768-dimensional embedding, and then performs a cosine similarity search over SQLite (using NumPy if available, lines 236-280) or Postgres (using `pgvector`, lines 163-202).
- **Edge Cache Client**: `core/edge_cache.py` (lines 8-76) provides `EdgeCache`, which queries Upstash Redis using its serverless REST API (GET, SET, INCR, EXPIRE) via `httpx.AsyncClient`.
- **Cover Letter Generation**: `backend/ai_engine.py` (lines 9-13) initializes a direct Groq client `AsyncGroq(api_key=...)` and makes direct calls to Groq API (line 49), bypassing the multi-provider pool `LLMProviderPool` and `semantic_cache`.
- **ATS Matcher AI Fallback**: `core/ats_matcher.py` (lines 1175-1187) uses `LLMProviderPool` for AI-based analysis:
  ```python
  pool = _get_llm_pool()
  if pool:
      content = await pool.complete(
          system_prompt="You are an ATS expert. Answer in JSON only.",
          user_prompt=prompt,
          ...
      )
  ```
  However, it does not check or save results using `edge_cache`.

### 1.3 Stealth Scraping & TLS Fingerprinting
- **Stealth Client**: `core/stealth_http.py` uses `curl_cffi` to impersonate `chrome110` (lines 19, 54). For every `get` and `post` request, it creates a new `curl_requests.AsyncSession` or `Session` from scratch (lines 63, 78). It does not configure rotating proxies or custom aligned headers.
- **Scraper Profiles**: `scrapers/stealth_ingest.py` (lines 26-106) defines `STEALTH_PROFILES` including headers mapped to `impersonate="chrome120"` or `safari17_2_1` to align TLS signatures with HTTP headers.
- **Impersonate Bug**: `core/stealth.py` (lines 264-270) defines `_BROWSER_PROFILES`:
  ```python
  _BROWSER_PROFILES = [
      "chrome131",  # Chrome 131 (Windows) — most common desktop
      "chrome130",  # Chrome 130 (Windows) — second most common
      "chrome129",  # Chrome 129 (macOS)
      "safari18_0",  # Safari 18 (macOS) — avoid LinkedIn honeypots
      "edge99",  # Edge 99 (Windows)
  ]
  ```
  These are passed directly to `cffi_requests.AsyncSession(impersonate=profile)` on line 306.
- **Canvas Spoofing**: `core/stealth.py` (line 663) in `NodriverFallback` injects a Canvas spoofing script:
  ```javascript
  if (imageData.data.length > 0) {
      imageData.data[0] = (imageData.data[0] + 1) % 256;
  }
  ```
  However, the robust Canvas spoofing script with subpixel noise is defined on lines 347-366 but is never injected.

### 1.4 SMTP Warmup & Telegram Webhook
- **Free SMTP HTTP Stack**: `core/free_smtp_pool.py` configures `FreeSMTPPool` rotating across Resend, Mailgun, Elastic Email, ZeptoMail, turboSMTP, Mailjet, SendPulse, and Postmark free API tiers.
- **SMTP Warmup Engine**: `core/email_warmup.py` defines `EmailWarmup` and a warmup schedule (`WARMUP_SCHEDULE = {1: 50, 2: 100, 3: 150, 4: 200, 5: 300, 6: 400, 7: 500}`) storing status in `cache/email_warmup.json`. However, it is never imported or used.
- **SMTP Rate Limiting**: `core/email_engine.py` (lines 712-719) implements its own primitive warmup:
  ```python
  if hourly_limit > 10 and len(self.sent_times[provider]) < 5:
      actual_limit = min(hourly_limit, 10)
  ```
- **Telegram Bot Polling**: `core/telegram/bot.py` contains the polling loop `run_bot()` (line 4685) and the webhook handler `process_webhook_update()` (line 4814).
- **Telegram Webhook Endpoints**: `web/app_v2.py` exposes `/webhook/telegram` (line 8256) and setup/remove routes. These endpoints are missing from `backend/main.py`.

---

## 2. Logic Chain

### 2.1 Single-Container Web+Worker Fusion
- **Pool Solo Concurrency**: To run under 512MB RAM, we must prevent Celery from spawning multiple heavy processes. Celery's default `prefork` pool spawns multiple processes, duplication of SQLAlchemy pools, and high RAM usage. Running with `--pool=solo` (or `-P solo`) and `--concurrency=1` (or `-c 1`) executes Celery tasks in the main thread of the single worker process, saving 100MB+ memory.
- **Database Pool Optimization**: Reducing PG connection parameters (`pool_size=3` and `max_overflow=2`) prevents the app from holding idle connections, reducing PG memory allocation on both Python and Database sides.
- **SQLite Cache Optimization**: Setting `PRAGMA cache_size=-64000` allocates 64MB of memory to SQLite's cache. Changing this to `-2000` limits memory allocation to 2MB, saving 62MB of container RAM.
- **Celery Broker Fallback**: Under cloud-only environments without RabbitMQ, Celery will fail unless the broker falls back to `REDIS_URL`.

### 2.2 Edge-Cached Semantic Engine & Failover Pool
- **LLM Integration**: Cover Letter generation in `backend/ai_engine.py` should be updated to use the `LLMProviderPool` instead of a direct `AsyncGroq` client to support automated key rotation, rate-limiting control, and failover redundancy.
- **Upstash Redis Caching**:
  - Semantic caching via Gemini embeddings requires a network call to Gemini followed by a vector DB search.
  - Upstash Redis is globally distributed at the edge and extremely fast. We can compute a SHA-256 hash of the inputs (e.g. `hash(resume_text + job_description)` or `hash(job_description + user_cv)`), and use this hash as the key in Upstash Redis.
  - Doing an async check on Upstash Redis (`edge_cache.get(key)`) takes ~10-20ms and avoids expensive LLM calls completely for identical payloads.

### 2.3 Stealth Scraping & TLS Fingerprinting
- **Session Reuse & Keep-Alive**: `core/stealth_http.py` instantiates a new session on every single request, which drops cookies and closes connections. We must implement session reuse by holding a persistent `requests.AsyncSession` to maintain keep-alive and handle challenges correctly.
- **UA/JA3 Mismatch**: `core/stealth_http.py` impersonates `chrome110` but doesn't pass aligned headers. A mismatch in UA/JA3 signatures is instantly flagged by Cloudflare. Aligned header profiles (like those in `scrapers/stealth_ingest.py`) must be used.
- **Unsupported Browser crash**: In `core/stealth.py`, the `_BROWSER_PROFILES` array contains `"chrome131"`, `"chrome130"`, and `"chrome129"`. Passing these strings to `curl_cffi` throws `Unsupported browser` exceptions and crashes the program. We must map them to supported versions (e.g., `"chrome120"`).
- **Canvas Spoofing**: Injecting the robust pixel-by-pixel noise script from `StealthScraper` rather than the weak first-pixel-only script in `NodriverFallback` prevents canvas-based fingerprinting detection.

### 2.4 SMTP Warmup & Telegram Webhook
- **SMTP Warmup Integration**: The `EmailWarmup` class in `core/email_warmup.py` must be imported and integrated into `core/email_engine.py` to correctly track provider send dates and enforce the 7-day ramp-up schedule.
- **Reputation Warmup Cron**: A background Celery cron task should be added to periodically send organic peer-to-peer warmup emails to safe seed mailboxes to warm up active SMTP accounts before campaign blasts.
- **Telegram Webhook Migration**:
  - The webhook endpoints in `web/app_v2.py` must be ported to the new FastAPI main entrypoint `backend/main.py`.
  - To make webhook configuration automatic and resilient, the lifecyle manager (`lifespan`) in `backend/main.py` should invoke Telegram's `setWebhook` endpoint on startup.
  - The polling loop (`run_bot()`) should be disabled in production, allowing the bot to run 100% reactively inside the FastAPI process with zero idle memory usage.

---

## 3. Caveats
- **Public Proxies**: Scraping fallback logic relies on `api.proxyscrape.com` for public proxies if residential proxies are not set. Public proxies are highly unreliable and might fail.
- **Upstash Redis REST Limits**: Upstash REST API is fast, but it is rate-limited on free tiers. The code must gracefully handle REST failures/timeouts from Upstash.
- **Gemini Embeddings**: Semantic cache depends on `GEMINI_API_KEY` for text-embedding-004. If the key is rate-limited or missing, the cache will fall back to exact hash matching.

---

## 4. Conclusion
The codebase contains all necessary tools to run under a 512MB RAM footprint, implement fast edge caching, spoof TLS signatures stealthily, and migrate the Telegram bot to webhooks. However, these components are currently misconfigured, contain bugs (e.g., unsupported `curl_cffi` browser strings and weak canvas spoofing), or are completely disconnected (e.g., Cover Letter generation bypassing the LLM pool, and `email_warmup.py` being unused). Resolving these issues will secure a permanent, reliable $0 cloud hosting setup.

---

## 5. Verification Method

### 5.1 Test Suites
Run the following test commands to verify pool logic and stealth fallbacks:
```bash
pytest tests/test_llm_provider_pool.py
pytest tests/test_stealth_parser_and_fallbacks.py
```

### 5.2 Manual Inspections
- **Process List**: Verify that only `start_cloud.py` runs Celery with `-P solo -c 1`, Uvicorn with `--workers 1`, and the Database Sync worker (no separate Telegram bot process).
- **SQLite Cache**: Check `backend/database.py` line 75 to confirm the SQLite cache is tuned down (e.g., `PRAGMA cache_size=-2000`).
- **Webhook Check**: Verify that `backend/main.py` lifespan sets the webhook on startup and handles POST `/webhook/telegram`.

---

## 6. Proposed Code Modifications

### 6.1 start_cloud.py memory optimization
```python
# Replace line 56:
celery_cmd = ["celery", "-A", "backend.tasks", "worker", "--loglevel=info", "-P", "solo", "-c", "1"]
```

### 6.2 backend/celery_app.py broker fallback
```python
# Replace lines 7-15:
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
# Fall back to Redis if RabbitMQ is not configured
BROKER_URL = RABBITMQ_URL or REDIS_URL or "redis://localhost:6379/0"

celery_app = Celery(
    "jobhunt_tasks",
    broker=BROKER_URL,
    backend=REDIS_URL,
    include=["backend.tasks"]
)
```

### 6.3 backend/database.py pool size & cache optimization
```python
# In PostgreSQL config (replace lines 58-59):
        "pool_size":     3,     # scaled down for 512MB limits
        "max_overflow":  2,     # scaled down for 512MB limits

# In SQLite PRAGMA tuning (replace line 75):
        cursor.execute("PRAGMA cache_size=-2000")  # limited to 2MB to prevent RAM bloat
```

### 6.4 core/stealth.py unsupported browser fix
```python
# Replace lines 264-270 with valid curl_cffi strings:
    _BROWSER_PROFILES = [
        "chrome120",  # Map chrome131 -> chrome120 (supported)
        "chrome120",  # Map chrome130 -> chrome120
        "chrome120",  # Map chrome129 -> chrome120
        "safari17_2_1",  # Map safari18_0 -> safari17_2_1 (supported)
        "chrome120",  # Map edge99 -> chrome120
    ]
```

### 6.5 NodriverFallback Canvas Spoofing injection in core/stealth.py
```python
# Replace lines 662-672 with the robust pixel-by-pixel noise script:
            js_script = """
            (function() {
                // WebGL Spoofing
                if (window.WebGLRenderingContext) {
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) return 'Intel Inc.';
                        if (parameter === 37446) return 'Intel(R) UHD Graphics';
                        return getParameter.apply(this, arguments);
                    };
                }
                // Robust Canvas Spoofing (iterates all pixels)
                if (window.CanvasRenderingContext2D) {
                    const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                    CanvasRenderingContext2D.prototype.getImageData = function() {
                        const imageData = originalGetImageData.apply(this, arguments);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            const shift = Math.random() > 0.5 ? 1 : -1;
                            imageData.data[i] = Math.min(255, Math.max(0, imageData.data[i] + shift));
                        }
                        return imageData;
                    };
                }
                // Browser Attribute Spoofing
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            })();
            """
```
