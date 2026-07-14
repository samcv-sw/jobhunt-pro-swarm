# Codebase Analysis Report: Deployment & Optimization Milestones

This analysis report provides detailed blueprints for Cloudflare Pages Next.js deployment, GitHub Actions keep-alive workflows, Celery memory configuration, Neon PgBouncer connection tuning, and Free Proxy Pool scraping and rotation.

---

## 1. Cloudflare Pages Next.js Deployment

### A. Frontend Location and Build Pipeline
- **Code Location**: The Next.js frontend code is located in the `frontend/` directory.
- **Dependencies**: Configured in `frontend/package.json`, which specifies Next.js `16.2.9` and React `19.2.4`.
- **Build Command**: The build script in `frontend/package.json` runs:
  ```bash
  npm run build
  # Executes: node node_modules/next/dist/bin/next build --webpack
  ```
- **Export Mode**: In `frontend/next.config.ts`, Next.js is configured for static exports:
  ```typescript
  output: "export",
  trailingSlash: true,
  ```
  When `npm run build` is executed, Next.js generates static HTML, CSS, and JS files in the `frontend/out/` directory.

### B. Custom Redirects and Headers
For Cloudflare Pages static deployments:
- **Proxy/Redirects Configuration**: Define routing and redirect rules in a `_redirects` file.
- **Custom Headers**: Define response headers (like Security Headers) in a `_headers` file.
- **Implementation**: Since the build output is fully static, these files must be located in the root of the deployed output. The best practice is to place them in `frontend/public/_redirects` and `frontend/public/_headers`. Next.js automatically copies any files in the `public/` directory into the `out/` build directory during compilation.

### C. Backend CORS Settings
- **Location**: In `backend/main.py`, CORS is configured around line 294.
- **Allowed Origins Source**: Loaded dynamically from the environment variable:
  ```python
  allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
  ```
- **Wildcard Subdomains**: If wildcard subdomains (such as `https://*.pages.dev`) are defined, the backend switches to `SecureCORSMiddleware` (lines 247-290). This custom middleware matches origins dynamically using:
  ```python
  re.compile(f"^{re.escape(pattern).replace(re.escape('*'), '[a-zA-Z0-9-]+')}$")
  ```
- **Fallback / Local Dev**: If `ALLOWED_ORIGINS` is not defined in the environment, the backend defaults to:
  ```python
  origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]
  ```
  And if `ENV` is not set to `production`, it falls back to a permissive Starlette `CORSMiddleware`.
- **CORS in Web Module**: In `web/app_v2.py` (lines 836-851), Starlette `CORSMiddleware` is configured to allow `https?://.*\.pages\.dev` and `https?://.*\.koyeb\.app` by default via:
  ```python
  allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|chrome-extension://.*|https?://.*\.pages\.dev|https?://.*\.koyeb\.app"
  ```
- **Updating for Cloudflare Pages**: To allow access from custom Cloudflare Pages domains or wildcard previews:
  1. Set the `ALLOWED_ORIGINS` environment variable on the backend host (e.g. Render, Koyeb, or Docker runtime environment).
  2. For wildcard preview pages, include: `https://*.pages.dev`
  3. For custom domains, include the full domain, e.g., `https://my-custom-app.com`.
  4. Separate multiple origins using a comma (`,`).

---

## 2. GitHub Actions Scheduled Keep-Alive

### A. Existing Workflows
Inside `.github/workflows/`, there are two existing keepalive workflows:
1. `keep-alive.yml`: Pings `RENDER_APP_URL` or `https://jobhunt-pro.onrender.com/health` and `https://jobhunt-pro-swarm.onrender.com/health` every 10 minutes.
2. `keep_alive.yml`: Pings `SITE_URL` / `RENDER_EXTERNAL_URL` / `https://jobhunt-pro.onrender.com/api/v1/health` every 10 minutes.

### B. Proposed Keep-Alive Workflow Design
To meet the requirement of keeping both the Render backend awake and warming the Neon DB every 12 minutes, the following GitHub Actions keepalive workflow is designed:

```yaml
name: ⚡ Render & Neon Keep-Alive

on:
  schedule:
    - cron: "*/12 * * * *" # Runs exactly every 12 minutes
  workflow_dispatch: # Allows manual triggering from GitHub UI

jobs:
  keep_alive:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Codebase
        uses: actions/checkout@v4

      - name: Setup Python environment
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install psycopg2-binary

      - name: Ping Render Backend /healthz
        env:
          RENDER_BACKEND_URL: ${{ secrets.RENDER_BACKEND_URL }}
        run: |
          # Fallback to default engine URL if secret is not set
          TARGET_URL="${RENDER_BACKEND_URL:-https://jobhunt-pro-engine.onrender.com}"
          echo "Pinging Render /healthz endpoint at: $TARGET_URL/healthz"
          curl -f -sS --retry 3 --max-time 15 "$TARGET_URL/healthz" || echo "Backend ping failed but continuing..."

      - name: Warm Neon Database (via Python Script)
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          if [ -z "$DATABASE_URL" ]; then
            echo "DATABASE_URL secret is missing. Attempting backend warm-up fallback..."
            # Fallback: Ping the backend's detailed health endpoint which queries the database
            TARGET_URL="${RENDER_BACKEND_URL:-https://jobhunt-pro-engine.onrender.com}"
            curl -f -sS --retry 3 --max-time 15 "$TARGET_URL/api/v1/health/detailed" || echo "Database detailed endpoint ping failed."
          else
            echo "Running core/neon_warmer.py..."
            python core/neon_warmer.py
          fi
```

### C. Analysis of the Warming Mechanism
- The `core/neon_warmer.py` script requires `DATABASE_URL` to connect to Neon DB and execute `SELECT 1`.
- Alternatively, pinging the backend's detailed health check endpoint (`/api/v1/health/detailed` defined in `backend/main.py` line 408) connects to the database via SQLAlchemy and executes `SELECT 1`, effectively warming the serverless Neon instance without requiring the database credentials to be stored as a GitHub Actions secret.

---

## 3. Celery Memory Guard

### A. Spawn Mechanism
In `start_cloud.py`, Celery is spawned as a subprocess within the `launch_services()` function (lines 114-129):
```python
    if os.environ.get("REDIS_URL"):
        logger.info("Starting Celery Worker...")
        celery_cmd = [sys.executable, "-m", "celery", "-A", "backend.tasks", "worker", "--loglevel=info"]
        if os.name == "nt":
            # On Windows, use solo pool to avoid multiprocessing issues
            celery_cmd.extend(["-P", "solo"])
        else:
            # On Linux (Render), omit -P solo and use concurrency=1 to allow worker process recycling
            celery_cmd.extend(["-c", "1"])
        
        celery_proc = subprocess.Popen(celery_cmd)
```

### B. Command Modification
To enforce process recycling limits at the command-line level, the list `celery_cmd` should be updated to append `--max-tasks-per-child=10` and `--max-memory-per-child=150000`:
```python
        celery_cmd = [
            sys.executable, "-m", "celery", 
            "-A", "backend.tasks", 
            "worker", 
            "--loglevel=info",
            "--max-tasks-per-child=10",
            "--max-memory-per-child=150000"
        ]
```

### C. Execution Considerations
1. **Windows vs. Linux Pools**:
   - On Windows (`os.name == "nt"`), `start_cloud.py` appends `["-P", "solo"]` to the command line. The `solo` pool executes Celery tasks in-process. Since no child worker processes are spawned under the solo pool, these parameters have no effect.
   - On Linux/Render, the worker is spawned without `-P solo` and with `-c 1` (concurrency level of 1), enabling the `prefork` pool. In this pool, the child processes will successfully recycle upon reaching either limit (10 tasks executed or RSS memory exceeding 150MB/150,000KB).
2. **Double Configuration**:
   The memory limits are already programmatically declared inside the celery application configuration (`backend/celery_app.py` lines 31-32):
   ```python
   worker_max_tasks_per_child=10,            # Recycle child worker after 10 tasks to reclaim memory
   worker_max_memory_per_child=150000,       # Recycle child worker if RSS exceeds 150MB (in KB)
   ```
   Adding these to `start_cloud.py` reinforces the configuration at the launcher command-line level.

---

## 4. Neon PgBouncer Connection String Updates

### A. Database Configuration in `backend/database.py`
The database URL is resolved at startup inside `_build_active_url()` (lines 29-47) of `backend/database.py`:
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

### B. Proposed Changes for PgBouncer & Port 5432
To support PgBouncer transaction pooling in Neon, we must append `sslmode=require` and `prepareThreshold=0` (disabling prepared statement caching which breaks under transaction poolers), change the port to `5432`, and ensure the host redirects to the Neon pooler endpoint (usually containing `-pooler` in its hostname).

Below is the proposed Python logic to apply inside `_build_active_url()`:

```python
    if REMOTE_PG_URL:
        _db_logger.info('{"msg": "Connecting to remote PostgreSQL"}')
        url = REMOTE_PG_URL
        
        # 1. Adapt scheme for asyncpg
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            
        # 2. Modify URL hostname, port, and query arguments for Neon PgBouncer poolers
        from urllib.parse import urlparse, urlunparse
        try:
            parsed = urlparse(url)
            # Only apply modifications to neon.tech hosts
            if "neon.tech" in parsed.netloc:
                netloc = parsed.netloc
                auth_part = ""
                host_port = netloc
                if "@" in netloc:
                    auth_part, host_port = netloc.split("@", 1)
                    auth_part += "@"
                
                host = host_port
                if ":" in host_port:
                    host, _ = host_port.split(":", 1)
                
                # Append -pooler to host if not already present
                if not host.endswith("-pooler"):
                    host_parts = host.split(".", 1)
                    if host_parts and not host_parts[0].endswith("-pooler"):
                        host_parts[0] = f"{host_parts[0]}-pooler"
                    host = ".".join(host_parts)
                
                # Force target port 5432
                new_netloc = f"{auth_part}{host}:5432"
                
                # Parse existing query parameters and inject connection parameters
                query = parsed.query
                params = {}
                if query:
                    for item in query.split("&"):
                        if "=" in item:
                            k, v = item.split("=", 1)
                            params[k] = v
                
                params["sslmode"] = "require"
                params["prepareThreshold"] = "0"
                new_query = "&".join(f"{k}={v}" for k, v in params.items())
                
                url = urlunparse(parsed._replace(netloc=new_netloc, query=new_query))
        except Exception as e:
            _db_logger.error(f"Failed parsing database connection string for Neon pooler: {e}")
            
        return url
```

### C. Alignment with `backend/sync_worker.py`
- In `backend/sync_worker.py` (line 23), the raw string is imported directly from `database.py`:
  ```python
  from .database import REMOTE_PG_URL, async_session
  ```
- It uses a string replacement to prepare a DSN for raw `asyncpg`:
  ```python
  raw_pg_url = REMOTE_PG_URL.replace("postgresql+asyncpg://", "postgresql://") if REMOTE_PG_URL else None
  ```
- Since `REMOTE_PG_URL` is imported, if we define the PgBouncer configuration inside `database.py` and assign it to `REMOTE_PG_URL`, `sync_worker.py` automatically inherits the updated, pooled connection string. The parameters `sslmode=require` and `prepareThreshold=0` will be correctly parsed by `asyncpg.connect(raw_pg_url)`.

---

## 5. Free Proxy Pool Scraper Rotation

### A. Current Class Structure in `core/ghost_hunter.py`
`GhostHunter` is currently defined in `core/ghost_hunter.py` as an autonomous web scraper using DDG Search API (`duckduckgo_search`) to locate LinkedIn URLs, and Camoufox (Playwright stealth extension) to extract job details.
- Currently, Camoufox is started synchronously:
  ```python
  from camoufox.sync_api import Camoufox
  with Camoufox(headless=True) as browser:
      page = browser.new_page()
      # page.goto() is executed here inside a loops over URLs
  ```
  No proxy configurations are passed, making the scraper vulnerable to IP bans by LinkedIn when scraping multiple jobs.

### B. Scraping and Rotation Strategy
To protect the scraper, we can implement an hourly free proxy scraper and cache system directly inside `ghost_hunter.py`.

#### Step 1: Proxy Scraper & Cache Implementation
Add the following functions to `core/ghost_hunter.py` (or load them from a proxy utility helper):

```python
import os
import json
import urllib.request
import re

PROXY_CACHE_FILE = "data/proxy_cache.json"

def scrape_free_proxies() -> list[str]:
    """Fetch free public HTTP/HTTPS proxies from free-proxy-list.net."""
    proxies = []
    try:
        url = "https://www.free-proxy-list.net/"
        req = urllib.request.Request(
            url, 
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode("utf-8")
        
        soup = BeautifulSoup(html, "html.parser")
        textarea = soup.find("textarea")
        if textarea:
            text = textarea.text.strip()
            for line in text.split("\n"):
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$", line.strip()):
                    proxies.append(line.strip())
        else:
            table = soup.find("table", {"class": "table-striped"})
            if table:
                for row in table.find_all("tr")[1:]:
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip) and port.isdigit():
                            proxies.append(f"{ip}:{port}")
    except Exception as e:
        logger.error(f"[PROXY-SCRAPER] Failed to fetch proxies: {e}")
    return proxies


def get_rotated_proxy() -> str | None:
    """Read proxies from local cache. Scrapes new proxies if cache is older than 1 hour."""
    now = time.time()
    cache_valid = False
    proxies = []

    if os.path.exists(PROXY_CACHE_FILE):
        try:
            with open(PROXY_CACHE_FILE, "r") as f:
                data = json.load(f)
                # Check 1-hour cache TTL (3600 seconds)
                if now - data.get("timestamp", 0) < 3600:
                    proxies = data.get("proxies", [])
                    if proxies:
                        cache_valid = True
        except Exception:
            pass

    if not cache_valid:
        logger.info("[PROXY-ROTATION] Proxy cache expired or missing. Initializing scrape...")
        proxies = scrape_free_proxies()
        if proxies:
            try:
                os.makedirs(os.path.dirname(PROXY_CACHE_FILE), exist_ok=True)
                with open(PROXY_CACHE_FILE, "w") as f:
                    json.dump({"timestamp": now, "proxies": proxies}, f)
                logger.info(f"[PROXY-ROTATION] Cached {len(proxies)} proxies.")
            except Exception as e:
                logger.error(f"[PROXY-ROTATION] Failed to write cache: {e}")

    if not proxies:
        return None
    return random.choice(proxies)
```

#### Step 2: Camoufox Integration with Resilient Failover
Camoufox accepts proxy configurations at launch time. Since we cannot switch proxies on a running browser context dynamically without re-creating the browser, the browser context should be managed with an exception handler. If a proxy fails, a new proxy is retrieved, and the browser is re-initialized:

```python
        # In GhostHunter.hunt_for_user:
        try:
            from camoufox.sync_api import Camoufox
            
            # Select proxy and configure launcher
            proxy = get_rotated_proxy()
            proxy_settings = {"server": f"http://{proxy}"} if proxy else None
            
            browser = None
            try:
                logger.info(f"[DATASET-FETCHER] Initializing Camoufox with proxy: {proxy}")
                browser = Camoufox(headless=True, proxy=proxy_settings)
                browser.__enter__()
                page = browser.new_page()
                
                for url in urls:
                    try:
                        # Check DB for duplicate job urls
                        conn = _get_db()
                        existing = conn.execute(
                            "SELECT 1 FROM jobs WHERE user_id = ? AND url = ?",
                            (user_id, url),
                        ).fetchone()
                        if existing:
                            conn.close()
                            continue

                        logger.info(f"[DATASET-FETCHER] Fetching page: {url}")
                        try:
                            page.goto(url, timeout=30000)
                        except Exception as page_err:
                            logger.error(f"[DATASET-FETCHER] Navigation failed: {page_err}")
                            # Proxy error detection (connection failures, timeouts, etc.)
                            if any(err in str(page_err) for err in ["ERR_PROXY_CONNECTION_FAILED", "ERR_CONNECTION_RESET", "Timeout"]):
                                logger.warning("[DATASET-FETCHER] Proxy connection failed. Rotating proxy...")
                                # Close current browser
                                page = None
                                if browser:
                                    try:
                                        browser.__exit__(None, None, None)
                                    except Exception:
                                        pass
                                
                                # Pick a new proxy and restart Camoufox
                                proxy = get_rotated_proxy()
                                proxy_settings = {"server": f"http://{proxy}"} if proxy else None
                                browser = Camoufox(headless=True, proxy=proxy_settings)
                                browser.__enter__()
                                page = browser.new_page()
                                
                                # Retry page navigation once with the new proxy
                                logger.info(f"[DATASET-FETCHER] Retrying page navigation with new proxy: {proxy}")
                                page.goto(url, timeout=30000)
                            else:
                                conn.close()
                                raise page_err

                        time.sleep(random.uniform(2, 4))  # Human jitter
                        html = page.content()
                        
                        # Ingestion logic...
                        soup = BeautifulSoup(html, "html.parser")
                        title_elem = soup.find("h1")
                        title = title_elem.text.strip() if title_elem else "Unknown Title"
                        
                        company_elem = soup.find("a", {"class": "topcard__org-name-link"})
                        company = company_elem.text.strip() if company_elem else "Unknown Company"
                        
                        desc_elem = soup.find("div", {"class": "description__text"})
                        desc = desc_elem.text.strip() if desc_elem else ""

                        if len(desc) > 50:
                            job_id = f"gh_{int(time.time())}_{random.randint(1000, 9999)}"
                            conn.execute(
                                """
                                INSERT INTO jobs (job_id, user_id, title, company, description, url, source, status)
                                VALUES (?, ?, ?, ?, ?, ?, 'ghost_hunter', 'new')
                            """,
                                (job_id, user_id, title, company, desc, url),
                            )
                            if hasattr(conn, "commit"):
                                conn.commit()
                            logger.info(f"[DATASET-FETCHER] Ingested sample: {title} at {company}")

                        conn.close()

                        # Anti-ban backoff delay
                        jitter = random.uniform(15, 35)
                        logger.info(f"[DATASET-FETCHER] Applying network backoff ({jitter:.1f}s)")
                        time.sleep(jitter)

                    except Exception as e:
                        logger.error(f"[DATASET-FETCHER] Error processing {url}: {e}")
            finally:
                if browser:
                    try:
                        browser.__exit__(None, None, None)
                    except Exception:
                        pass
        except ImportError:
            logger.error("[DATASET-FETCHER] Headless dependency not installed.")
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] Runtime Error: {e}")
```

This ensures `GhostHunter` is resilient, rotating proxies dynamically without restarting the whole worker process.
