# Codebase Analysis & Design Report: Cloud Infrastructure Optimizations (Milestones 1-5)

This report details the codebase investigation and provides copy-paste-ready design strategies and code modifications for deploying and hardening the JobHunt Pro application on a $0 cloud infrastructure.

---

## Executive Summary
The JobHunt Pro codebase has been audited across five key architectural areas. By implementing Next.js static exports, a GitHub Actions scheduled heartbeat, Celery child-worker memory caps, Neon PgBouncer compatibility tweaks, and an automated free proxy pool manager, the platform is prepared for 24/7 autonomous operation within the constraints of Render, Neon, and Cloudflare free tiers.

---

## 1. Cloudflare Pages Next.js Deployment (Milestone 1)

### 1.1 Frontend Location & Build Output
* **Frontend Location**: The Next.js frontend code is located in the `frontend/` directory of the workspace root.
* **Build Command**: The build process is defined in `frontend/package.json` under `"build": "node node_modules/next/dist/bin/next build --webpack"`.
* **Export Strategy**: In `frontend/next.config.ts`, static HTML export is enabled via the parameter `output: "export"`. When `npm run build` is executed, Next.js compiles the entire application into static HTML, CSS, and JS assets located in `frontend/out/`.

### 1.2 Routing & Proxy/Redirect Configurations
Since Next.js is configured for static export (`output: "export"`), dynamic routing features (like rewrite rules or API proxies) cannot rely on Next.js server-side middlewares or standard Node.js server configurations.
* **Programmatic Routing (`_worker.js`)**: The application uses a custom Cloudflare Pages Worker router located at `cloudflare/pages/_worker.js`. This worker intercepts all pages requests:
  - It proxies routes defined in `PROXY_PATHS = ['/api/', '/_/pa/', '/scrape', '/health']` directly to the edge worker API (`WORKER_URL = 'https://jobhunt-pro-router.samsalameh-cv.workers.dev'`).
  - It serves static frontend assets directly from Cloudflare's edge cache via `env.ASSETS.fetch(request)`.
* **Static Redirect File (`_redirects`)**: To add custom redirects, a `_redirects` file can be placed at the root of the compiled output (`frontend/out/_redirects`). The best practice is to place this file inside `frontend/public/_redirects`. Next.js automatically copies everything in `public/` to the build output `out/` folder during compilation, ensuring custom redirects persist across deployments.

### 1.3 Backend CORS Configurations & Cloudflare Pages Integration
CORS is dynamically managed in the backend to ensure secure API requests:
* **CORS Settings Location**: Configured in `backend/main.py` (lines 294-320).
* **Allowed Origins**: Loaded from the environment variable `ALLOWED_ORIGINS` via:
  ```python
  allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
  if allowed_origins_env:
      origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
  ```
  If `ALLOWED_ORIGINS` is not defined in the environment, it defaults to localhost urls (`http://localhost:3000`, `http://localhost:5173`, `http://localhost:8000`).
* **Subdomain Validation**: `backend/main.py` uses `SecureCORSMiddleware` (lines 247-290) and `_build_origin_regex` to support wildcard subdomains (e.g., `https://*.pages.dev`).
* **Update for Cloudflare Pages**: To authorize the production Pages site and its preview deployments, set the backend environment variable:
  ```env
  ALLOWED_ORIGINS=https://jobhunt-pro-frontend.pages.dev,https://*.pages.dev
  ```

---

## 2. GitHub Actions Scheduled Keep-Alive (Milestone 2)

### 2.1 Workflow Audit
The `.github/workflows/` folder contains two active keepalive actions: `keep-alive.yml` and `keep_alive.yml`. Both are configured on a `*/10 * * * *` schedule, but only ping the standard `/health` or `/api/v1/health` HTTP endpoints.

### 2.2 Uptime & Database Warmup Workflow Design
Render's free web service instances spin down after 15 minutes of inactivity. Neon serverless databases auto-suspend after 5 minutes of idle time. To keep both active with zero cold-starts, the keepalive must run at least every 12 minutes and ping both the backend and query the database.
* **Database Warming Strategy**: Pinging `/healthz` only verifies FastAPI's status and does not query the database. Pinging the detailed health endpoint `/api/v1/health/detailed` triggers an active SQLAlchemy database query (`SELECT 1`), keeping Neon warm. Alternatively, the local script `core/neon_warmer.py` can be executed directly by the workflow.

### 2.3 Proposed Workflow: `.github/workflows/keep_alive_optimized.yml`
```yaml
name: ⚡ Render Backend & Neon DB Keep-Alive

on:
  schedule:
    - cron: "*/12 * * * *" # Runs every 12 minutes to prevent Render (15m) & Neon (5m) sleeps
  workflow_dispatch:      # Allows manual trigger in GitHub UI

jobs:
  keep-alive:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install DB Dependencies
        run: |
          pip install psycopg2-binary

      - name: Ping Render Backend /healthz
        env:
          RENDER_APP_URL: ${{ secrets.RENDER_APP_URL }}
        run: |
          TARGET_URL="${RENDER_APP_URL:-https://jobhunt-pro.onrender.com}"
          echo "Pinging Render healthz: $TARGET_URL/healthz"
          curl -sS --fail --retry 3 --max-time 15 "$TARGET_URL/healthz"

      - name: Run Neon DB Warming Script
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          if [ -z "$DATABASE_URL" ]; then
            echo "DATABASE_URL secret is missing. Skipping local DB warming script."
          else
            echo "Running local Neon DB warming script..."
            python core/neon_warmer.py
          fi

      - name: Ping Detailed Health Endpoint (Alternative/Fallback DB Warmer)
        env:
          RENDER_APP_URL: ${{ secrets.RENDER_APP_URL }}
        run: |
          TARGET_URL="${RENDER_APP_URL:-https://jobhunt-pro.onrender.com}"
          echo "Pinging detailed health endpoint to warm DB: $TARGET_URL/api/v1/health/detailed"
          curl -sS --fail --retry 3 --max-time 15 "$TARGET_URL/api/v1/health/detailed"
```

---

## 3. Celery Memory Guard (Milestone 3)

### 3.1 Worker Spawning Analysis
In `start_cloud.py` (lines 113-132), the Celery worker is spawned inside a subprocess:
```python
        celery_cmd = [sys.executable, "-m", "celery", "-A", "backend.tasks", "worker", "--loglevel=info"]
        if os.name == "nt":
            celery_cmd.extend(["-P", "solo"])
        else:
            celery_cmd.extend(["-c", "1"])
```
* **Windows vs Linux Pool**: On Windows (`os.name == "nt"`), Celery must run with the `solo` pool (`-P solo`) to avoid multi-processing compatibility issues. On Linux (Render), it runs with the default `prefork` pool and concurrency 1 (`-c 1`).
* **Command Option Compatibility**: Celery's process recycling flags (`--max-tasks-per-child` and `--max-memory-per-child`) only apply to pools that manage child worker processes (like `prefork`). If passed to a `solo` pool, they are ignored since tasks execute within the master process itself. Thus, we must append these parameters to the command list, ensuring they are functional in production (Linux).

### 3.2 Proposed Modifications for `start_cloud.py`
We modify the `celery_cmd` initialization in `start_cloud.py` to inject the limits before checking for platform-specific arguments:
```python
        # Base Celery Command with memory limits (150000 KB = 150 MB)
        celery_cmd = [
            sys.executable, "-m", "celery", 
            "-A", "backend.tasks", 
            "worker", 
            "--loglevel=info",
            "--max-tasks-per-child=10",
            "--max-memory-per-child=150000"
        ]
        if os.name == "nt":
            # On Windows, use solo pool (recycling limits have no effect but CLI arguments parse fine)
            celery_cmd.extend(["-P", "solo"])
        else:
            # On Linux (Render), omit -P solo and use concurrency=1 to allow worker process recycling
            celery_cmd.extend(["-c", "1"])
```

---

## 4. Neon PgBouncer Connection String Updates (Milestone 4)

### 4.1 Neon PgBouncer & transaction pooling limits
Neon database connections can use a PgBouncer connection pooler (indicated by `-pooler` in the hostname) to handle high concurrency. 
* **Prepared Statement Conflict**: PgBouncer transaction-mode poolers route consecutive queries to different database sessions. Since SQLAlchemy's `asyncpg` driver uses prepared statements by default (stored in session memory), PgBouncer transaction pooling will cause errors (e.g., `prepared statement "..." does not exist`).
* **Mitigation**: Disabling prepared statements is mandatory. For `asyncpg` and SQLAlchemy, this is done by setting `statement_cache_size=0` and `prepared_statement_cache_size=0` in connection parameters, rather than passing raw JDBC parameters like `prepareThreshold` directly to the `asyncpg` driver, which raises a `ValueError`.

### 4.2 Proposed Strategy for `backend/database.py`
We will rewrite `REMOTE_PG_URL` during initialization to target the Neon pooler (subdomain suffix `-pooler`), target port `5432`, and append `?sslmode=require&prepareThreshold=0` (ensuring JDBC/external compliance). Then, we strip these parameters before passing the URL to `create_async_engine()`, handling them cleanly via `connect_args`.

#### Before (`backend/database.py` lines 27-46):
```python
REMOTE_PG_URL    = os.getenv("DATABASE_URL")             # kept for legacy / Postgres path

def _build_active_url() -> str:
    """Return the resolved async database URL at startup, logging the active backend."""
    if TURSO_URL:
        # libsql+aiosqlite over HTTPS — aiosqlite supports the libsql URL scheme
        # when the libsql-experimental package is installed.
        url = TURSO_URL.replace("libsql://", "sqlite+aiosqlite://")
        _db_logger.info('{"msg": "Connecting to Turso edge database", "url": "%s"}', TURSO_URL)
        return url
    if REMOTE_PG_URL:
        _db_logger.info('{"msg": "Connecting to remote PostgreSQL"}')
        url = REMOTE_PG_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://")
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://")
        return url
    _db_logger.info('{"msg": "Using local SQLite fallback", "url": "%s"}', LOCAL_DB_URL)
    return LOCAL_DB_URL
```

#### Proposed Change (`backend/database.py`):
```python
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def configure_pg_bouncer_url(url: str) -> str:
    """Rewrite PG URL to target Neon PgBouncer pooler on port 5432 with standard parameters."""
    if not url or "postgres" not in url:
        return url
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc
        auth = ""
        host_port = netloc
        if "@" in netloc:
            auth, host_port = netloc.split("@", 1)
            auth += "@"
            
        host = host_port
        if ":" in host_port:
            host, _ = host_port.split(":", 1)
            
        # Target Neon Pooler (e.g. ep-some-name-pooler.us-east-2.aws.neon.tech)
        if "neon.tech" in host:
            parts = host.split(".")
            if parts and not parts[0].endswith("-pooler"):
                parts[0] = f"{parts[0]}-pooler"
                host = ".".join(parts)
                
        # Force PgBouncer port 5432
        new_netloc = f"{auth}{host}:5432"
        
        # Append query params for JDBC/custom parser compatibility
        query_params = dict(parse_qsl(parsed.query))
        query_params["sslmode"] = "require"
        query_params["prepareThreshold"] = "0"
        new_query = urlencode(query_params)
        
        return urlunparse(parsed._replace(netloc=new_netloc, query=new_query))
    except Exception as e:
        _db_logger.error(f"Error compiling PgBouncer connection string: {e}")
        return url

# Load and rewrite raw database URL
RAW_DATABASE_URL = os.getenv("DATABASE_URL")
REMOTE_PG_URL = configure_pg_bouncer_url(RAW_DATABASE_URL) if RAW_DATABASE_URL else None

def _build_active_url() -> str:
    """Return the resolved async database URL at startup, logging the active backend."""
    if TURSO_URL:
        url = TURSO_URL.replace("libsql://", "sqlite+aiosqlite://")
        _db_logger.info('{"msg": "Connecting to Turso edge database", "url": "%s"}', TURSO_URL)
        return url
    if REMOTE_PG_URL:
        _db_logger.info('{"msg": "Connecting to remote PostgreSQL", "url": "%s"}', REMOTE_PG_URL)
        url = REMOTE_PG_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url
    _db_logger.info('{"msg": "Using local SQLite fallback", "url": "%s"}', LOCAL_DB_URL)
    return LOCAL_DB_URL
```

And update the post-processing of `ACTIVE_DB_URL` in `backend/database.py` (lines 77-86) to strip custom parameters and inject them via `connect_args`:
```python
    # Configure connect args safely
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }
    
    if "sslmode" in ACTIVE_DB_URL or "ssl" in ACTIVE_DB_URL:
        connect_args["ssl"] = True
        
    # Strip any query parameters from ACTIVE_DB_URL before passing it to create_async_engine
    if "?" in ACTIVE_DB_URL:
        base_url, _ = ACTIVE_DB_URL.split("?", 1)
        ACTIVE_DB_URL = base_url
        
    engine_kwargs["connect_args"] = connect_args
```

### 4.3 Proposed Strategy for `backend/sync_worker.py`
In `backend/sync_worker.py`, the worker establishes a connection to Neon via raw `asyncpg.connect()`:
```python
            # Strip async+asyncpg scheme for raw asyncpg connection
            raw_pg_url = REMOTE_PG_URL.replace("postgresql+asyncpg://", "postgresql://") if REMOTE_PG_URL else None
```
Because raw `asyncpg` does not recognize `prepareThreshold`, passing it in `raw_pg_url` causes a `ValueError`.
We must strip the query parameters from `raw_pg_url` and pass `ssl="require"` and `statement_cache_size=0` explicitly to `asyncpg.connect()`.

#### Proposed Change (`backend/sync_worker.py` lines 143-146):
```python
                # Reuse connection if active, otherwise reconnect
                if not cloud_conn or cloud_conn.is_closed():
                    logger.info("[SyncWorker] Re-establishing remote DB connection...")
                    # Strip URL parameters to avoid asyncpg parser ValueError
                    clean_pg_url = raw_pg_url.split("?")[0]
                    cloud_conn = await asyncpg.connect(
                        clean_pg_url, 
                        ssl="require", 
                        statement_cache_size=0
                    )
```

---

## 5. Free Proxy Pool Scraper Rotation (Milestone 5)

### 5.1 Scraper Architecture & Performance Audit
In `core/ghost_hunter.py`, `GhostHunter.hunt_for_user()` performs public job scraping on LinkedIn via a single `Camoufox` browser context:
```python
            from camoufox.sync_api import Camoufox

            with Camoufox(headless=True) as browser:
                page = browser.new_page()
                for url in urls:
```
* **Performance Leak**: The DB duplicate check happens inside the loop, *after* the browser is spawned. If all scraped URLs are duplicates, launching the browser wasted substantial memory and boot time.
* **Stealth and IP Rotation**: Using a single IP address (direct connection) to fetch multiple job descriptions on LinkedIn is highly susceptible to rate-limiting and IP bans.

### 5.2 Implementation of `ProxyManager`
We design a `ProxyManager` to scrape free proxies hourly and cache them in `cache/proxy_pool.json`. To prevent fingerprint tracking and enable complete IP rotation, `Camoufox` must be instantiated per URL, utilizing a different proxy.

#### Proposed Proxy Integration code in `core/ghost_hunter.py`:
```python
import os
import json
import re
import requests
from bs4 import BeautifulSoup

class ProxyManager:
    """Manages hourly scraping, caching, and rotation of free proxies."""
    CACHE_FILE = "cache/proxy_pool.json"

    def __init__(self):
        os.makedirs(os.path.dirname(self.CACHE_FILE), exist_ok=True)
        self.proxies = []
        self.load_proxies()

    def load_proxies(self):
        """Loads cached proxies or scrapes new ones if the cache is stale (>1 hour)."""
        now = time.time()
        stale = True
        
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if now - data.get("timestamp", 0) < 3600:
                        self.proxies = data.get("proxies", [])
                        if self.proxies:
                            stale = False
                            logger.info(f"[PROXY-POOL] Loaded {len(self.proxies)} proxies from cache.")
            except Exception as e:
                logger.error(f"[PROXY-POOL] Error reading proxy cache: {e}")
                
        if stale:
            logger.info("[PROXY-POOL] Cache is stale or empty. Scraping new proxies...")
            self.scrape_and_save()

    def scrape_and_save(self):
        """Scrape free proxies from free-proxy-list.net and sslproxies.org."""
        self.proxies = []
        sources = [
            "https://free-proxy-list.net/",
            "https://www.sslproxies.org/"
        ]
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        for url in sources:
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    table = soup.find("table", class_="table-striped")
                    if table:
                        tbody = table.find("tbody")
                        if tbody:
                            for row in tbody.find_all("tr"):
                                cols = row.find_all("td")
                                if len(cols) >= 2:
                                    ip = cols[0].text.strip()
                                    port = cols[1].text.strip()
                                    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                                        self.proxies.append(f"{ip}:{port}")
            except Exception as e:
                logger.error(f"[PROXY-POOL] Error scraping {url}: {e}")
                
        self.proxies = list(set(self.proxies))
        
        if self.proxies:
            logger.info(f"[PROXY-POOL] Successfully scraped {len(self.proxies)} unique proxies.")
            try:
                with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"timestamp": time.time(), "proxies": self.proxies}, f)
            except Exception as e:
                logger.error(f"[PROXY-POOL] Error saving proxy cache: {e}")
        else:
            logger.warning("[PROXY-POOL] Scraped 0 proxies. Keeping old proxies as fallback.")

    def get_proxy(self) -> str | None:
        """Retrieve a random proxy from the active pool."""
        if not self.proxies:
            self.load_proxies()
        if self.proxies:
            return random.choice(self.proxies)
        return None

    def mark_failed(self, proxy: str):
        """Remove a failed proxy from the pool and update cache."""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.info(f"[PROXY-POOL] Removed failed proxy: {proxy}. Remaining: {len(self.proxies)}")
            try:
                if os.path.exists(self.CACHE_FILE):
                    with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    data["proxies"] = self.proxies
                    with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(data, f)
            except Exception as e:
                logger.error(f"[PROXY-POOL] Error updating proxy cache: {e}")
```

#### Proposed Changes in `GhostHunter.hunt_for_user()`:
We rewrite the Camoufox loop in `core/ghost_hunter.py` (lines 65-139) to incorporate:
1. **Lazy DB Validation**: Validate duplicates before spawning the heavy browser process.
2. **IP Rotation per Request**: Recreate the browser with a proxy selected from `ProxyManager`.
3. **Automatic Bad Proxy Eviction**: Catch connection errors and mark the bad proxy.

```python
        # For Camoufox, we run it synchronously since it's blocking
        try:
            from camoufox.sync_api import Camoufox
            proxy_mgr = ProxyManager()

            for url in urls:
                # 1. OPTIMIZATION: Check if job already exists before launching browser
                conn = _get_db()
                existing = conn.execute(
                    "SELECT 1 FROM jobs WHERE user_id = ? AND url = ?",
                    (user_id, url),
                ).fetchone()
                conn.close()
                if existing:
                    logger.info(f"[DATASET-FETCHER] Duplicate job found — skipping: {url}")
                    continue

                # 2. Retrieve proxy and construct configuration
                proxy = proxy_mgr.get_proxy()
                proxy_config = {"server": f"http://{proxy}"} if proxy else None
                logger.info(f"[DATASET-FETCHER] Launching Camoufox with proxy: {proxy or 'Direct Connection'}")

                try:
                    # 3. Launch fresh browser context for IP rotation
                    with Camoufox(headless=True, proxy=proxy_config) as browser:
                        page = browser.new_page()
                        logger.info(f"[DATASET-FETCHER] Fetching page: {url}")
                        page.goto(url, timeout=30000)
                        time.sleep(random.uniform(2, 4))  # Human delay
                        html = page.content()

                        soup = BeautifulSoup(html, "html.parser")
                        title_elem = soup.find("h1")
                        title = title_elem.text.strip() if title_elem else "Unknown Title"

                        company_elem = soup.find("a", {"class": "topcard__org-name-link"})
                        company = company_elem.text.strip() if company_elem else "Unknown Company"

                        desc_elem = soup.find("div", {"class": "description__text"})
                        desc = desc_elem.text.strip() if desc_elem else ""

                        if len(desc) > 50:
                            job_id = f"gh_{int(time.time())}_{random.randint(1000, 9999)}"
                            conn = _get_db()
                            conn.execute(
                                """
                                INSERT INTO jobs (job_id, user_id, title, company, description, url, source, status)
                                VALUES (?, ?, ?, ?, ?, ?, 'ghost_hunter', 'new')
                                """,
                                (job_id, user_id, title, company, desc, url),
                            )
                            if hasattr(conn, "commit"):
                                conn.commit()
                            conn.close()
                            logger.info(f"[DATASET-FETCHER] Ingested sample: {title} at {company}")

                        # ANTI-BAN JITTER: Randomized delay from 15 to 35 seconds
                        jitter = random.uniform(15, 35)
                        logger.info(f"[DATASET-FETCHER] Applying network backoff ({jitter:.1f}s)")
                        time.sleep(jitter)

                except Exception as e:
                    logger.error(f"[DATASET-FETCHER] Error processing {url} with proxy {proxy}: {e}")
                    if proxy:
                        proxy_mgr.mark_failed(proxy)
                    # Optional: We could re-queue or retry here with a different proxy

        except ImportError:
            logger.error("[DATASET-FETCHER] Headless dependency not installed.")
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] Runtime Error: {e}")
```
