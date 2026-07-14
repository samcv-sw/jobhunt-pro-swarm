# Handoff Report — Milestones 1 to 5 Codebase Analysis

## 1. Observation
1. **Milestone 1 (Cloudflare Pages Next.js Deployment)**:
   - Next.js frontend code is located in `frontend/`.
   - `frontend/package.json` line 7: `"build": "node node_modules/next/dist/bin/next build --webpack"`.
   - `frontend/next.config.ts` line 11: `output: "export"`.
   - `backend/main.py` line 294: `allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")`.
   - `web/app_v2.py` line 842: `allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|chrome-extension://.*|https?://.*\.pages\.dev|https?://.*\.koyeb\.app"`.
2. **Milestone 2 (GitHub Actions Scheduled Keep-Alive)**:
   - Workflows directory: `.github/workflows/`.
   - Existing keep-alive: `.github/workflows/keep-alive.yml` pings `RENDER_APP_URL` or `https://jobhunt-pro.onrender.com/health` and `https://jobhunt-pro-swarm.onrender.com/health` every 10 minutes.
   - DB warming endpoint: `/api/v1/health/detailed` is defined in `backend/main.py` line 408 and performs a database query `SELECT 1`.
   - DB warming script: `core/neon_warmer.py` performs database query `SELECT 1` directly.
3. **Milestone 3 (Celery Memory Guard)**:
   - Celery worker launch command in `start_cloud.py` line 116: `celery_cmd = [sys.executable, "-m", "celery", "-A", "backend.tasks", "worker", "--loglevel=info"]`.
   - Programmatic settings in `backend/celery_app.py` lines 31-32:
     ```python
     worker_max_tasks_per_child=10,
     worker_max_memory_per_child=150000,
     ```
4. **Milestone 4 (Neon PgBouncer Connection String Updates)**:
   - Database URL resolving logic in `backend/database.py` lines 37-44:
     ```python
     if REMOTE_PG_URL:
         _db_logger.info('{"msg": "Connecting to remote PostgreSQL"}')
         url = REMOTE_PG_URL
         if url.startswith("postgresql://"):
             url = url.replace("postgresql://", "postgresql+asyncpg://")
         elif url.startswith("postgres://"):
             url = url.replace("postgres://", "postgresql+asyncpg://")
         return url
     ```
   - Connection URL mapping in `backend/sync_worker.py` line 23: `from .database import REMOTE_PG_URL, async_session` and line 138: `raw_pg_url = REMOTE_PG_URL.replace("postgresql+asyncpg://", "postgresql://") if REMOTE_PG_URL else None`.
5. **Milestone 5 (Free Proxy Pool Scraper Rotation)**:
   - Scraper logic in `core/ghost_hunter.py` lines 69-70:
     ```python
     with Camoufox(headless=True) as browser:
         page = browser.new_page()
     ```
     No proxy or rotation is currently set up.

---

## 2. Logic Chain
1. **Next.js & CORS**: Because Next.js uses static HTML export (`output: "export"`), Cloudflare Pages receives a purely static directory. Redirect/header files (`_redirects` and `_headers`) must be placed in `frontend/public/` so they are copied to `frontend/out/` during build. Updating the `ALLOWED_ORIGINS` environment variable on the host enables the backend's `SecureCORSMiddleware` to allow requests from the Pages custom or wildcard domains.
2. **Scheduled Keep-Alive**: To ping every 12 minutes, the cron expression should be `*/12 * * * *`. Pinging `/healthz` wakes the API container. Running `core/neon_warmer.py` using Python or curling `/api/v1/health/detailed` runs `SELECT 1` on Neon DB, keeping Neon database compute active.
3. **Celery Memory Guard**: Appending `--max-tasks-per-child=10` and `--max-memory-per-child=150000` to `celery_cmd` in `start_cloud.py` configures the spawned Celery worker. On Windows, `-P solo` ignores this. On Linux/Render, it utilizes `prefork` with concurrency 1, enabling safe recycling of the child process.
4. **Neon Connection String**: To direct Neon DB connections to PgBouncer, `_build_active_url()` in `database.py` should parse the remote Postgres URL, insert `-pooler` into the host, force port `5432`, and append query string parameters `sslmode=require&prepareThreshold=0`. Because `sync_worker.py` imports and references `REMOTE_PG_URL`, it automatically inherits the updated, pooled DSN configuration.
5. **Free Proxy Rotation**: Adding a free proxy scraper that parses `https://www.free-proxy-list.net/` and stores IPs in a JSON cache (`data/proxy_cache.json`) with an hourly TTL check avoids rate-limiting issues. Recreating the Camoufox browser instance when a proxy connection error occurs enables automatic rotation without crashing the worker process.

---

## 3. Caveats
- **Verification Limits**: Code execution was not performed as the scope of this task is strictly a read-only investigation.
- **Proxy Reliability**: Public free proxies are often unstable or slow. For a robust production setup, a commercial proxy service provider should be used.

---

## 4. Conclusion
The implementation plans described in `analysis.md` address all five milestone objectives without modifying the source files, aligning with the project's requirements.

---

## 5. Verification Method
1. **Next.js static files**: Compile using `npm run build` inside `frontend/` and verify that `out/_redirects` and `out/_headers` exist.
2. **CORS validation**: Check response headers of the `/healthz` endpoint with a custom origin:
   ```bash
   curl -H "Origin: https://my-app.pages.dev" -I https://jobhunt-pro-engine.onrender.com/healthz
   ```
3. **Keep-Alive**: Run the workflow manually in GitHub Actions and check the log output.
4. **Celery options**: Run `python start_cloud.py` and inspect the Celery worker process CLI parameters:
   ```bash
   ps -ef | grep celery
   ```
5. **Database connection**: Call the `/api/v1/health/detailed` endpoint to verify the connection.
6. **Proxy rotation**: Run `python core/ghost_hunter.py` and check the console logs for proxy allocation and rotation.
