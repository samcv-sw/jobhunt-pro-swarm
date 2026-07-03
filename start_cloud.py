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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cloud-start")

PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")
WORKERS = int(os.environ.get("WEB_CONCURRENCY", 1)) # Keep at 1 for free tier memory limits
processes = []

def cleanup(signum, frame):
    logger.info("Shutting down all services...")
    for p in processes:
        p.terminate()
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
        "--loop", "uvloop",
        "--access-log",
    ]
    uvicorn_proc = subprocess.Popen(uvicorn_cmd)
    processes.append(uvicorn_proc)

    # Keep script alive and monitor processes
    try:
        while True:
            time.sleep(1)
            for p in processes:
                if p.poll() is not None:
                    logger.error("A critical background service crashed! Shutting down container...")
                    cleanup(None, None)
    except KeyboardInterrupt:
        cleanup(None, None)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    launch_services()
