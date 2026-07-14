"""
routers/api_v2.py - API V2 Router (FastAPI APIRouter)
Extracted from app_v2.py
"""
import logging
import os
import sys
import time
from datetime import datetime

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["api-v2"])

def _deps():
    from web.app_v2 import get_campaign_stats, get_payment_addresses
    from web.shared import config, get_db, get_verified_user_id
    return get_db, get_verified_user_id, config, get_campaign_stats, get_payment_addresses


@router.get("/api/v2/campaign/track/{campaign_id}")
def campaign_track(campaign_id: int):
    """Tracking pixel — 1x1 transparent GIF, updates opened_at timestamp."""
    get_db, _, _, _, _ = _deps()
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE email_campaign_log SET opened_at = CURRENT_TIMESTAMP WHERE id = ? AND opened_at IS NULL",
                (campaign_id,)
            )
            conn.commit()
            pass  # conn.close()
    except Exception as e:
        logger.error(e, exc_info=True)
    # Return 1x1 transparent GIF (43 bytes)
    return Response(
        content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b',
        media_type="image/gif"
    )


@router.get("/api/v2/campaigns/stats")
def campaign_stats_api():
    """Return aggregated campaign statistics."""
    _, _, _, get_campaign_stats, _ = _deps()
    try:
        stats = get_campaign_stats()
        return stats
    except Exception as e:
        logger.warning(f"Error fetching campaign stats: {e}")
        return {
            "total_sent": 0,
            "total_opened": 0,
            "open_rate": 0,
            "campaigns": {"welcome": 0, "abandoned_cart": 0, "re_engagement": 0, "post_purchase": 0},
            "error": str(e)
        }


# Request dedup cache for cloud-tick
_tick_cache: dict = {"last_tick": 0, "last_result": None, "pending": False}
import asyncio

_tick_cache_lock = None

@router.post("/api/v2/cloud-tick")
async def cloud_tick_endpoint(request: Request):
    """Multi-tenant cloud tick - runs campaigns for ALL users in parallel."""
    from web.app_v2 import verify_system_key
    verify_system_key(request)

    global _tick_cache_lock, _tick_cache
    if _tick_cache_lock is None:
        _tick_cache_lock = asyncio.Lock()

    get_db, _, _, _, _ = _deps()
    company_limit = 10
    force = False
    try:
        body = await request.json()
        company_limit = body.get("company_limit", 10)
        force = body.get("force", False)
    except Exception:
        pass

    async with _tick_cache_lock:
        now = time.time()
        if not force and _tick_cache.get("last_result") and (now - _tick_cache.get("last_tick", 0)) < 60:
            logger.info("[CloudTick] 📦 Returning cached result (dedup)")
            return _tick_cache["last_result"]
        if _tick_cache.get("pending"):
            logger.info("[CloudTick] 🔄 Tick already in progress, returning pending")
            return {"status": "pending", "message": "Tick already running", "cached": True}
        _tick_cache["pending"] = True

    try:
        from core.multi_tenant import MultiTenantRunner
        runner = MultiTenantRunner(company_limit=company_limit)
        result = await runner.tick()

        compact = {
            "status": result.get("status", "ok"),
            "tenants": result.get("tenant_count", 0),
            "campaigns": result.get("campaigns_processed", 0),
            "sent": result.get("emails_sent", 0),
            "errors": result.get("errors", 0),
            "elapsed": result.get("elapsed_sec", 0),
            "version": "v17.1-optimized",
        }

        async with _tick_cache_lock:
            _tick_cache["last_tick"] = time.time()
            _tick_cache["last_result"] = compact
            _tick_cache["pending"] = False

        return compact
    except ImportError:
        logger.warning("MultiTenantRunner not available, falling back")
        try:
            from cloud_orchestrator import CloudOrchestrator
            orch = CloudOrchestrator()
            result = await orch.tick()
            compact = {
                "status": result.get("status", "error"),
                "tenants": result.get("tenant_count", 0),
                "campaigns": result.get("campaigns_processed", 0),
                "sent": result.get("emails_sent", 0),
                "errors": result.get("errors", 0),
                "elapsed": result.get("elapsed_sec", 0),
                "version": "v17.1-optimized",
            }
            async with _tick_cache_lock:
                _tick_cache["last_tick"] = time.time()
                _tick_cache["last_result"] = compact
                _tick_cache["pending"] = False
            return compact
        except Exception as e:
            async with _tick_cache_lock:
                _tick_cache["pending"] = False
            return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"cloud-tick: {e}")
        async with _tick_cache_lock:
            _tick_cache["pending"] = False
        return {"status": "error", "error": str(e)}


@router.get("/api/v2/cloud-tick/status")
def cloud_tick_status():
    return {
        "status": "ok",
        "pa_token": bool(os.getenv("PA_API_TOKEN")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "time": datetime.now().isoformat(),
        "version": "v17.1-optimized"
    }


@router.get("/api/v2/services")
def api_v2_services():
    from services.catalog import SERVICE_CATALOG
    return {"success": True, "services": SERVICE_CATALOG}


@router.get("/api/v2/services/grouped")
def api_v2_services_grouped():
    from services.catalog import SERVICE_CATALOG
    grouped = {}
    for s in SERVICE_CATALOG:
        cat = s.get("category", "general")
        grouped.setdefault(cat, []).append(s)
    return {"success": True, "grouped": grouped}


@router.get("/api/v2/stats")
def api_v2_stats():
    get_db, _, _, _, _ = _deps()
    with get_db() as conn:
        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_campaigns = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        total_emails = conn.execute("SELECT COUNT(*) FROM campaign_emails").fetchone()[0]
        pass  # conn.close()
        return {
            "success": True,
            "users": total_users,
            "campaigns": total_campaigns,
            "emails": total_emails,
            "uptime_sec": int(time.time() - getattr(sys, "_app_start_time", time.time()))
        }


@router.get("/api/v2/earnings")
def api_v2_earnings(request: Request):
    get_db, get_verified_user_id, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    with get_db() as conn:
        earnings = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions WHERE user_id = ? AND transaction_type = 'referral_bonus'",
            (user_id,)
        ).fetchone()[0]
        pass  # conn.close()
        return {"success": True, "earnings_usd": float(earnings)}
