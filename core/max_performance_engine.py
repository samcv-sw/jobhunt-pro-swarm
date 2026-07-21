import time
import os
import sys
import psutil
import logging
from datetime import datetime, timezone

logger = logging.getLogger("max_performance_engine")

_START_TIME = time.time()
_REQUEST_COUNTER = 0

def record_request():
    """Increment internal request counter for RPS metrics."""
    global _REQUEST_COUNTER
    _REQUEST_COUNTER += 1

def get_system_telemetry() -> dict:
    """Return real-time performance, uptime, memory, and environment metrics."""
    uptime_seconds = round(time.time() - _START_TIME, 2)
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    rps = round(_REQUEST_COUNTER / max(uptime_seconds, 1), 2)
    
    return {
        "status": "healthy",
        "uptime_seconds": uptime_seconds,
        "uptime_human": f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m {int(uptime_seconds % 60)}s",
        "total_requests": _REQUEST_COUNTER,
        "avg_rps": rps,
        "memory": {
            "rss_mb": round(memory_info.rss / (1024 * 1024), 2),
            "vsz_mb": round(memory_info.vms / (1024 * 1024), 2),
        },
        "python_version": sys.version.split()[0],
        "pid": os.getpid(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }

def apply_db_performance_pragmas(conn):
    """Apply high-performance SQLite PRAGMAs for fast zero-lock concurrency and zero table locks."""
    try:
        if hasattr(conn, "execute"):
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            conn.execute("PRAGMA temp_store=MEMORY;")
            conn.execute("PRAGMA cache_size=-64000;")
            conn.execute("PRAGMA mmap_size=30000000000;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute("PRAGMA foreign_keys=ON;")
    except Exception as e:
        logger.debug(f"SQLite PRAGMA tuning skipped: {e}")

