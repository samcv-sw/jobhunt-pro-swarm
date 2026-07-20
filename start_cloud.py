#!/usr/bin/env python3
"""
JobHunt Pro - Zero Cost Enterprise Cloud Startup Script
Runs FastAPI, Celery Worker, and Database Sync Worker in a SINGLE container.
This ensures you only consume 1 Free Tier instance on platforms like Render.
"""
import gc
import json as _json
import logging
import os
import signal
import subprocess
import sys
import threading
import time

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

class LogtailHandler(logging.Handler):
    """Custom asynchronous Logtail logging handler using standard urllib to prevent blocking."""
    def __init__(self, source_token: str):
        super().__init__()
        self.source_token = source_token
        from queue import Queue as _Queue
        self.queue = _Queue()
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def emit(self, record):
        try:
            log_entry = self.format(record)
            from datetime import datetime as _datetime
            payload = {
                "message": log_entry,
                "dt": _datetime.utcfromtimestamp(record.created).isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "pid": record.process,
            }
            self.queue.put(payload)
        except Exception:
            self.handleError(record)

    def _worker(self):
        import urllib.error
        import urllib.request
        while True:
            try:
                payload = self.queue.get()
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.source_token}",
                    "User-Agent": "LogtailLogger/1.0"
                }
                req = urllib.request.Request(
                    "https://in.logs.betterstack.com",
                    data=_json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                try:
                    with urllib.request.urlopen(req, timeout=5) as response:
                        response.read()
                except urllib.error.URLError:
                    pass
            except Exception:
                pass

_handlers = [logging.StreamHandler()]
_token = os.environ.get("LOGTAIL_SOURCE_TOKEN")
if _token:
    _handlers.append(LogtailHandler(_token))

for h in _handlers:
    h.setFormatter(_JsonFormatter())

logging.basicConfig(level=logging.INFO, handlers=_handlers)
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
        celery_cmd = [sys.executable, "-m", "celery", "-A", "backend.tasks", "worker", "--loglevel=info"]
        if os.name == "nt":
            # On Windows, use solo pool to avoid multiprocessing issues
            celery_cmd.extend(["-P", "solo"])
        else:
            # On Linux (Render), omit -P solo and use concurrency=1 to allow worker process recycling
            celery_cmd.extend(["-c", "1", "--max-tasks-per-child=10", "--max-memory-per-child=150000"])

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

    # 3. Start FastAPI Web Server (Granian if installed, otherwise Uvicorn)
    has_granian = False
    try:
        import importlib.util
        if importlib.util.find_spec("granian") is not None:
            has_granian = True
    except ImportError:
        pass

    if has_granian and os.name != "nt":
        logger.info(f"Starting JobHunt Pro API with GRANIAN on {HOST}:{PORT}...")
        web_cmd = [
            sys.executable, "-m", "granian",
            "--interface", "asgi",
            "--host", HOST,
            "--port", str(PORT),
            "--workers", str(WORKERS),
            "backend.main:app"
        ]
    else:
        logger.info(f"Starting JobHunt Pro API with UVICORN on {HOST}:{PORT}...")
        web_cmd = [
            sys.executable, "-m", "uvicorn",
            "backend.main:app",
            "--host", HOST,
            "--port", str(PORT),
            "--workers", str(WORKERS),
            "--access-log",
        ]
        if os.name != "nt":
            web_cmd.extend(["--loop", "uvloop"])

    web_proc = subprocess.Popen(web_cmd)
    running_services["uvicorn"] = {
        "proc": web_proc,
        "cmd": web_cmd,
        "limit": 220 * 1024 * 1024  # 220MB limit for Uvicorn
    }

    # Start Keep-Alive ping daemon thread (skip during test runs to prevent thread leak warnings)
    def keep_alive_ping():
        import urllib.error
        import urllib.request
        try:
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
                except (KeyboardInterrupt, SystemExit):
                    return
                except Exception as e:
                    logger.error(f"Keep-Alive ping check: ERROR: {e}")

                try:
                    # Ping every 10 minutes (600 seconds)
                    time.sleep(600)
                except (KeyboardInterrupt, SystemExit):
                    return
        except (KeyboardInterrupt, SystemExit):
            return

    # Skip the keep-alive ping thread during test runs to prevent thread leak warnings
    _is_testing = "pytest" in sys.modules or os.environ.get("TESTING", "false").lower() == "true"
    if not _is_testing:
        ping_thread = threading.Thread(target=keep_alive_ping, daemon=True, name="keep_alive_ping")
        ping_thread.start()

    # Attempt psutil import at startup — but use sys.modules lookup in the loop
    # so that test mocks via patch.dict(sys.modules, {'psutil': ...}) take effect.
    try:
        import psutil as _psutil_check
        logger.info("psutil memory monitor initialization: SUCCESS")
        del _psutil_check
    except ImportError:
        logger.warning("psutil memory monitor initialization: FAILED (psutil not installed). Skipping memory checks.")

    # Keep script alive, perform GC, and monitor processes/memory
    try:
        while True:
            # Explicitly run garbage collector in parent supervisor process
            gc.collect()

            # Fetch psutil from sys.modules so unit tests can inject mocks via patch.dict
            psutil = sys.modules.get("psutil")

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

            # Sleep at the end of the loop (tests intercept this to control loop tick count)
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("Supervisor loop interrupted. Exiting launch_services().")

def startup_self_test() -> bool:
    """
    Run environment and connectivity checks before launching services.

    Checks performed:
    - JWT secret key presence (critical — exits if absent outside TESTING mode)
    - GROQ_API_KEY presence (warning only)
    - Redis reachability via REDIS_URL (warning only)
    - Neon DB reachability via DATABASE_URL (warning only)

    Emits a single structured JSON summary log at INFO level on completion.

    Returns:
        True when all checks pass (or only non-critical warnings were raised).
    """
    is_testing = "pytest" in sys.modules or os.environ.get("TESTING", "false").lower() == "true"
    results: dict = {}

    # --- JWT Secret Key ---
    jwt_ok = bool(
        os.environ.get("JWT_SECRET_KEY") or os.environ.get("JWT_SECRET_KEYS")
    )
    results["jwt_secret"] = "ok" if jwt_ok else "missing"
    if not jwt_ok:
        if is_testing:
            logger.warning("JWT_SECRET_KEY / JWT_SECRET_KEYS not set (allowed in TESTING mode)")
        else:
            logger.critical(
                "CRITICAL: Neither JWT_SECRET_KEY nor JWT_SECRET_KEYS is set. "
                "The API cannot issue secure tokens. Set the variable and restart."
            )
            sys.exit(1)

    # --- GROQ API Key ---
    groq_ok = bool(os.environ.get("GROQ_API_KEY"))
    results["groq_api_key"] = "ok" if groq_ok else "missing"
    if not groq_ok:
        logger.warning("GROQ_API_KEY is not set — AI cover-letter generation will be unavailable.")

    # --- Redis Connectivity ---
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis as _redis
            _redis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2).ping()
            results["redis"] = "ok"
        except Exception as exc:
            results["redis"] = f"unreachable: {exc}"
            logger.warning("Redis connectivity check FAILED: %s", exc)
    else:
        results["redis"] = "not_configured"

    # --- Neon DB Connectivity ---
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        try:
            import psycopg2 as _psycopg2
            _conn = _psycopg2.connect(database_url, connect_timeout=5)
            _conn.close()
            results["neon_db"] = "ok"
        except Exception as exc:
            results["neon_db"] = f"unreachable: {exc}"
            logger.warning("Neon DB connectivity check FAILED: %s", exc)
    else:
        results["neon_db"] = "not_configured"

    # --- Structured JSON Startup Summary ---
    logger.info(
        _json.dumps({
            "event": "startup_self_test_complete",
            "testing_mode": is_testing,
            "checks": results,
        })
    )
    return True


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    startup_self_test()
    try:
        launch_services()
    except SystemExit:
        pass
    except KeyboardInterrupt:
        cleanup(None, None)
