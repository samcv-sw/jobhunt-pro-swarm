# Handoff Report — teamwork_preview_explorer_m1_3

## 1. Observation
- **Test Suite baseline execution**: 
  - Ran `uv run pytest` under project directory `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`.
  - Pytest output: `======================= 632 passed in 188.84s (0:03:08) =======================`
- **Background tasks in web application**:
  - `web/app_v2.py` (lines 556-636) lifespan hook:
    ```python
    task1 = asyncio.create_task(email_marketing_loop())
    task2 = asyncio.create_task(_honeypot_cleanup_loop())
    task3 = asyncio.create_task(_campaign_self_tick_loop())
    task4 = asyncio.create_task(_seo_blog_farm_loop())
    _background_tasks.extend([task1, task2, task3, task4])
    ```
- **Thread pool sizes**:
  - `backend/main.py` (lines 131-134):
    ```python
    celery_dispatch_executor = ThreadPoolExecutor(
        max_workers=32,
        thread_name_prefix="celery_dispatch"
    )
    ```
- **Synchronous rate limiting network request**:
  - `core/aegis_shield.py` (lines 92-102) Upstash exec wrapper:
    ```python
    req = urllib.request.Request(
        self.url,
        data=payload,
        headers={
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=3) as resp:
        return json.loads(resp.read()).get("result")
    ```
  - Running every request inside `AegisShieldMiddleware` (line 357):
    ```python
    allowed_req, remaining, retry_after = await asyncio.to_thread(_redis.token_bucket_check, client_ip)
    ```
- **SQLite journal mode under PythonAnywhere**:
  - `core/pg_sqlite_shim.py` (lines 727-730):
    ```python
    if is_pa:
        self.conn.execute("PRAGMA journal_mode=DELETE")
        self.conn.execute("PRAGMA synchronous=FULL")
    ```
  - `web/app_v2.py` (lines 1341-1342) in `get_db()`:
    ```python
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA synchronous=FULL")
    ```
- **Rate limiter DB writes**:
  - `web/shared.py` (lines 184, 189, 193) `_check_rate_limit()`:
    ```python
    conn.execute("REPLACE INTO system_config (key, value) VALUES (?, ?)", (db_key, f"{now}:1"))
    ```
- **DLQ Requeue Endpoint DB locks**:
  - `backend/routers/admin.py` (lines 45-51):
    ```python
    query_str = "UPDATE ps_crud_outbox SET synced = 0, created_at = :now WHERE synced = 0 AND created_at < :cutoff"
    ...
    result = await session.execute(stmt, params)
    await session.commit()
    ```
- **Scraper user-agent fallback**:
  - `core/pa_job_scraper.py` (lines 429-439):
    ```python
    except ImportError:
        logger.warning("[PAJobScraper] curl_cffi not installed, falling back to urllib (HIGH BAN RISK)")
        ...
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    ```

## 2. Logic Chain
1. **Background Tasks**: Because web apps on PythonAnywhere run under managed uWSGI servers that recycle processes automatically on inactivity, any task spawned asynchronously inside the ASGI lifecycle (`email_marketing_loop`, etc. in `web/app_v2.py` lines 556-636) will be terminated unexpectedly, causing data synchronization gaps and loop failures.
2. **Thread Limits**: PythonAnywhere imposes low caps on user threads. instantiating a ThreadPoolExecutor with 32 workers globally (`backend/main.py` line 131) risks exceeding these limits when multiple uWSGI worker processes are running.
3. **Upstash REST Latency**: `AegisShieldMiddleware` runs `token_bucket_check` on every request. This executes a synchronous `urllib` HTTP POST request to Upstash Redis. If the Upstash REST endpoint slows down or is blocked by PythonAnywhere's firewall (which blocks non-whitelisted destinations on free accounts), it will hit the 3-second timeout, exhaust uWSGI threads, and trigger site-wide 504 Gateway Timeouts.
4. **SQLite NFS Write Contentions**: WAL mode is disabled on PythonAnywhere since NFS does not support shared memory mapped files. Because uWSGI runs multiple worker processes and SQLite is forced to `journal_mode=DELETE` and `synchronous=FULL` (to prevent corruption), every write blocks the entire database file.
5. **Rate Limiting and DLQ Contention**: The `_check_rate_limit` endpoint performs a database write (`REPLACE INTO system_config`) for every login/registration query, and `/api/v1/admin/dlq/requeue` does a mass update on `ps_crud_outbox`. These write-heavy operations will cause database file locking under concurrent traffic, blocking readers and triggering timeouts.
6. **Scraper Bans**: `curl_cffi` requires compiled native binaries. If it fails to compile or load in PythonAnywhere's restricted environment, the scraper falls back to `urllib` which cannot spoof browser TLS fingerprints, leading to immediate blocks by major job sites (LinkedIn/Indeed).

## 3. Caveats
- Outbound connection testing was not performed directly on a live PythonAnywhere server, but inferred based on the official PythonAnywhere security whitelist and proxy documentation.
- We assumed the free or standard PythonAnywhere hosting environments are being used, which have stricter process and network proxy controls compared to a self-managed VPS.

## 4. Conclusion
While the codebase is functional and passes all 632 test cases, it is not optimized for PythonAnywhere's distributed NFS storage and uWSGI process limits.
Deploying it without changes will result in:
1. Deadlocks and timeouts due to synchronous Upstash Redis requests.
2. Ephemeral loop terminations because background task loops run inside uWSGI workers.
3. `database is locked` errors due to write-heavy rate-limit syncing (`REPLACE INTO system_config`) and massive DLQ updates on SQLite `journal_mode=DELETE`.
4. High ban risk on scrapers falling back to `urllib`.

## 5. Verification Method
- **Pytest command**: Run `uv run pytest` under the root directory to verify that all 632 test cases pass.
- **Config inspection**: Verify the active database configuration in `backend/database.py` and `core/database.py` to ensure correct handling of SQLite and Postgres connections.
