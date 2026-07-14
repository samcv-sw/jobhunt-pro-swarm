## 2026-07-12T10:24:00Z
You are teamwork_preview_worker.
Your task is to implement the following requirements in the JobHunt Pro workspace:

### 1. Cloudflare Pages Next.js Deployment
- In `frontend/public/_worker.js`, update `BACKEND_URL` to `'https://jobhunt-pro.onrender.com'` with fallback:
  `const BACKEND_URL = (typeof env !== 'undefined' && env.BACKEND_URL) || 'https://jobhunt-pro.onrender.com';`
- Create `frontend/public/_redirects` to proxy/redirect requests from `/api/v1/*` to the Render backend URL:
  `/api/v1/* https://jobhunt-pro.onrender.com/api/v1/:splat 200`
- Modify `backend/main.py` allowed origins list to include `"https://*.pages.dev"` to enable CORS credentials and allow Cloudflare Pages subdomains securely.

### 2. GitHub Actions Scheduled Keep-Alive (24/7 Free Uptime)
- Create `.github/workflows/keepalive.yml` that runs on a schedule every 12 minutes (`cron: "*/12 * * * *"`).
- It should run a curl script to ping `https://jobhunt-pro.onrender.com/healthz` (Render backend) and also execute `core/neon_warmer.py` using python to warm the Neon database. (Install psycopg2-binary in the python environment in the workflow).

### 3. Celery Memory Guard Configuration
- In `start_cloud.py`, modify the celery worker command (line 114-131 or similar).
- For Linux (Render), add `--max-tasks-per-child=10` and `--max-memory-per-child=150000` (150MB) to the celery command line args to recycle worker processes frequently and prevent memory leaks. Do not add these to the Windows solo pool branch.

### 4. Neon PgBouncer Connection String Updates
- Modify `backend/database.py` and `backend/sync_worker.py` to support Neon PgBouncer connection pooling.
- Create a utility function `format_neon_connection_string(url: str) -> str` that rewrites PostgreSQL database URLs:
  - Targets port 5432.
  - Ensures `-pooler` is inserted in the host if host is a Neon host (e.g. `ep-*.neon.tech` becomes `ep-*-pooler.neon.tech`).
  - Appends query parameters `sslmode=require&prepareThreshold=0`.
- In `backend/database.py`, use this utility on `os.getenv("DATABASE_URL")`. Clean/strip these parameters from `ACTIVE_DB_URL` before calling `create_async_engine()`, and pass `ssl=True` and `prepared_statement_cache_size=0` inside `connect_args`.
- In `backend/sync_worker.py`, format the raw database URL using the utility, then strip parameters before calling `asyncpg.connect()`, passing `ssl="require"` and `statement_cache_size=0` explicitly to avoid `asyncpg` parser errors.

### 5. Free Proxy Pool Scraper Rotation
- In `core/ghost_hunter.py`, implement a class `ProxyManager` that scrapes free HTTP/HTTPS proxies from `https://free-proxy-list.net/` and `https://www.sslproxies.org/` hourly, caches them to `cache/proxy_pool.json`, validates and rotates them when initiating the Camoufox browser.
- Update `GhostHunter.hunt_for_user()` to:
  - Perform the duplicate job URL check before spawning the browser process (to save memory).
  - Launch Camoufox using the rotated proxy.
  - Catch connection errors and mark failed proxies to evict them from the pool.

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT
> hardcode test results, create dummy/facade implementations, or
> circumvent the intended task. A Forensic Auditor will independently
> verify your work. Integrity violations WILL be detected and your
> work WILL be rejected.

Verify your changes:
- Run a build check / compiler check on all modified Python files to ensure zero syntax errors.
- Run `pytest` to make sure the existing tests pass successfully.
- Write a report of your changes in `handoff.md` inside your working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_cloud_stealth_reliability\handoff.md.
