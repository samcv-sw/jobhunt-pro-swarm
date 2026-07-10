#!/usr/bin/env python3
"""
JobHunt Pro - Zero Cost Enterprise Cloud Startup Script
Runs FastAPI, Celery Worker, and Database Sync Worker in a SINGLE container.
This ensures you only consume 1 Free Tier instance on platforms like Render.
"""
import os
import sys
import time
import subprocess
import logging
import signal

import json as _json

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
processes = []

def cleanup(signum, frame):
    """Handle SIGINT/SIGTERM: gracefully terminate all child processes and exit."""
    logger.info("Shutting down all services...")
    for p in processes:
        try:
            p.terminate()
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
        celery_cmd = ["celery", "-A", "backend.tasks", "worker", "--loglevel=info", "--concurrency=2"]
        celery_proc = subprocess.Popen(celery_cmd)
        processes.append(celery_proc)
    else:
        logger.warning("REDIS_URL not set. Background tasks (Scraping/Emails) will fail.")

    # 2. Start Sync Worker (Background process)
    logger.info("Starting Database Sync Worker...")
    sync_proc = subprocess.Popen([sys.executable, "-m", "backend.sync_worker"])
    processes.append(sync_proc)

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
    processes.append(uvicorn_proc)

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

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    launch_services()
