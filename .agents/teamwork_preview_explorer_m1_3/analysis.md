# Baseline Audit Report: PythonAnywhere & Backend Compatibility Analysis

## Executive Summary
This report analyzes JobHunt Pro's compatibility with PythonAnywhere's restricted hosting environment, evaluates core endpoint performance to identify timeout risks, audits the authentication rate limiters (Aegis Shield) and scraper anti-ban systems, and establishes a baseline test suite execution.

While the baseline test suite shows a **100% pass rate** (632/632 passing locally), several critical architectural issues must be addressed before production deployment on PythonAnywhere to avoid server freezes, database locks, and gateway timeouts.

---

## 1. PythonAnywhere Compatibility Issues

### A. Ephemeral Background Tasks inside ASGI/WSGI Lifespan
- **Observations**: 
  - `web/app_v2.py` (lines 556-636) utilizes FastAPI's `lifespan` hook to initialize and run asynchronous background loops: `email_marketing_loop()`, `_honeypot_cleanup_loop()`, `_campaign_self_tick_loop()`, `_seo_blog_farm_loop()`, and `start_worker()`.
  - It uses a file lock (`jobhunt_background_loops.lock` in the `/tmp` folder) to prevent multiple workers from running these loops simultaneously.
- **PythonAnywhere Impact**: 
  - Web apps on PythonAnywhere run inside a managed WSGI/uWSGI server where worker processes are ephemeral, automatically recycled, and shut down due to inactivity.
  - Spawning long-running tasks via `asyncio.create_task()` directly in the web process will lead to abrupt terminations. If a worker process holding the loop lock is recycled, the loops stop until another worker process triggers the lock check, causing inconsistent campaign scheduling and delayed emails.
  - Celery background workers (`core/worker.py`) cannot run inside the web app process. On PythonAnywhere, background workers require a separate "Always-on task" (only available on paid accounts), making standard background execution fail in the free tier.

### B. Excessive Global ThreadPoolExecutor Max Workers
- **Observations**: 
  - `backend/main.py` (line 131) instantiates a global `celery_dispatch_executor = ThreadPoolExecutor(max_workers=32, thread_name_prefix="celery_dispatch")`.
- **PythonAnywhere Impact**: 
  - PythonAnywhere places strict limits on the number of system threads and file descriptors per user account.
  - Creating a ThreadPoolExecutor with 32 workers globally inside the web app process—especially when multiple uWSGI worker processes are spawned—can easily exceed thread limits, leading to process crashes or `ResourceTemporarilyUnavailable` errors.

### C. Outbound Proxy and Connection Whitelisting
- **Observations**:
  - `backend/main.py` (`LogtailHandler`, line 80) sends log entries to `https://in.logs.betterstack.com` via `urllib.request.urlopen(req, timeout=5)`.
  - `core/aegis_shield.py` (`_UpstashClient._exec`, line 86) sends rate-limit queries to Upstash Redis REST API (`https://...upstash.io`) using `urllib.request.urlopen(req, timeout=3)`.
  - `backend/main.py` (lifespan hook, line 156) registers webhooks by querying `https://api.telegram.org`.
- **PythonAnywhere Impact**:
  - PythonAnywhere free tier accounts block all outbound TCP traffic except to whitelisted HTTP/HTTPS domains (e.g., Telegram API is generally whitelisted, but custom logging endpoints and Upstash Redis may not be).
  - Outbound HTTP connections must explicitly route through the local proxy (`http://proxy.server:3128`). Standard urllib calls do not automatically apply proxy settings unless `http_proxy` / `https_proxy` env vars are properly parsed, leading to network timeouts and connection errors.

### D. SQLite Concurrency and NFS locking Bottlenecks
- **Observations**:
  - `core/pg_sqlite_shim.py` (line 727) and `web/app_v2.py` (line 1341) explicitly force `PRAGMA journal_mode=DELETE` and `PRAGMA synchronous=FULL` when running under PythonAnywhere.
- **PythonAnywhere Impact**:
  - PythonAnywhere storage is mounted over a distributed Network File System (NFS). Because NFS does not support POSIX shared memory locks, SQLite's high-performance Write-Ahead Logging (WAL) mode cannot be used and causes file locking failures.
  - Forcing `DELETE` journal mode and `FULL` synchronous operations prevents database corruption but introduces severe latency. Every write operation requires deleting/re-creating the journal file and executing synchronous disk flushes over the network, slowing queries by up to 10-100x compared to WAL mode.
  - Simultaneous writes (e.g., user registration, login attempts, rate limiter increments, campaign status updates) will serialize and cause frequent `database is locked` (`SQLITE_BUSY`) exceptions.

### E. WebSockets Protocol Limitations
- **Observations**:
  - `backend/main.py` (line 398) loads `backend.routers.websocket`.
- **PythonAnywhere Impact**:
  - PythonAnywhere web apps do not support WebSockets or long-lived server-sent events. Connection requests to WebSocket routers will return `502 Bad Gateway` or fail to connect.

---

## 2. Core Endpoint Speed & Timeout Risks

### A. Dashboard Stats Endpoint (`/api/v1/dashboard/stats`)
- **Path**: `web/routers/dashboard.py` (lines 23-73)
- **Logic**: Executes a `LEFT JOIN campaigns` query grouped by `u.user_id` and `u.wallet_balance`.
- **Risk**: 
  - Although `campaigns.user_id` is indexed, aggregating metrics (such as summing `sent_count` and counting active/completed statuses) across a large volume of rows for active users will slow down.
  - Under SQLite `DELETE` mode on NFS, if this query is executed concurrently with write operations, it will block, leading to slow dashboard load times and potential HTTP 504 Gateway Timeouts.
  - *Mitigation note*: It returns a `Cache-Control: private, max-age=30` header, which helps cache the response for 30s in the client browser, but does not protect against concurrent backend hits.

### B. DLQ Requeue Endpoint (`/api/v1/admin/dlq/requeue`)
- **Path**: `backend/routers/admin.py` (lines 20-58)
- **Logic**: Performs a batch update: `UPDATE ps_crud_outbox SET synced = 0, created_at = :now WHERE synced = 0 AND created_at < :cutoff`.
- **Risk**:
  - The outbox table (`ps_crud_outbox`) tracks all local mutations. If synchronization breaks, the table will grow rapidly.
  - Executing a mass `UPDATE` statement locks the entire SQLite database file under `DELETE` journal mode. During the update, all incoming requests (logins, dashboard queries, public landing pages) will be blocked and will wait on the SQLite lock. If the update takes more than a few seconds, it will exhaust the web server's worker threads, triggering a site-wide crash or timeout.

### C. Rate Limit Synced Database Write Locking
- **Path**: `web/shared.py` (lines 165-197)
- **Logic**: The IP rate limiter `_check_rate_limit` reads and updates rate-limit records in the database: `REPLACE INTO system_config (key, value) VALUES (?, ?)`.
- **Risk**:
  - To sync rate limits across workers without Redis, it writes to the SQLite database.
  - Because it runs a `REPLACE INTO` query on **every login and registration attempt**, this creates a write-lock bottleneck. Under moderate traffic, multiple parallel authentication checks will cause SQLite thread contention, locking out users and throwing database errors.

---

## 3. Auth Rate Limits (Aegis/Banshield) & Scraper Anti-Ban

### A. Aegis Shield rate Limiting Latency Hazard
- **Logic**: `AegisShieldMiddleware` (lines 274-415) intercepts every HTTP request. If Upstash Redis is configured, it executes `token_bucket_check` which calls Upstash via HTTP REST.
- **Risk**:
  - Making a synchronous outbound HTTP REST request to Upstash Redis for **every incoming web request** introduces massive overhead (50-200ms latency per request) and will block the ASGI thread.
  - If Upstash experiences network latency or downtime, the 3-second request timeout in the rate limiter will exhaust the WSGI worker pool instantly, causing immediate 542/504 gateway timeouts for all users.
  - On free PythonAnywhere accounts, the connection will be blocked by default since external Upstash URLs are not whitelisted, causing a fallback to in-memory limits.

### B. Scraper Anti-Ban and `curl_cffi` Binary Compilation Fallback
- **Logic**: `core/pa_job_scraper.py` (lines 405-440) performs job scraping using `curl_cffi` (which spoof browser TLS signatures to bypass Cloudflare). If `curl_cffi` fails to load, it falls back to `urllib` requesting.
- **Risk**:
  - `curl_cffi` relies on compiled C extensions and shared libraries (`libcurl-impersonate`). Installing it on PythonAnywhere often fails due to missing compilation tools or restricted user environments.
  - Falling back to `urllib` uses standard TLS signatures, which will trigger immediate bot blocks (Cloudflare 403 Forbidden) from major job sites (LinkedIn, Indeed), rendering the scraping engine inoperable.
  - Outbound scraping to non-whitelisted job boards is blocked entirely on PythonAnywhere free accounts.

---

## 4. Baseline Test Suite Execution Status

The full pytest test suite was executed inside the virtual environment using `uv run pytest`.

### Execution Summary
- **Total Collected Tests**: 632
- **Passed**: 632
- **Failed**: 0
- **Skipped**: 0
- **Total Execution Time**: 188.84 seconds (~3 minutes 9 seconds)
- **Status**: 100% Baseline Pass Rate

The test suite covers:
1. E2E routes, landing pages, and frontend templates.
2. Rate limiters (Aegis Shield WAF, Banshield, and daily caps).
3. Database interfaces and the PG-to-SQLite translation shim (`pg_sqlite_shim`).
4. AI cover letter engines, ML ranking models, and email dispatchers.

---

## 5. Actionable Optimization & Hardening Steps (Milestone 4 Targets)

To ensure high performance and stable deployment on PythonAnywhere, we propose the following changes:

1. **Decouple Background Loops from Web Process**:
   - Disable active background loops inside the web app on PythonAnywhere using environment variables (e.g. `RUN_BACKGROUND_LOOPS=false`).
   - Re-route these loops to a dedicated CLI python script and configure them as standard PythonAnywhere Scheduled Tasks (e.g. running once per hour or once per day depending on task urgency).

2. **Optimize SQLite Write Contention on NFS**:
   - Implement an in-memory fallback cache for rate-limiting data (`_check_rate_limit`) when running on PythonAnywhere. Avoid using the database (`system_config` table) for transient request counting.
   - Restructure DLQ requeue transactions to use pagination or chunked updates (e.g., updating in batches of 100 records) to release the SQLite database lock quickly and avoid blocking other users.

3. **Limit Thread Pool Count**:
   - Dynamically scale the global `ThreadPoolExecutor` worker count in `backend/main.py` based on the detected hosting environment. If running on PythonAnywhere, reduce `max_workers` from 32 to 4 or 8 to prevent resource exhaustion.

4. **Harden Aegis Shield Redis Fallback**:
   - Add a circuit breaker to Upstash Redis REST calls. If the REST API fails or times out once, disable Redis rate-limiting and fall back to the in-memory rate-limiter for 5 minutes.
   - For free accounts, skip Upstash REST connection entirely and use in-memory state.

5. **Ensure Stealth Scraper Compatibility**:
   - Provide pre-compiled wheels for `curl_cffi` or ensure that compilation steps are validated in the PythonAnywhere setup script.
   - If fallback to `urllib` is required, configure it to route requests through the PythonAnywhere proxy (`http://proxy.server:3128`) and randomize browser headers to reduce ban risk.
