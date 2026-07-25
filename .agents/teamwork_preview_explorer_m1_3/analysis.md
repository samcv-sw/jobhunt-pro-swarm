# Zero-PC Runtime Independence Audit Report: JobHunt Pro SaaS

## Executive Summary
JobHunt Pro SaaS demonstrates complete zero-PC runtime independence. The system is engineered to run 24/7 on $0 free-tier cloud infrastructure across Vercel, Render, Cloudflare Workers/Pages, and Supabase/Neon PostgreSQL. No active local PC server or desktop environment is required for continuous operation.

---

## 1. Direct Observations & Code Evidence

### 1.1 Serverless & Cloud Gateway Entry Points
- **Vercel Configuration (`vercel.json`)**:
  - `src: "web/app_v2.py"`, `use: "@vercel/python"`, routing all traffic `/(.*)` to FastAPI app.
  - Native WSGI/ASGI wrapper via `a2wsgi` / `@vercel/python` allowing serverless deployment on Vercel edge/lambda infra.
- **Render Service Blueprint (`render.yaml`)**:
  - Web service `jobhunt-pro-backend` configured on Render `plan: free` with Python 3.12.0 runtime.
  - Startup command: `uvicorn web.app_v2:app --host 0.0.0.0 --port $PORT --workers 2`.
  - Built-in `PORT` environment variable support.
- **Container Infrastructure (`Dockerfile` & `Dockerfile.cloud`)**:
  - Multi-stage Docker builds (`python:3.12-slim` builder + runtime).
  - Environment defaults set for non-root execution (`USER appuser` / `USER jobhunt`).
  - Native support for cloud environments with `PORT=7860` (HuggingFace Spaces) or `PORT=8000` (Railway/Render).

### 1.2 Autonomous Database Auto-Detection (`core/database.py`, `core/pg_sqlite_shim.py`, `core/supabase_rest_shim.py`)
- **Neon / PostgreSQL Auto-Detection (`core/database.py:65-74`)**:
  - Automatically parses `POSTGRES_URL`, `DATABASE_URL`, or `NEON_URL`.
  - `format_neon_connection_string()` rewrites Neon pooled connection endpoints (`-pooler`), enforces `sslmode=require`, sets `prepareThreshold=0`, and configures `statement_cache_size=0` to prevent PgBouncer transaction mode errors.
- **Resilient Connection Pooling for Cold Starts (`core/database.py:102-115`)**:
  - `QueuePool` configured with `pool_size=2`, `max_overflow=1`, `pool_timeout=30`, `pool_recycle=280`, and `pool_pre_ping=True`.
  - Conserves connections strictly under Neon's 10-connection free tier cap while surviving 5-minute auto-suspends.
- **Supabase REST Shim (`core/supabase_rest_shim.py`)**:
  - Provides a fallback PostgREST API client using `SUPABASE_SERVICE_KEY` for environments where direct TCP database ports (5432) are outbound-restricted.
- **Seamless Local SQLite Fallback (`core/pg_sqlite_shim.py:703-753`)**:
  - Automatically falls back to SQLite (`aiosqlite`/`sqlite3`) if no remote database environment variable is configured.

### 1.3 24/7 Background Workers & Multi-Cloud Cron Orchestration
- **GitHub Actions Scheduled Runners (`.github/workflows/`)**:
  - `keepalive_ultra_247.yml`: Runs every 5 minutes (`cron: '*/5 * * * *'`), sending HTTP ping requests to Render (`/health`), HuggingFace, and Cloudflare Worker nodes to prevent free-tier spin-down.
  - `scheduled_runner.yml`: Triggers remote background job scans (`/api/v1/trigger-scan`) every 30 minutes via API request.
  - `job-hunt.yml` & `auto_apply.yml`: Autonomous job search and auto-application execution triggered directly on GitHub Actions runners without requiring local PC execution.
- **Cloudflare Worker Cron Edge Triggers (`cloudflare/wrangler.toml` & `cloudflare/keepalive_cron/wrangler.toml`)**:
  - `wrangler.toml` configures `crons = ["*/4 * * * *"]` for edge routing and periodic trigger invocation.
  - Bound to Cloudflare D1 Database (`DB`), KV Cache (`CACHE`), Workers AI (`AI`), and R2 Storage (`BUCKET`).

---

## 2. Logic Chain

1. **Zero Local PC Dependency**:
   - The application codebase contains zero hardcoded local filesystem paths (`C:\Users\...`). All storage, configuration, and state management utilize environment variables (`os.getenv`), Cloud PostgreSQL (Neon/Supabase), Cloudflare KV/D1/R2, or transient `/tmp` directories.
   - When deployed to Render/Vercel/Cloudflare, all core REST endpoints (`backend/main.py` & `web/app_v2.py`) execute independently of the developer's local workstation.

2. **Serverless Edge Compatibility**:
   - Vercel's serverless Python runtime creates ephemeral execution contexts.
   - SQLite database writes on ephemeral local disks (`/tmp`) reset on cold start; however, `core/database.py` seamlessly switches to Neon PostgreSQL (`postgresql+asyncpg://`) or Supabase REST when `POSTGRES_URL` / `DATABASE_URL` is set in Vercel environment settings.
   - CORS validation (`SecureCORSMiddleware`) dynamically handles wildcard subdomains and production domains.

3. **Background Job Execution Architecture**:
   - On long-running cloud containers (Render / Docker / Railway), background tasks run continuously via FastAPI `BackgroundTasks` or `ThreadPoolExecutor` (`celery_dispatch_executor`).
   - On serverless providers (Vercel), background execution threads freeze post-HTTP response. The platform resolves this by offloading scheduled background jobs to external triggers:
     1. GitHub Actions workflows (`scheduled_runner.yml`, `keepalive_ultra_247.yml`).
     2. Cloudflare Worker Cron Triggers (`cloudflare/wrangler.toml`).
     3. Periodic webhook endpoints (`/api/v1/trigger-scan`, `/webhook/telegram`).

---

## 3. Caveats

1. **Vercel Ephemeral Execution Freeze**:
   - Long-running in-process background threads (e.g. `email_marketing_loop`) inside `web/app_v2.py` will be suspended on Vercel once the initial HTTP response completes. Heavy background jobs MUST be triggered via GitHub Actions crons or hosted on Render/Railway.
2. **Neon PostgreSQL Free-Tier Connection Limit**:
   - Neon free tier limits active connections to 10. `core/database.py` enforces `pool_size=2`, `max_overflow=1` per worker process to avoid connection exhaustion under multi-instance scaling.
3. **Playwright / Heavy Scraper Restrictions on Vercel**:
   - Browser automation using Playwright/Chromium cannot run inside standard Vercel serverless functions (due to bundle size limits >50MB). Stealth scraping operations must route to Render/Docker instances or external scraping APIs (`curl_cffi`).

---

## 4. Conclusion

JobHunt Pro SaaS is fully architecture-ready for **100% Zero-PC Runtime Independence**.
- **Web App & APIs**: Deployable on **Vercel** or **Render**.
- **Persistence Layer**: **Neon PostgreSQL** or **Supabase** (with automatic SQLite fallback for local testing).
- **Edge Routing & Caching**: **Cloudflare Workers / Pages** with D1, KV, and R2 bindings.
- **Background Execution & Keep-Alive**: **GitHub Actions Cron Workflows** + **Cloudflare Cron Triggers**.

---

## 5. Verification Method

1. **Database Resilience Test**:
   - Set `POSTGRES_URL="postgresql://user:pass@ep-cool-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require"` in environment.
   - Run `python -c "from core.database import NEON_URL; print(NEON_URL)"`.
   - Invalidation Condition: Failure to append `-pooler` or convert scheme to `postgresql+asyncpg://`.

2. **Test Suite Verification**:
   - Execute pytest test suite in repository:
     ```bash
     pytest tests/
     ```
   - Invalidation Condition: Any test failures related to database connection or env missing.
