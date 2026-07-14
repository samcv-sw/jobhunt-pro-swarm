# Handoff Report — teamwork_preview_explorer_m1_2

## 1. Observation
I have performed a detailed read-only investigation of the codebase and observed the following:
* **Next.js Location & Build**: Next.js is located in `/frontend/`. The file `/frontend/next.config.ts` specifies `"output": "export"` (line 11), generating static assets. The build command in `frontend/package.json` (line 7) is `"build": "node node_modules/next/dist/bin/next build --webpack"`.
* **CORS Middleware**: `/backend/main.py` loads allowed CORS origins from the `ALLOWED_ORIGINS` environment variable (lines 294-297) and wraps them inside `SecureCORSMiddleware` (lines 247-290).
* **Pages Edge Routing**: The file `/frontend/public/_worker.js` acts as the proxy router on Cloudflare Pages. It maps requests starting with `['/api/', '/ws/', '/_/pa/', '/scrape', '/health']` (line 7) to `const BACKEND_URL = 'https://jhfguf.pythonanywhere.com'` (line 6) and routes them.
* **Keep-Alive Workflows**: Directory `.github/workflows/` contains `keep-alive.yml` and `keep_alive.yml`, both configured on `cron: '*/10 * * * *'` to ping the Render backend.
* **Celery Process Spawning**: In `/start_cloud.py` (lines 116-124), Celery is spawned with `concurrency=1` on non-Windows systems:
  ```python
  celery_cmd = [sys.executable, "-m", "celery", "-A", "backend.tasks", "worker", "--loglevel=info"]
  if os.name == "nt":
      celery_cmd.extend(["-P", "solo"])
  else:
      celery_cmd.extend(["-c", "1"])
  ```
* **Database Connection & asyncpg**:
  * In `/backend/database.py` (lines 27-46), SQLAlchemy creates the database URL based on `DATABASE_URL`.
  * In `/backend/sync_worker.py` (lines 138-146), a raw `asyncpg.connect(raw_pg_url)` connection is established.
  * Attempting to connect directly via asyncpg using query parameters like `sslmode=require` or `prepareThreshold=0` fails, throwing `asyncpg.exceptions.InterfaceError: bad connection option`.
* **Stealth Proxy Scraper**: `/core/ghost_hunter.py` imports `Camoufox` and launches it without proxy arguments:
  ```python
  from camoufox.sync_api import Camoufox
  with Camoufox(headless=True) as browser:
  ```

## 2. Logic Chain
* **Next.js Cloudflare Pages Deployment**: Since the Next.js frontend has `output: "export"`, it compiles to static files. Standard redirect rules (like `_redirects`) can be defined in `/frontend/public/` so they end up in the build folder, but the advanced proxy behavior (WebSocket conversion, custom headers) is handled by `/frontend/public/_worker.js`. To proxy to Render, `BACKEND_URL` in `_worker.js` must be changed. For CORS validation, setting the environment variable `ALLOWED_ORIGINS` in the backend ensures the pages domain passes the regex checks in `SecureCORSMiddleware`.
* **GitHub Actions Keep-Alive**: To warm both Render `/healthz` and Neon DB, a new workflow run on `*/12 * * * *` is needed. Pinging `/healthz` is done via `curl`, while warming Neon DB is accomplished by executing the existing script `core/neon_warmer.py` with Python and the `DATABASE_URL` secret.
* **Celery Memory Guard**: Since `start_cloud.py` uses the standard prefork pool on Linux, appending Celery command-line flags `--max-tasks-per-child=10` and `--max-memory-per-child=150000` enables the built-in pool recycling to prevent memory leaks.
* **Neon PgBouncer Connection**: Because PgBouncer in transaction mode doesn't support prepared statements, disabling them is mandatory (`prepareThreshold=0`/`prepared_statement_cache_size=0`). Since `asyncpg` throws exceptions when parsing these parameters in the DSN URL, a wrapper function must intercept the URL, parse and remove these query params, and supply them as driver connection arguments (`ssl="require"` and `statement_cache_size=0`/`prepared_statement_cache_size=0`).
* **Free Proxy Rotation**: `GhostHunter`'s Camoufox instance is vulnerable to IP bans. An hourly-updating free proxy harvester pulling from `https://free-proxy-list.net/`, combined with rotating proxy initialization and a self-healing retry block, will prevent blockages.

## 3. Caveats
* The analysis assumes that the `psycopg2-binary` package is available in the environment running the GitHub actions workflow and can be installed via `pip`.
* The free proxy list `https://free-proxy-list.net/` is public; therefore, some proxies might have high latency or be blocked by LinkedIn. The proposed retry logic is critical to filter out these dead proxies dynamically.

## 4. Conclusion
We have identified the exact files, code segments, and configuration variables that must be updated. Complete implementations and code designs for all 5 milestones have been compiled in `/analysis.md`.

## 5. Verification Method
* **Milestone 1**: Inspect `frontend/public/_worker.js` and verify target `BACKEND_URL` matches the Render backend. Verify `ALLOWED_ORIGINS` env is set to the Cloudflare Pages domain.
* **Milestone 2**: Manually trigger the keep-alive workflow using `workflow_dispatch` in GitHub Actions.
* **Milestone 3**: Run `python start_cloud.py` on Linux and verify Celery worker initializes successfully.
* **Milestone 4**: Check that database connection pool tests succeed and verify `prepared_statement_cache_size=0` is set.
* **Milestone 5**: Execute `python core/ghost_hunter.py` and inspect logs to confirm proxies are scraped, loaded, and rotated.
