"""JobHunt Pro — Health & Telemetry Routers.

Aggregates root metadata, health checks, healthz, and telemetry endpoints.
"""

import logging
import os
import time
import gc
import asyncio
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi_cache.decorator import cache

from backend.auth import verify_jwt
from backend.database import async_session
from backend.models import User
from sqlalchemy import func, select

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


# ---------------------------------------------------------------------------
# Root metadata
# ---------------------------------------------------------------------------
@router.get("/")
async def root(request: Request = None) -> dict[str, str]:
    """Return service metadata."""
    return {
        "service": "JobHunt Pro",
        "version": os.getenv("RELEASE_VERSION", "3.0.0"),
        "status": "operational",
    }


# ---------------------------------------------------------------------------
# Aggregate platform stats (landing dashboard)
# ---------------------------------------------------------------------------
@router.get("/api/v1/stats", dependencies=[Depends(verify_jwt)])
async def get_stats(request: Request = None) -> dict[str, Any]:
    """Return aggregate platform stats for the landing dashboard — IMP-227."""
    users = 0
    try:
        async with async_session() as session:
            result = await session.execute(select(func.count()).select_from(User))
            users = result.scalar() or 0
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Stats query failed, returning defaults: %s", exc)

    return {
        "success": True,
        "users": users,
        "campaigns": 0,
        "emails": 0,
    }


# ---------------------------------------------------------------------------
# Simple health checks (no DB dependency)
# ---------------------------------------------------------------------------
@router.get("/health")
async def health_check(request: Request = None) -> dict[str, str]:
    """Lightweight health check for load balancers."""
    return {"status": "ok"}


@router.get("/healthz")
async def healthz(request: Request = None) -> dict[str, str]:
    """Minimal health probe for Render / K8s."""
    return {"status": "ok"}


@router.get("/api/v1/health")
async def health_v1(request: Request = None) -> dict[str, str]:
    """API v1 health endpoint."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Detailed health  (cached 15 s)
# ---------------------------------------------------------------------------
@router.get("/api/v1/health/detailed")
@cache(expire=15)
async def health_detailed(request: Request = None) -> dict[str, Any]:
    """Detailed health check: reports DB, Redis, SMTP, and Groq API status."""
    import time
    result: dict[str, Any] = {"status": "ok", "components": {}}

    # Check DB
    db_start = time.monotonic()
    try:
        async with async_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        result["components"]["db"] = {"status": "ok", "latency_ms": round((time.monotonic() - db_start) * 1000, 2)}
    except Exception as e:
        result["components"]["db"] = {"status": "error", "detail": str(e)}
        result["status"] = "degraded"

    # Check Redis
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        r_start = time.monotonic()
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(redis_url, socket_timeout=3)
            await r.ping()
            await r.aclose()
            result["components"]["redis"] = {"status": "ok", "latency_ms": round((time.monotonic() - r_start) * 1000, 2)}
        except Exception as e:
            result["components"]["redis"] = {"status": "error", "detail": str(e)}
            result["status"] = "degraded"
    else:
        result["components"]["redis"] = {"status": "not_configured"}

    # Check SMTP
    smtp_host = os.getenv("SMTP_HOST") or os.getenv("BREVO_SMTP_HOST")
    if smtp_host:
        smtp_start = time.monotonic()
        try:
            from contextlib import suppress
            smtp_port = int(os.getenv("SMTP_PORT") or os.getenv("BREVO_SMTP_PORT") or "587")
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(smtp_host, smtp_port),
                timeout=0.9,
            )
            writer.close()
            with suppress(Exception):
                await writer.wait_closed()
            result["components"]["smtp"] = {
                "status": "ok",
                "host": smtp_host,
                "port": smtp_port,
                "latency_ms": round((time.monotonic() - smtp_start) * 1000, 2),
            }
        except asyncio.TimeoutError:
            result["components"]["smtp"] = {
                "status": "timeout",
                "host": smtp_host,
                "detail": "TCP connection timed out (<1s)",
            }
            result["status"] = "degraded"
        except Exception as e:
            result["components"]["smtp"] = {
                "status": "error",
                "host": smtp_host,
                "detail": str(e),
            }
            result["status"] = "degraded"
    else:
        result["components"]["smtp"] = {"status": "not_configured"}

    # Check Groq API
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        groq_start = time.monotonic()
        try:
            import httpx
            async with httpx.AsyncClient(timeout=0.9) as client:
                resp = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {groq_key}"}
                )
            groq_status = "ok" if resp.status_code in (200, 401) else "error"
            result["components"]["groq_api"] = {
                "status": groq_status,
                "http_status": resp.status_code,
                "latency_ms": round((time.monotonic() - groq_start) * 1000, 2),
            }
            if groq_status == "error":
                result["status"] = "degraded"
        except httpx.TimeoutException:
            result["components"]["groq_api"] = {
                "status": "timeout",
                "detail": "HTTP probe timed out (<1s)",
            }
            result["status"] = "degraded"
        except Exception as e:
            result["components"]["groq_api"] = {"status": "error", "detail": str(e)}
            result["status"] = "degraded"
    else:
        result["components"]["groq_api"] = {"status": "not_configured"}

    return result


# ---------------------------------------------------------------------------
# Telemetry  (JWT required)
# ---------------------------------------------------------------------------
@router.get(
    "/api/v1/telemetry",
    dependencies=[Depends(verify_jwt)],
)
async def get_telemetry(request: Request = None) -> dict:
    """Return process-level telemetry (memory, CPU, etc.)."""
    import threading
    import time as _time
    import backend.main as main_mod
    
    start_time = getattr(main_mod, "_APP_START_TIME", 0.0)
    uptime = _time.monotonic() - start_time if start_time else 0.0

    rss_mb = 0.0
    open_fds = -1
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        mem_info = proc.memory_info()
        rss_mb = round(mem_info.rss / (1024 * 1024), 2)
        try:
            open_fds = proc.num_fds()
        except AttributeError:
            try:
                open_fds = proc.num_handles()
            except Exception:
                open_fds = -1
    except ImportError:
        pass

    gc_stats = gc.get_count()
    thread_count = threading.active_count()

    return {
        "uptime_seconds": round(uptime, 2),
        "rss_mb": rss_mb,
        "thread_count": thread_count,
        "gc_stats": {
            "counts": gc_stats,
            "threshold": gc.get_threshold(),
        },
        "open_fds": open_fds,
    }
