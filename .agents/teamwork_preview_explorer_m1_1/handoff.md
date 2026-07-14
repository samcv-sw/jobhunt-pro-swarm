# Handoff Report: Cloud Infrastructure Optimizations (Milestones 1-5)

This handoff report summarizes the read-only codebase investigation and design proposals for Milestones 1 to 5. Detailed changes are documented in `analysis.md`.

---

## 1. Observation

Direct observations made in the codebase:
* **Milestone 1 (Cloudflare Pages Next.js Deployment)**:
  - Frontend location: `frontend/` folder.
  - In `frontend/next.config.ts` (line 11): `output: "export"` is set, producing a static build in `frontend/out/`.
  - Cloudflare Pages Worker router exists in `cloudflare/pages/_worker.js` (lines 4-6):
    ```javascript
    const WORKER_URL = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev';
    const PROXY_PATHS = ['/api/', '/_/pa/', '/scrape', '/health'];
    ```
  - Backend CORS settings: Loaded in `backend/main.py` (lines 294-297) from `os.getenv("ALLOWED_ORIGINS", "")`.
* **Milestone 2 (GitHub Actions Keep-Alive)**:
  - Keepalive workflows: `.github/workflows/keep-alive.yml` and `.github/workflows/keep_alive.yml` exist. They run on a `*/10 * * * *` (10-minute) schedule.
  - Endpoint: `backend/main.py` defines `@app.get("/healthz")` (lines 378-381) as a lightweight health check, and `/api/v1/health/detailed` (lines 408-425) which runs a database `SELECT 1` query.
  - Database warmer script: `core/neon_warmer.py` is present, executing raw SQL `SELECT 1` using `psycopg2`.
* **Milestone 3 (Celery Memory Guard)**:
  - Worker spawn logic: Found in `start_cloud.py` (lines 115-124):
    ```python
    celery_cmd = [sys.executable, "-m", "celery", "-A", "backend.tasks", "worker", "--loglevel=info"]
    if os.name == "nt":
        celery_cmd.extend(["-P", "solo"])
    else:
        celery_cmd.extend(["-c", "1"])
    ```
  - Celery config: `backend/celery_app.py` already specifies `worker_max_tasks_per_child=10` and `worker_max_memory_per_child=150000` (lines 31-32).
* **Milestone 4 (Neon PgBouncer Connection String Updates)**:
  - Database config: `backend/database.py` (lines 27-46) parses `DATABASE_URL` as `REMOTE_PG_URL`.
  - Prepared statement compatibility: PgBouncer transaction-mode connection poolers conflict with `asyncpg` prepared statements.
  - Outbox Sync: `backend/sync_worker.py` (lines 143-146) connects to remote PG via `asyncpg.connect(raw_pg_url)`.
* **Milestone 5 (Free Proxy Pool Scraper Rotation)**:
  - Scraper: `core/ghost_hunter.py` uses `BeautifulSoup`, `DDGS`, and `Camoufox`.
  - Loop structure (lines 66-70): `Camoufox` is launched once, and queries `jobs` inside the loop (lines 74-82) after the browser is already running.

---

## 2. Logic Chain

1. **Static Next.js Routing**: Because the frontend is a static export, proxying to the backend API cannot happen in Next.js itself. The Pages edge router `_worker.js` handles requests programmatically. For declarative redirects, a `_redirects` file can be placed in `frontend/public/_redirects` which Next.js copies to `out/_redirects`. Adding Cloudflare Pages domains to `ALLOWED_ORIGINS` in Render environment configurations updates CORS allowed origins.
2. **Keep-Alive and Database Warming**: Render spins down after 15 minutes of inactivity; Neon databases suspend after 5 minutes of idle time. Running a GitHub Action keep-alive every 12 minutes (cron: `*/12 * * * *`) that pings Render `/healthz` and either triggers `core/neon_warmer.py` or pings `/api/v1/health/detailed` keeps both backend and database active 24/7.
3. **Memory Limits in Celery**: On Windows, Celery uses `solo` pool, where process recycling is not supported. On Linux (Render), it runs with standard `prefork` pool (`-c 1`), which supports process recycling. Adding `--max-tasks-per-child=10` and `--max-memory-per-child=150000` directly to `celery_cmd` in `start_cloud.py` enforces these limits on Linux and prevents memory bloat.
4. **PgBouncer prepared statement cache**: `asyncpg` prepared statements must be disabled for compatibility with PgBouncer. Rewriting the connection URL in `database.py` to target port 5432 and the `-pooler` host, while appending `?sslmode=require&prepareThreshold=0`, keeps JDBC/external clients happy. However, since the Python `asyncpg` driver raises a `ValueError` for unknown query parameters like `prepareThreshold`, the URL query parameters must be stripped before calling `create_async_engine` (SQLAlchemy) or `asyncpg.connect()` (sync worker), passing `statement_cache_size=0` and `ssl=True` via driver-level arguments instead.
5. **Proxy Rotation and Jitter**: Public scraping on LinkedIn requires IP rotation to evade rate-limiting. A class `ProxyManager` scrapes free proxies hourly and stores them in `cache/proxy_pool.json`. Instantiating `Camoufox` per URL with a new proxy from the pool enables clean rotation. Moving the duplicate check to the beginning of the loop (lazy evaluation) prevents launching the browser for duplicate URLs, drastically saving memory.

---

## 3. Caveats

* Free proxies are highly unstable. A proxy might fail to connect mid-scrape. The `ProxyManager` handles this by catching connection exceptions, marking the failed proxy to evict it from the pool, and proceeding.
* Celery `--max-tasks-per-child` will trigger worker recycling, which is safe since the sync worker and database will preserve state, but could cause short delays when a new child process is spawned.
* We assume the environment variables `DATABASE_URL` and `ALLOWED_ORIGINS` are correctly configured on Render/Koyeb and GitHub secrets.

---

## 4. Conclusion

All five optimization milestones are thoroughly analyzed. Implementations are fully designed, scoped, and documented with copy-paste-ready Python, YAML, and configuration blocks in `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_1\analysis.md`. The proposed modifications are backward-compatible and directly address Render memory/cold-start limits, Neon transaction pooling constraints, and scraper durability.

---

## 5. Verification Method

Independent verification of the design proposals can be performed as follows:
1. **Next.js static build**: Run `npm run build` in `frontend/` and confirm that `frontend/out/` contains `_redirects` and the static HTML files.
2. **FastAPI CORS configuration**: Set `ALLOWED_ORIGINS="https://*.pages.dev"` and send a test request with an origin header matching a pages deployment; verify the response contains `Access-Control-Allow-Origin: [matching origin]`.
3. **Celery Worker Recyclability**: On Linux, start `start_cloud.py` with `REDIS_URL` active, trigger 10 mock tasks, and verify in the stdout log that the Celery child process recycles.
4. **PgBouncer & Asyncpg**: Connect to a Neon database using the modified URL with transaction pooling enabled. Ensure queries execute successfully without `prepared statement does not exist` errors.
5. **Ghost Hunter Scraper**: Run `python core/ghost_hunter.py` and confirm that:
   - A `cache/proxy_pool.json` is generated with scraped proxies.
   - Camoufox runs successfully using a selected proxy.
   - Stale/failed proxies are correctly evicted from the pool.
