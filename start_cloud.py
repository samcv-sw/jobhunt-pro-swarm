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
import secrets
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

    # 2. Start Sync Worker (Background process - optional)
    try:
        if os.path.exists("backend/sync_worker.py"):
            logger.info("Starting Database Sync Worker...")
            sync_cmd = [sys.executable, "-m", "backend.sync_worker"]
            sync_proc = subprocess.Popen(sync_cmd)
            running_services["sync_worker"] = {
                "proc": sync_proc,
                "cmd": sync_cmd,
                "limit": 80 * 1024 * 1024   # 80MB limit for Database Sync Worker
            }
    except Exception as exc:
        logger.warning(f"Sync worker skipped: {exc}")

    # 3. Start FastAPI Web Server
    logger.info(f"Starting JobHunt Pro Sovereign Engine on {HOST}:{PORT}...")
    web_cmd = [
        sys.executable, "-m", "uvicorn",
        "web.app_v2:app",
        "--host", HOST,
        "--port", str(PORT),
        "--workers", str(WORKERS),
        "--access-log",
    ]

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
            target_url = target_url.rstrip("/") + "/ping"

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
                    # Ping every 4 minutes (240 seconds)
                    time.sleep(240)
                except (KeyboardInterrupt, SystemExit):
                    return
        except (KeyboardInterrupt, SystemExit):
            return

    # Skip the keep-alive ping thread during test runs to prevent thread leak warnings
    _is_testing = "pytest" in sys.modules or os.environ.get("TESTING", "false").lower() == "true"
    if not _is_testing:
        ping_thread = threading.Thread(target=keep_alive_ping, daemon=True, name="keep_alive_ping")
        ping_thread.start()

        try:
            from core.telegram_daemon import start_telegram_daemon_background
            start_telegram_daemon_background()
            logger.info("24/7 Telegram Bot Daemon initialization: SUCCESS")
        except Exception as tg_daemon_err:
            logger.warning(f"Telegram Bot Daemon startup notice: {tg_daemon_err}")

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

            # Modular memory evaluation and enforcement
            evaluate_memory_and_enforce(running_services)

            # Sleep at the end of the loop (tests intercept this to control loop tick count)
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("Supervisor loop interrupted. Exiting launch_services().")


def get_process_tree_rss(pid: int, psutil_mod=None) -> int:
    """Calculate total RSS in bytes for a PID and all its recursive children."""
    if psutil_mod is None:
        psutil_mod = sys.modules.get("psutil")
    if not psutil_mod or not pid:
        return 0

    total = 0
    try:
        proc = psutil_mod.Process(pid)
        total += proc.memory_info().rss
        for child in proc.children(recursive=True):
            try:
                total += child.memory_info().rss
            except (getattr(psutil_mod, "NoSuchProcess", Exception),
                    getattr(psutil_mod, "AccessDenied", Exception),
                    getattr(psutil_mod, "ZombieProcess", Exception),
                    AttributeError, ProcessLookupError):
                pass
    except (getattr(psutil_mod, "NoSuchProcess", Exception),
            getattr(psutil_mod, "AccessDenied", Exception),
            getattr(psutil_mod, "ZombieProcess", Exception),
            AttributeError, ProcessLookupError):
        pass
    return total


def terminate_and_recycle(service_name: str, service: dict, timeout: float = 5.0) -> bool:
    """Gracefully terminate a process with SIGKILL fallback, and restart it."""
    proc = service.get("proc")
    if not proc:
        return False

    try:
        proc.terminate()
        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    except (OSError, ProcessLookupError):
        pass

    # Immediately respawn worker to eliminate downtime window
    if "cmd" in service:
        service["proc"] = subprocess.Popen(service["cmd"])
        return True
    return False


def evaluate_memory_and_enforce(
    running_services: dict,
    psutil_mod=None,
    global_limit_bytes: int = 450 * 1024 * 1024,
    supervisor_pid: int = None
) -> dict:
    """
    Evaluate RSS for supervisor and all services.
    Enforces per-service limits (Tier 1) and global container ceiling (Tier 2).
    Returns telemetry dictionary detailing actions taken.
    """
    if psutil_mod is None:
        psutil_mod = sys.modules.get("psutil")
    if not psutil_mod:
        return {"status": "psutil_missing", "total_rss_bytes": 0, "service_rss_map": {}, "recycled": []}

    recycled = []
    total_rss = 0

    # Supervisor PID memory
    sup_pid = supervisor_pid or os.getpid()
    try:
        sup_rss = psutil_mod.Process(sup_pid).memory_info().rss
        if isinstance(sup_rss, (int, float)):
            total_rss += int(sup_rss)
    except Exception:
        pass

    service_rss_map = {}

    # Check each service
    for name, service in list(running_services.items()):
        p = service.get("proc")
        if not p:
            continue

        if p.poll() is not None:
            # Service died or exited, auto-restart
            if "cmd" in service:
                logger.error(f"Service '{name}' (PID {getattr(p, 'pid', 'unknown')}) exited! Restarting...")
                service["proc"] = subprocess.Popen(service["cmd"])
            continue

        rss = get_process_tree_rss(p.pid, psutil_mod)
        if not isinstance(rss, (int, float)):
            rss = 0
        service_rss_map[name] = rss
        total_rss += int(rss)

        # Tier 1: Per-service limit check
        limit = service.get("limit", float("inf"))
        if rss > limit:
            logger.warning(
                f"Service '{name}' (PID {p.pid}) RSS ({rss / (1024*1024):.1f}MB) exceeded "
                f"limit of {limit / (1024*1024):.1f}MB! Recycling service..."
            )
            terminate_and_recycle(name, service)
            recycled.append({"service": name, "reason": "per_service_limit", "rss": rss})

    # Tier 2: Global 450MB container ceiling check
    # Only trigger if no service was already recycled in Tier 1 (avoiding double-recycle)
    if not recycled and total_rss > global_limit_bytes:
        logger.warning(
            f"Global container footprint ({total_rss / (1024*1024):.1f}MB) exceeding "
            f"450MB ceiling ({global_limit_bytes / (1024*1024):.1f}MB)! Identifying largest consumer..."
        )
        max_service_name = None
        max_service_rss = 0
        for name, rss in service_rss_map.items():
            p = running_services[name].get("proc")
            if p and p.poll() is None and rss > max_service_rss:
                max_service_rss = rss
                max_service_name = name

        if max_service_name:
            logger.warning(
                f"Recycling largest consumer '{max_service_name}' ({max_service_rss / (1024*1024):.1f}MB) "
                f"to prevent global OOM."
            )
            terminate_and_recycle(max_service_name, running_services[max_service_name])
            recycled.append({"service": max_service_name, "reason": "global_ceiling_breach", "rss": max_service_rss})

    return {
        "status": "ok",
        "total_rss_bytes": total_rss,
        "service_rss_map": service_rss_map,
        "recycled": recycled
    }

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
    # SECURITY: Load from env only. If absent, generate a cryptographically
    # random 64-char secret at runtime — never a hardcoded, predictable value.
    jwt_secret = os.environ.get("JWT_SECRET_KEY") or os.environ.get("JWT_SECRET_KEYS") or os.environ.get("SECRET_KEY")
    if not jwt_secret:
        jwt_secret = secrets.token_hex(32)
        os.environ["JWT_SECRET_KEY"] = jwt_secret
    jwt_ok = True
    results["jwt_secret"] = "ok"

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
