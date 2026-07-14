# Milestone 1: Free Tier Keep-Alive Scheduler - Exploration & Implementation Strategy

## 1. Observation
We examined the relevant target files to understand the current structure and configurations.

### Target 1: `backend/main.py`
In `backend/main.py`, we observed health check endpoints defined at lines 203-213:
```python
203: @app.get("/health")
204: async def health_check(request: Request = None) -> dict[str, str]:
205:     """Retrieve service health status of task queue and async loop runner."""
206:     logger.info("Health check verification endpoint requested.")
207:     return {"status": "ok", "architecture": "FastAPI + Celery + Redis"}
208: 
209: 
210: @app.get("/healthz")
211: async def healthz(request: Request = None) -> dict[str, str]:
212:     """Lightweight Render health check endpoint."""
213:     return {"status": "ok"}
```
There is no `/api/v1/health` endpoint currently exposed.

### Target 2: `start_cloud.py`
In `start_cloud.py`, we observed how the container launches and monitors its services inside `launch_services()` (lines 50-96):
```python
50: def launch_services():
51:     """Launch Uvicorn, Celery, and Sync Worker concurrently."""
52:     
53:     # 1. Start Celery Worker (if Redis is configured)
54:     if os.environ.get("REDIS_URL"):
...
64:     sync_proc = subprocess.Popen([sys.executable, "-m", "backend.sync_worker"])
...
80:     uvicorn_proc = subprocess.Popen(uvicorn_cmd)
81:     processes.append(uvicorn_proc)
82: 
83:     # Keep script alive and monitor processes
84:     try:
85:         while True:
86:             time.sleep(5)
87:             for p in processes:
88:                 exit_code = p.poll()
...
```
There is currently no background thread or keep-alive scheduler running inside the startup script to query the web server.

### Target 3: GitHub Actions Workflows
Using the file search tool, we found that `.github/workflows/` does not exist or has no workflow files for keep-alive checks. Only some configuration files are located under `archive/` or individual node modules.

---

## 2. Logic Chain
1. **Endpoint Implementation**: Exposing `/api/v1/health` requires defining a new HTTP GET endpoint in `backend/main.py`. Placing this next to the existing `/healthz` route ensures minimal routing overhead and clean structure.
2. **Container Keep-Alive (Internal Daemon)**: 
   - Render containers shut down after 15 minutes of inactivity (lack of incoming traffic).
   - If we ping the public URL of the container from the inside, it leaves the container, hits Render's public router/load balancer, and comes back as a fresh incoming web request.
   - Pinging `localhost` internally would not go through the public router, but it is useful as a fallback.
   - By creating a background daemon thread in `start_cloud.py`, we ensure it starts with the container, runs every 10 minutes (less than the 15-minute Render timeout), and doesn't block the main Uvicorn or Celery processes.
   - The thread can check `RENDER_EXTERNAL_URL` or `SITE_URL` env vars, falling back to local `http://{HOST}:{PORT}/api/v1/health` if neither is defined (e.g. during local testing).
3. **External Keep-Alive (GitHub Actions)**:
   - Having an external scheduler pinging the public endpoint guarantees Render registers incoming activity even if internal network issues occur inside the container.
   - A GitHub Actions workflow running on a cron schedule (`*/10 * * * *`) satisfies this. It will derive the target URL from secrets (`RENDER_EXTERNAL_URL` or `SITE_URL`) with a fallback default.

---

## 3. Caveats
- **Local host fallback**: Pinging local `http://{HOST}:{PORT}` does not keep Render alive, but it does verify the server is responding to keep-alive requests locally. To keep Render alive, `RENDER_EXTERNAL_URL` or `SITE_URL` must be set in Render's environment variables.
- **GitHub Action Cron Delays**: GitHub Actions cron scheduler can sometimes experience delays of up to 10-15 minutes depending on GitHub's internal runner queues. Therefore, having *both* the internal daemon thread *and* the GitHub Action running in parallel provides high redundancy and guarantees the container stays awake.

---

## 4. Conclusion
We recommend implementing a redundant keep-alive strategy:
1. Add a lightweight `/api/v1/health` endpoint in `backend/main.py`.
2. Add a background daemon thread in `start_cloud.py` using `threading` and Python's standard `urllib.request` library.
3. Add a GitHub Actions workflow in `.github/workflows/keep_alive.yml` pinging the service.

### Recommended Code Modifications

#### 1. `backend/main.py` Patch
```diff
diff --git a/backend/main.py b/backend/main.py
--- a/backend/main.py
+++ b/backend/main.py
@@ -210,5 +210,11 @@
 @app.get("/healthz")
 async def healthz(request: Request = None) -> dict[str, str]:
     """Lightweight Render health check endpoint."""
     return {"status": "ok"}
 
+@app.get("/api/v1/health")
+async def health_v1(request: Request = None) -> dict[str, str]:
+    """Lightweight API v1 health check endpoint."""
+    return {"status": "ok"}
+
 @app.post("/webhook/telegram")
```

#### 2. `start_cloud.py` Patch
```diff
diff --git a/start_cloud.py b/start_cloud.py
--- a/start_cloud.py
+++ b/start_cloud.py
@@ -10,4 +10,5 @@
 import subprocess
 import logging
 import signal
+import threading
 
@@ -80,5 +81,38 @@
     uvicorn_proc = subprocess.Popen(uvicorn_cmd)
     processes.append(uvicorn_proc)
 
+    # Start Keep-Alive ping daemon thread
+    def keep_alive_ping():
+        import urllib.request
+        import urllib.error
+        # Wait 30 seconds for services to fully initialize
+        time.sleep(30)
+        
+        # Resolve target keep-alive ping URL
+        target_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("SITE_URL")
+        if not target_url:
+            target_url = f"http://{HOST}:{PORT}"
+        target_url = target_url.rstrip("/") + "/api/v1/health"
+        
+        logger.info(f"Keep-Alive ping daemon started targeting: {target_url}")
+        
+        while True:
+            try:
+                req = urllib.request.Request(
+                    target_url, 
+                    headers={"User-Agent": "JobHuntPro-KeepAlive/1.0"}
+                )
+                with urllib.request.urlopen(req, timeout=10) as response:
+                    if response.getcode() == 200:
+                        logger.info("Keep-Alive ping check: SUCCESS (200 OK)")
+                    else:
+                        logger.warning(f"Keep-Alive ping check: WARNING (Status {response.getcode()})")
+            except urllib.error.URLError as e:
+                logger.warning(f"Keep-Alive ping check: FAILED (URLError): {e.reason}")
+            except Exception as e:
+                logger.error(f"Keep-Alive ping check: ERROR: {e}")
+            
+            # Ping every 10 minutes (600 seconds)
+            time.sleep(600)
+
+    ping_thread = threading.Thread(target=keep_alive_ping, daemon=True)
+    ping_thread.start()
+
     # Keep script alive and monitor processes
     try:
         while True:
```

#### 3. `.github/workflows/keep_alive.yml` Replacement Content
```yaml
name: Free Tier Keep-Alive

on:
  schedule:
    # Runs every 10 minutes
    - cron: '*/10 * * * *'
  workflow_dispatch: # Allows manual trigger

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Keep-Alive Endpoint
        env:
          SITE_URL: ${{ secrets.SITE_URL }}
          RENDER_EXTERNAL_URL: ${{ secrets.RENDER_EXTERNAL_URL }}
        run: |
          # Determine the target URL to ping
          URL=""
          if [ -n "$RENDER_EXTERNAL_URL" ]; then
            URL="$RENDER_EXTERNAL_URL"
          elif [ -n "$SITE_URL" ]; then
            URL="$SITE_URL"
          else
            # Fallback to the production Render URL
            URL="https://jobhunt-pro.onrender.com"
          fi
          
          # Clean trailing slash and append health endpoint
          TARGET_URL="${URL%/}/api/v1/health"
          echo "Pinging keep-alive endpoint: $TARGET_URL"
          
          # Send a GET request with curl, expecting a 200 OK. Try up to 3 times on failure.
          curl --fail --silent --show-error --retry 3 --max-time 10 "$TARGET_URL"
```

---

## 5. Verification Method
1. **Unit Test Verification**: Create a test file `tests/test_keep_alive.py` with the following content and run `pytest tests/test_keep_alive.py`:
   ```python
   from fastapi.testclient import TestClient
   from backend.main import app

   client = TestClient(app)

   def test_api_v1_health():
       response = client.get("/api/v1/health")
       assert response.status_code == 200
       assert response.json() == {"status": "ok"}
   ```
2. **Daemon Thread Execution Verification**: 
   - Start the stack locally by running `python start_cloud.py`.
   - Check the console logs. A message saying `"Keep-Alive ping daemon started targeting: ..."` should appear after 30 seconds.
   - Wait 10 minutes or mock `time.sleep` to verify another log `"Keep-Alive ping check: SUCCESS (200 OK)"` is printed.
3. **GitHub Workflow Verification**:
   - Commit the `.github/workflows/keep_alive.yml` file to GitHub.
   - Manually trigger the workflow from the Actions tab in GitHub (using `workflow_dispatch`) to verify it runs and prints the output successful response.
