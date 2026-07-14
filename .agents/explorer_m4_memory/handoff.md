# Handoff Report: Milestone 4 - Memory Reclamation and OOM Prevention

## 1. Observation
We observed the following about process execution and memory management in the project:
*   **Celery Initialization (`backend/celery_app.py`):**
    The celery application is initialized at lines 12-17 and configured via `celery_app.conf.update` at lines 19-41:
    ```python
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        broker_connection_retry_on_startup=True,
        # Non-blocking / fail-fast configurations
        broker_connection_timeout=0.2,            # Fast timeout for establishing broker connection
        broker_transport_options={
            "max_connections": 10,                 # Max connections in pool
            "pool_timeout": 0.05,                  # Fast timeout for checking out connection from pool (50ms)
            "connect_timeout": 0.2,                # Transport-level connection timeout (200ms)
        },
        # Route specific tasks to different queues if needed
        task_routes={
            "backend.tasks.scrape_jobs": {"queue": "scraping"},
            "backend.tasks.generate_cover_letter": {"queue": "ai_inference"},
            "backend.tasks.send_application_email": {"queue": "email_sender"},
        }
    )
    ```
    No memory limit or task-count limit (such as `worker_max_tasks_per_child` or `worker_max_memory_per_child`) is currently set here.
*   **Process Startup (`start_cloud.py`):**
    At lines 55-61, `start_cloud.py` starts the Celery worker process with the `-P solo` pool:
    ```python
    # 1. Start Celery Worker (if Redis is configured)
    if os.environ.get("REDIS_URL"):
        logger.info("Starting Celery Worker...")
        celery_cmd = ["celery", "-A", "backend.tasks", "worker", "--loglevel=info", "-P", "solo", "-c", "1"]
        celery_proc = subprocess.Popen(celery_cmd)
        processes.append(celery_proc)
    ```
    The `-P solo` pool executes tasks in the master worker thread directly, meaning Celery will not spawn child processes. Consequently, any child-recycling settings (like `worker_max_tasks_per_child`) will have no effect.
*   **Supervisor Loop (`start_cloud.py`):**
    At lines 125-136, the supervisor loop merely checks if any process has exited:
    ```python
    # Keep script alive and monitor processes
    try:
        while True:
            time.sleep(5)
            for p in processes:
                exit_code = p.poll()
                if exit_code is not None:
                    logger.error(
                        f"A critical background service (PID {p.pid}) exited with code {exit_code}! Shutting down container..."
                    )
                    cleanup(None, None)
    except KeyboardInterrupt:
        cleanup(None, None)
    ```
    No active memory monitoring or individual recycling of processes exists in `start_cloud.py`.
*   **GC Configuration:**
    Python's default garbage collection thresholds are set to `(700, 10, 10)`. No custom thresholds or periodic collections are implemented in `start_cloud.py`, `backend/main.py`, or `backend/sync_worker.py`.

---

## 2. Logic Chain
To strictly limit RAM usage below 512MB and prevent container OOMs:
1.  **Enable Worker Process Recycling:** Celery workers running scraper operations and language model integration are highly susceptible to memory leaks. Setting `worker_max_tasks_per_child=10` and `worker_max_memory_per_child=150000` (150MB limit) forces Celery to recycle child worker processes. (Observation: `backend/celery_app.py` conf update has no worker limit configs).
2.  **Enable Prefork Pool in Linux Production:** Because Celery's child worker process recycling only works when utilizing a process pool (prefork), we must omit the `-P solo` argument when running on Linux (Render), while keeping `-P solo` for Windows development to avoid multi-processing compatibility issues. (Observation: `start_cloud.py` uses `-P solo` unconditionally).
3.  **Perform Aggressive GC Tuning:** In a low-memory 512MB container, garbage collection should trigger frequently to reclaim memory from temporary objects. Calling `gc.set_threshold(50, 5, 5)` at the entry points of all components (FastAPI app, Celery worker, Database sync worker, and start_cloud itself) forces Python's garbage collector to trigger after only 50 net allocations rather than 700. (Observation: Default Python GC is used).
4.  **Introduce Active Memory Monitoring Daemon:** A memory monitor daemon in `start_cloud.py` can monitor RSS of each process and the global container footprint. If an individual process breaches its threshold (e.g. Celery > 180MB, Sync > 80MB, Uvicorn > 220MB) or total footprint hits 450MB, the supervisor can terminate the offending process. (Observation: `start_cloud.py` supervisor loop only checks `poll()`).
5.  **Graceful Self-Healing Restarts:** By replacing the list of processes with a dictionary containing command lines and PID references, the supervisor can gracefully restart any process that terminates (whether via normal exit, crash, or manual termination from the memory monitor) without killing the entire container. Since Celery uses `task_acks_late=True`, restarted worker processes will not lose tasks. (Observation: `task_acks_late=True` is active).

---

## 3. Caveats
*   **psutil availability:** The memory monitor depends on `psutil`. If `psutil` fails to import (e.g. not present in a minimalist virtualenv), the active memory monitor must fall back to basic process status polling to prevent start failures.
*   **Windows Subprocess Behavior:** When terminating child processes, Windows handles signals differently than POSIX systems. However, Render is a Linux container platform, so targeting POSIX-compliant termination (`SIGTERM`) is correct.

---

## 4. Conclusion & Proposed Changes
We recommend the following exact changes to implement memory reclamation and OOM prevention:

### A. Celery Settings: `backend/celery_app.py`
Add worker limits to recycle worker processes and aggressively tune GC:
```python
<<<<
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
====
import gc
gc.set_threshold(50, 5, 5)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,            # Recycle child worker after 10 tasks to reclaim memory
    worker_max_memory_per_child=150000,       # Recycle child worker if RSS exceeds 150MB (in KB)
    broker_connection_retry_on_startup=True,
>>>>
```

### B. FastAPI Startup: `backend/main.py`
Tune GC threshold at startup:
```python
<<<<
import asyncio
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
====
import asyncio
import logging
import os
import sys
import gc
from concurrent.futures import ThreadPoolExecutor

gc.set_threshold(50, 5, 5)
>>>>
```

### C. Sync Worker: `backend/sync_worker.py`
Tune GC threshold and run explicit cleanup on every iteration:
```python
<<<<
import asyncio
import json
import logging
import os
import random
import sys
import time
====
import asyncio
import json
import logging
import os
import random
import sys
import time
import gc

gc.set_threshold(50, 5, 5)
>>>>
```
And inside the main `sync_outbox_to_cloud` loop:
```python
<<<<
        except Exception as e:
            logger.error(f"[SyncWorker] Unexpected error: {e}")
        
        # Poll every 30 seconds
        await asyncio.sleep(30)
====
        except Exception as e:
            logger.error(f"[SyncWorker] Unexpected error: {e}")
        
        # Explicit garbage collection to free up memory from db sessions
        gc.collect()
        # Poll every 30 seconds
        await asyncio.sleep(30)
>>>>
```

### D. Startup Script & Memory Monitor: `start_cloud.py`
Rewrite `start_cloud.py` to:
1. Enable Celery prefork pool on Linux (`-c 1` instead of `-P solo`).
2. Integrate `psutil` memory monitoring and self-healing worker restarts.
3. Automatically recycle individual bloated workers and trigger fallback recovery under high total RAM pressure.

Proposed replacement code for `start_cloud.py`:
```python
#!/usr/bin/env python3
"""
JobHunt Pro - Zero Cost Enterprise Cloud Startup Script
Runs FastAPI, Celery Worker, and Database Sync Worker in a SINGLE container.
This ensures you only consume 1 Free Tier instance on platforms like Render.
"""
import json as _json
import logging
import os
import signal
import subprocess
import sys
import threading
import time
import gc

# Aggressive garbage collection tuning for the parent supervisor process
gc.set_threshold(50, 5, 5)

class _JsonFormatter(logging.Formatter):
    """JSON log formatter compatible with Render log drain and Datadog/Logtail."""
    def format(self, record: logging.LogRecord) -> str:
        return _json.dumps({
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "pid": record.process,
        })

_handler = logging.StreamHandler()
_handler.setFormatter(_JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[_handler])
logger = logging.getLogger("cloud-start")

PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")
WORKERS = int(os.environ.get("WEB_CONCURRENCY", 1)) # Keep at 1 for free tier memory limits
running_services = {}

def cleanup(signum, frame):
    """Handle SIGINT/SIGTERM: gracefully terminate all child processes and exit."""
    logger.info("Shutting down all services...")
    for name, service in running_services.items():
        try:
            service["proc"].terminate()
        except OSError:
            pass  # Process may already have exited
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def launch_services():
    """Launch Uvicorn, Celery, and Sync Worker concurrently."""

    # 1. Start Celery Worker (if Redis is configured)
    if os.environ.get("REDIS_URL"):
        logger.info("Starting Celery Worker...")
        celery_cmd = ["celery", "-A", "backend.tasks", "worker", "--loglevel=info"]
        if os.name == "nt":
            # On Windows, use solo pool to avoid multiprocessing issues
            celery_cmd.extend(["-P", "solo"])
        else:
            # On Linux (Render), omit -P solo and use concurrency=1 to allow worker process recycling
            celery_cmd.extend(["-c", "1"])
        
        celery_proc = subprocess.Popen(celery_cmd)
        running_services["celery"] = {
            "proc": celery_proc,
            "cmd": celery_cmd,
            "limit": 180 * 1024 * 1024  # 180MB limit for Celery
        }
    else:
        logger.warning("REDIS_URL not set. Background tasks (Scraping/Emails) will fail.")

    # 2. Start Sync Worker (Background process)
    logger.info("Starting Database Sync Worker...")
    sync_cmd = [sys.executable, "-m", "backend.sync_worker"]
    sync_proc = subprocess.Popen(sync_cmd)
    running_services["sync_worker"] = {
        "proc": sync_proc,
        "cmd": sync_cmd,
        "limit": 80 * 1024 * 1024   # 80MB limit for Database Sync Worker
    }

    # 3. Start FastAPI Uvicorn (Blocking process)
    logger.info(f"Starting JobHunt Pro API on {HOST}:{PORT}...")
    uvicorn_cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", HOST,
        "--port", str(PORT),
        "--workers", str(WORKERS),
        "--access-log",
    ]
    if os.name != "nt":
        uvicorn_cmd.extend(["--loop", "uvloop"])

    uvicorn_proc = subprocess.Popen(uvicorn_cmd)
    running_services["uvicorn"] = {
        "proc": uvicorn_proc,
        "cmd": uvicorn_cmd,
        "limit": 220 * 1024 * 1024  # 220MB limit for Uvicorn
    }

    # Start Keep-Alive ping daemon thread
    def keep_alive_ping():
        import urllib.error
        import urllib.request
        # Wait 30 seconds for services to fully initialize
        time.sleep(30)

        # Resolve target keep-alive ping URL
        target_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("SITE_URL")
        if not target_url:
            ping_host = "127.0.0.1" if HOST == "0.0.0.0" else HOST
            target_url = f"http://{ping_host}:{PORT}"
        if not target_url.startswith("http"):
            target_url = "https://" + target_url
        target_url = target_url.rstrip("/") + "/api/v1/health"

        logger.info(f"Keep-Alive ping daemon started targeting: {target_url}")

        while True:
            try:
                req = urllib.request.Request(
                    target_url,
                    headers={"User-Agent": "JobHuntPro-KeepAlive/1.0"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.getcode() == 200:
                        logger.info("Keep-Alive ping check: SUCCESS (200 OK)")
                    else:
                        logger.warning(f"Keep-Alive ping check: WARNING (Status {response.getcode()})")
            except urllib.error.URLError as e:
                logger.warning(f"Keep-Alive ping check: FAILED (URLError): {e.reason}")
            except Exception as e:
                logger.error(f"Keep-Alive ping check: ERROR: {e}")

            # Ping every 10 minutes (600 seconds)
            time.sleep(600)

    ping_thread = threading.Thread(target=keep_alive_ping, daemon=True)
    ping_thread.start()

    # Initialize psutil if available
    try:
        import psutil
        logger.info("psutil memory monitor initialization: SUCCESS")
    except ImportError:
        psutil = None
        logger.warning("psutil memory monitor initialization: FAILED (psutil not installed). Skipping memory checks.")

    # Keep script alive, perform GC, and monitor processes/memory
    try:
        while True:
            time.sleep(5)
            
            # Explicitly run garbage collector in parent supervisor process
            gc.collect()

            total_rss = 0
            if psutil:
                try:
                    # Get parent process RSS
                    total_rss += psutil.Process(os.getpid()).memory_info().rss
                except Exception:
                    pass

            for name, service in list(running_services.items()):
                p = service["proc"]
                exit_code = p.poll()
                if exit_code is not None:
                    logger.error(
                        f"Service '{name}' (PID {p.pid}) exited with code {exit_code}! Restarting..."
                    )
                    new_proc = subprocess.Popen(service["cmd"])
                    service["proc"] = new_proc
                    continue

                if psutil:
                    try:
                        proc_info = psutil.Process(p.pid)
                        rss = proc_info.memory_info().rss
                        # Sum up all spawned child processes
                        for child in proc_info.children(recursive=True):
                            rss += child.memory_info().rss
                        
                        total_rss += rss
                        logger.debug(f"Service '{name}' (PID {p.pid}) memory usage: {rss / (1024*1024):.1f}MB")

                        # If service memory exceeds limits, terminate it (the loop will auto-restart it on next tick)
                        if rss > service["limit"]:
                            logger.warning(
                                f"Service '{name}' (PID {p.pid}) RSS ({rss / (1024*1024):.1f}MB) exceeded "
                                f"limit of {service['limit'] / (1024*1024):.1f}MB! Recycling service..."
                            )
                            p.terminate()
                            try:
                                p.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                p.kill()
                                p.wait()

                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        logger.warning(f"Failed to query memory for service '{name}': {e}")

            # If the total container footprint exceeds 450MB, force recycle the largest worker process to prevent OOM
            if psutil and total_rss > 450 * 1024 * 1024:
                logger.warning(
                    f"Global container footprint ({total_rss / (1024*1024):.1f}MB) approaching 512MB threshold! "
                    f"Identifying largest consumer to recycle..."
                )
                max_service_name = None
                max_service_rss = 0
                for name, service in running_services.items():
                    p = service["proc"]
                    if p.poll() is None:
                        try:
                            proc_info = psutil.Process(p.pid)
                            rss = proc_info.memory_info().rss
                            for child in proc_info.children(recursive=True):
                                rss += child.memory_info().rss
                            if rss > max_service_rss:
                                max_service_rss = rss
                                max_service_name = name
                        except Exception:
                            pass
                
                if max_service_name:
                    logger.warning(
                        f"Recycling largest consumer '{max_service_name}' ({max_service_rss / (1024*1024):.1f}MB) "
                        f"to prevent global OOM."
                    )
                    running_services[max_service_name]["proc"].terminate()
                    try:
                        running_services[max_service_name]["proc"].wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        running_services[max_service_name]["proc"].kill()
                        running_services[max_service_name]["proc"].wait()

    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    launch_services()
```

---

## 5. Verification Method
1.  **Unit Tests:**
    Run python unit tests to verify the files do not contain syntax errors or import issues:
    ```bash
    python -m pytest archive/test_client.py
    ```
2.  **Dry Run with Memory Monitoring:**
    Run the startup script locally in a terminal with the debugging logs enabled to ensure all subprocesses spin up and are monitored properly:
    ```bash
    python start_cloud.py
    ```
3.  **Simulated Memory Leak Verification:**
    We can temporarily set a very low threshold (e.g. 50MB) for `sync_worker` in `start_cloud.py` to verify the memory monitor correctly detects the limit breach, terminates the process, and automatically re-launches it.
4.  **Celery Worker Prefork Pool Verification:**
    Verify Celery starts up with the prefork worker model on Linux (Render) and that the child process restarts after processing 10 tasks.
