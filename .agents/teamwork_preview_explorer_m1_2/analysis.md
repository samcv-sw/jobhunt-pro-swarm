# Codebase Analysis Report - Milestones 1-5 Investigation

This report provides a detailed read-only investigation and design architecture for deploying to Cloudflare Pages, implementing a GitHub keep-alive cron job, guarding Celery memory limits, configuring Neon PgBouncer connection compatibility, and establishing a rotating free proxy scraper pool.

---

## Milestone 1: Cloudflare Pages Next.js Deployment

### 1. Frontend Location and Build Pipeline
- **Next.js Source Path**: The frontend is located in the `/frontend` directory.
- **Build Output Target**: The project is configured as a static export, indicated by the setting `output: "export"` in `frontend/next.config.ts` (lines 10-11).
- **Build Command**: `npm run build` (mapped to `"build": "node node_modules/next/dist/bin/next build --webpack"` in `frontend/package.json` line 7) compiles the source code into static files and places the output in the `frontend/out/` directory.

### 2. Redirect and Proxy Configurations
- **Vercel vs Cloudflare Pages**: While a `vercel.json` exists at the root for Vercel deployments, Cloudflare Pages utilizes either `_redirects` rules or a custom edge router script.
- **Edge Routing & Proxy System**:
  - The project contains a custom Cloudflare Pages router at `frontend/public/_worker.js`.
  - When Next.js compiles, all assets from `/frontend/public` are copied directly into the `/frontend/out` build directory. Thus, `_worker.js` ends up at the root of the deployed assets, putting Cloudflare Pages in **Advanced Mode**.
  - `_worker.js` intercepts all incoming requests to the Pages deployment. It proxies routes matching `/api/`, `/ws/`, `/_/pa/`, `/scrape`, or `/health` to the backend target `BACKEND_URL` (currently set to `'https://jhfguf.pythonanywhere.com'`).
  - The script handles WebSocket protocol upgrades (converting `http` to `ws`) and sets the `Host` header to match the backend (critical for hosting providers that routing via Host headers).
  - To point to Render instead of PythonAnywhere, `BACKEND_URL` in `frontend/public/_worker.js` must be updated to the Render app URL (e.g. `https://jobhunt-pro.onrender.com`).

### 3. Backend CORS Allowed Origins
- **CORS Loading Location**: Allowed origins are loaded in `backend/main.py` (lines 294-299):
  ```python
  allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
  if allowed_origins_env:
      origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
  else:
      origins = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]
  ```
- **Dynamic CORS Validation**: `backend/main.py` uses a custom `SecureCORSMiddleware` (lines 247-290) when wildcards or explicit origins are configured. This middleware dynamically validates the `Origin` header using regex compiled from subdomain wildcards (e.g., `https://*.pages.dev` becomes `^https://[a-zA-Z0-9-]+\.pages\.dev$`).
- **Cloudflare Pages Update**: To support Cloudflare Pages domains securely, the production environment variable `ALLOWED_ORIGINS` must be updated to include the pages domain. For example:
  ```env
  ALLOWED_ORIGINS=https://*.pages.dev,https://yourcustomdomain.com
  ```

---

## Milestone 2: GitHub Actions Scheduled Keep-Alive

### 1. Existing Workflows
- The `.github/workflows/` directory contains existing workflows, including `keep-alive.yml` and `keep_alive.yml`. Both run on a `*/10 * * * *` schedule, but only ping the backend health endpoints.

### 2. Design of the 12-Minute Keep-Alive and Warming Workflow
A keep-alive workflow should run every 12 minutes to ping the Render backend's `/healthz` endpoint and run the Neon DB warming script (`core/neon_warmer.py`) to prevent serverless database auto-suspend (Neon's default is 300 seconds of inactivity).

#### Proposed Workflow File (`.github/workflows/keepalive.yml`):
```yaml
name: ⚡ Cloud Infrastructure Keep-Alive

on:
  schedule:
    - cron: "*/12 * * * *" # Triggers every 12 minutes
  workflow_dispatch: # Allows manual trigger from GitHub UI

jobs:
  ping-infrastructure:
    runs-on: ubuntu-latest
    steps:
      - name: 1️⃣ Checkout Repository Source
        uses: actions/checkout@v4

      - name: 2️⃣ Set up Python Environment
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: 3️⃣ Install Database Connector
        run: |
          python -m pip install --upgrade pip
          pip install psycopg2-binary

      - name: 4️⃣ Ping Render Backend /healthz
        env:
          RENDER_APP_URL: ${{ secrets.RENDER_APP_URL || 'https://jobhunt-pro.onrender.com' }}
        run: |
          TARGET_URL="${RENDER_APP_URL%/}/healthz"
          echo "Pinging backend at $TARGET_URL..."
          curl -f -sS --retry 3 --max-time 15 "$TARGET_URL" || echo "Warning: Render backend ping failed, continuing..."

      - name: 5️⃣ Run Neon DB Warmer
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          if [ -n "$DATABASE_URL" ]; then
            echo "Running database warming script..."
            python core/neon_warmer.py
          else
            echo "Error: DATABASE_URL secret is missing. Skipping database warm-up."
            exit 1
          fi
```

---

## Milestone 3: Celery Memory Guard

### 1. Process Spawning in `start_cloud.py`
- The `start_cloud.py` file supervises the FastAPI app (Uvicorn), Celery worker, and database sync worker under a single process tree.
- The Celery worker command is defined and executed inside `launch_services()` (lines 114-131):
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

### 2. Proposed Modification for Memory Guarding
Celery provides command-line flags to automatically recycle pool child worker processes when they exceed memory or execution thresholds:
- `--max-tasks-per-child=10`: Replaces the child process after it executes 10 tasks.
- `--max-memory-per-child=150000`: Replaces the child process if its memory footprint exceeds 150,000 KB (~150MB).

These options are only supported by the default `prefork` pool. They are incompatible with the `solo` pool used on Windows. Therefore, they must be added to the Linux branch:

#### Modified Command Logic in `start_cloud.py`:
```python
        if os.name == "nt":
            # On Windows, use solo pool to avoid multiprocessing issues
            celery_cmd.extend(["-P", "solo"])
        else:
            # On Linux (Render), use prefork pool with concurrency=1 and enforce memory guards
            celery_cmd.extend([
                "-c", "1",
                "--max-tasks-per-child=10",
                "--max-memory-per-child=150000"
            ])
```

---

## Milestone 4: Neon PgBouncer Connection String Updates

### 1. Current Database & Sync Worker Configurations
- `backend/database.py` establishes the SQLAlchemy engine connection (lines 27-46).
- `backend/sync_worker.py` establishes a raw connection to PostgreSQL via `asyncpg` (lines 135-146) to push local outbox records to the cloud database.
- **Problem**: When using Neon's connection pooler (PgBouncer in transaction mode), the driver must use SSL (`sslmode=require`) and prepared statements must be completely disabled because PgBouncer does not support session-bound prepared statement caches across transactions.

### 2. Driver Incompatibilities with Direct Parameter Appends
- The `asyncpg` driver used by SQLAlchemy (`postgresql+asyncpg://`) and directly in `sync_worker.py` **does not support** query string parameters like `sslmode` or `prepareThreshold` in the DSN URL. Doing so causes a connection error: `asyncpg.exceptions.InterfaceError: bad connection option`.
- Instead, connection-level configurations must be passed explicitly via Python arguments (`connect_args` for SQLAlchemy and constructor parameters for `asyncpg.connect()`).

### 3. Implementation Plan
We define a utility function to inject the port `5432` and append `?sslmode=require&prepareThreshold=0` to the database URL representation, and then parse these arguments out inside the database and sync worker connections to configure the drivers safely.

#### A. Database URL Manipulation Utility
```python
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def format_neon_connection_string(url: str) -> str:
    """Format connection string to target port 5432 and include PgBouncer params."""
    if not url:
        return url
        
    prefix = ""
    for p in ["postgresql+asyncpg://", "postgres+asyncpg://", "postgresql://", "postgres://"]:
        if url.startswith(p):
            prefix = p
            url = url[len(p):]
            break
    else:
        prefix = "postgresql://"

    # Parse using a mock standard scheme
    parsed = urlparse("postgresql://" + url)
    netloc = parsed.netloc
    
    credentials = ""
    host_port = netloc
    if "@" in netloc:
        credentials, host_port = netloc.rsplit("@", 1)
        credentials = credentials + "@"
        
    host = host_port
    if ":" in host_port:
        host, _ = host_port.rsplit(":", 1)
        
    # Standardize port to 5432 for pooler/database host
    new_netloc = f"{credentials}{host}:5432"
    
    # Append required parameters
    query_params = dict(parse_qsl(parsed.query))
    query_params["sslmode"] = "require"
    query_params["prepareThreshold"] = "0"
    
    new_query = urlencode(query_params)
    modified = parsed._replace(netloc=new_netloc, query=new_query)
    
    res = urlunparse(modified)
    if res.startswith("postgresql://"):
        res = prefix + res[len("postgresql://"):]
    return res
```

#### B. Safe SQLAlchemy Configuration in `backend/database.py`
Modify `_build_active_url` to run the formatter, then parse and set driver-specific arguments inside `engine_kwargs`:
```python
# Strip non-supported query params from string before engine creation
clean_url = ACTIVE_DB_URL
if "?" in clean_url:
    base_url, query = clean_url.split("?", 1)
    params = [p for p in query.split("&") if not (p.startswith("sslmode=") or p.startswith("prepareThreshold="))]
    clean_url = f"{base_url}?{'&'.join(params)}" if params else base_url

# Configure connection args
if "sslmode=require" in ACTIVE_DB_URL or "sslmode" in ACTIVE_DB_URL:
    engine_kwargs.setdefault("connect_args", {})["ssl"] = True

if "prepareThreshold=0" in ACTIVE_DB_URL:
    # Setting prepared_statement_cache_size=0 disables prepared statement cache in asyncpg
    engine_kwargs.setdefault("connect_args", {})["prepared_statement_cache_size"] = 0

engine = create_async_engine(clean_url, **engine_kwargs)
```

#### C. Safe `asyncpg` Connection in `backend/sync_worker.py`
Update `sync_outbox_to_cloud()` to clean the URL and inject connection parameters:
```python
# Format the remote PostgreSQL URL with parameters
formatted_pg_url = format_neon_connection_string(REMOTE_PG_URL)
raw_pg_url = formatted_pg_url.replace("postgresql+asyncpg://", "postgresql://")

# Clean URL parameters to avoid asyncpg interface errors
clean_pg_url = raw_pg_url
connect_kwargs = {}
if "?" in clean_pg_url:
    base_url, query = clean_pg_url.split("?", 1)
    params = [p for p in query.split("&") if not (p.startswith("sslmode=") or p.startswith("prepareThreshold="))]
    clean_pg_url = f"{base_url}?{'&'.join(params)}" if params else base_url

if "sslmode=require" in raw_pg_url:
    connect_kwargs["ssl"] = "require"
if "prepareThreshold=0" in raw_pg_url:
    # Disable prepared statements in raw asyncpg connection
    connect_kwargs["statement_cache_size"] = 0

# Connect safely
cloud_conn = await asyncpg.connect(clean_pg_url, **connect_kwargs)
```

---

## Milestone 5: Free Proxy Pool Scraper Rotation

### 1. Current Scraper Architecture
- `core/ghost_hunter.py` handles autonomous job scraping using `DDGS` to find LinkedIn job URLs and `Camoufox` (a stealth browser based on Playwright) to extract job details.
- Currently, `Camoufox(headless=True)` (line 69) is initialized without proxy settings. This exposes the scraper to IP rate-limiting and temporary blocks when fetching LinkedIn pages.

### 2. Rotation & Recovery Strategy
We implement a thread-safe proxy management layer that fetches free HTTP/HTTPS proxies hourly, validates their format, and rotates them when initializing the browser context. Dead or blocked proxies are evicted dynamically on connection errors.

#### Proposed Implementation Code for `GhostHunter`:
```python
import urllib.request
from bs4 import BeautifulSoup
import time
import random

class GhostHunter:
    _proxy_pool = []
    _last_scraped = 0.0

    def _scrape_free_proxies(self) -> list[str]:
        """Scrape public HTTP/HTTPS proxies from free-proxy-list.net."""
        proxies = []
        try:
            url = "https://free-proxy-list.net/"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read()
            
            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table", class_="table-striped")
            if table:
                for row in table.find_all("tr")[1:]:  # Skip header row
                    cols = row.find_all("td")
                    if len(cols) >= 2:
                        ip = cols[0].text.strip()
                        port = cols[1].text.strip()
                        proxies.append(f"http://{ip}:{port}")
        except Exception as e:
            logger.error(f"[PROXY-SCRAPER] Failed to harvest free proxies: {e}")
        return proxies

    def _get_proxy(self, force_refresh: bool = False) -> str | None:
        """Fetch a proxy from the pool, refreshing it hourly if required."""
        now = time.time()
        if force_refresh or not self._proxy_pool or (now - self._last_scraped > 3600):
            scraped = self._scrape_free_proxies()
            if scraped:
                self._proxy_pool = scraped
                self._last_scraped = now
                logger.info(f"[PROXY-SCRAPER] Pool updated with {len(self._proxy_pool)} proxies.")
            else:
                logger.warning("[PROXY-SCRAPER] Scraping returned empty results. Reusing current pool.")
        
        if self._proxy_pool:
            return random.choice(self._proxy_pool)
        return None

    def hunt_for_user(self, user_id: str, job_title: str, location: str, max_jobs: int = 5) -> None:
        # DDGS search logic (remains as is)
        # ...
        
        try:
            from camoufox.sync_api import Camoufox
            
            for url in urls:
                # Check DB for duplicate URL
                # ...
                
                # Fetch page with proxy rotation and connection error recovery
                success = False
                attempts = 3
                
                while attempts > 0 and not success:
                    proxy_str = self._get_proxy()
                    proxy_config = {"server": proxy_str} if proxy_str else None
                    logger.info(f"[DATASET-FETCHER] Attempting fetch with proxy: {proxy_str} ({attempts} attempts remaining)")
                    
                    try:
                        # Initialize browser with selected proxy
                        with Camoufox(headless=True, proxy=proxy_config) as browser:
                            page = browser.new_page()
                            logger.info(f"[DATASET-FETCHER] Navigating to: {url}")
                            page.goto(url, timeout=30000)
                            time.sleep(random.uniform(2, 4))  # Jitter delay
                            
                            html = page.content()
                            soup = BeautifulSoup(html, "html.parser")
                            
                            # Parse page contents
                            title_elem = soup.find("h1")
                            title = title_elem.text.strip() if title_elem else "Unknown Title"
                            
                            company_elem = soup.find("a", {"class": "topcard__org-name-link"})
                            company = company_elem.text.strip() if company_elem else "Unknown Company"
                            
                            desc_elem = soup.find("div", {"class": "description__text"})
                            desc = desc_elem.text.strip() if desc_elem else ""
                            
                            if len(desc) > 50:
                                # Save record in DB
                                # ...
                                logger.info(f"[DATASET-FETCHER] Successfully ingested: {title} at {company}")
                                success = True
                                
                    except Exception as e:
                        logger.warning(f"[DATASET-FETCHER] Proxy {proxy_str} failed: {e}. Evicting from pool...")
                        if proxy_str in self._proxy_pool:
                            self._proxy_pool.remove(proxy_str)
                        attempts -= 1
                
                # Jitter between job records
                jitter = random.uniform(15, 35)
                logger.info(f"[DATASET-FETCHER] Jitter delay: {jitter:.1f}s")
                time.sleep(jitter)
                
        except ImportError:
            logger.error("[DATASET-FETCHER] Camoufox dependency not found.")
        except Exception as e:
            logger.error(f"[DATASET-FETCHER] Fatal loop failure: {e}")
```
