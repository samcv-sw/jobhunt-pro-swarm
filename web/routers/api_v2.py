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


@router.get("/api/v2/campaign/track/{tracking_id}")
def campaign_track(tracking_id: str):
    """Tracking pixel — 1x1 transparent GIF, updates opened_at in campaign_emails and email_campaign_log."""
    get_db, _, _, _, _ = _deps()
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE campaign_emails SET opened_at = CURRENT_TIMESTAMP WHERE (tracking_id = ? OR id = ? OR id = CAST(? AS INTEGER)) AND opened_at IS NULL",
                (str(tracking_id), str(tracking_id), str(tracking_id))
            )
            try:
                try:
                    tid_val = int(tracking_id)
                except (ValueError, TypeError):
                    tid_val = tracking_id
                conn.execute(
                    "UPDATE email_campaign_log SET opened_at = CURRENT_TIMESTAMP WHERE id = ? OR id = ?",
                    (str(tracking_id), tid_val)
                )
            except Exception as ex:
                logger.error(f"[campaign_track] email_campaign_log update error: {ex}")
            conn.commit()
    except Exception as e:
        logger.error(f"[campaign_track] Tracking pixel error for {tracking_id}: {e}")
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
        }


# Request dedup cache for cloud-tick
_tick_cache: dict = {"last_tick": 0, "last_result": None, "pending": False}
import asyncio

_tick_cache_lock = None

async def _execute_tick_in_bg(company_limit: int):
    try:
        try:
            from web.cloud_tick_router import reset_stuck_campaigns
            await reset_stuck_campaigns()
        except Exception as re_err:
            logger.debug(f"[CloudTick BG] Reset stuck error: {re_err}")

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
            "version": "v1",
        }
        async with _tick_cache_lock:
            _tick_cache["last_tick"] = time.time()
            _tick_cache["last_result"] = compact
            _tick_cache["pending"] = False
    except Exception as e:
        logger.error(f"[CloudTick BG Error] {e}")
        async with _tick_cache_lock:
            _tick_cache["pending"] = False


@router.post("/api/v2/cloud-tick")
async def cloud_tick_endpoint(request: Request):
    """Multi-tenant cloud tick - dispatches campaigns asynchronously in background task."""
    from web.app_v2 import verify_system_key
    verify_system_key(request)
    global _tick_cache_lock, _tick_cache
    if _tick_cache_lock is None:
        _tick_cache_lock = asyncio.Lock()

    company_limit = 3
    force = False
    try:
        body = await request.json()
        company_limit = body.get("company_limit", 3)
        force = body.get("force", False)
    except Exception:
        pass

    async with _tick_cache_lock:
        now = time.time()
        if force:
            _tick_cache["pending"] = False
        else:
            if _tick_cache.get("last_result") and (now - _tick_cache.get("last_tick", 0)) < 60:
                logger.info("[CloudTick] 📦 Returning cached result (dedup)")
                return _tick_cache["last_result"]
            if _tick_cache.get("pending"):
                logger.info("[CloudTick] 🔄 Tick already in progress, returning pending")
                return {"status": "pending", "message": "Tick already running", "sent": 0, "cached": True}
        _tick_cache["pending"] = True

    asyncio.create_task(_execute_tick_in_bg(company_limit))
    return {
        "status": "processing",
        "message": "Cloud tick dispatched in background",
        "sent": 0,
        "cached": False
    }


@router.get("/api/v2/cloud-tick/status")
def cloud_tick_status():
    from web.shared import config
    return {
        "status": "ok",
        "pa_token": bool(getattr(config, "PA_API_TOKEN", "")),
        "groq": bool(getattr(config, "GROQ_API_KEY", "")),
        "time": datetime.now().isoformat(),
        "version": "v1"
    }


@router.get("/api/v2/services")
def api_v2_services():
    from services.catalog import SERVICE_CATALOG, BOUQUET_CATALOG
    return {"success": True, "services": SERVICE_CATALOG, "bouquets": BOUQUET_CATALOG}


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
        try:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        except Exception:
            total_users = 0
        try:
            total_campaigns = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        except Exception:
            total_campaigns = 0
        try:
            total_emails = conn.execute("SELECT COUNT(*) FROM campaign_emails").fetchone()[0]
        except Exception:
            total_emails = 0
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
        return {"success": True, "earnings_usd": 0.0, "authenticated": False}
    with get_db() as conn:
        earnings = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM wallet_transactions WHERE user_id = ? AND transaction_type = 'referral_bonus'",
            (user_id,)
        ).fetchone()[0]
        return {"success": True, "earnings_usd": float(earnings), "authenticated": True}


@router.get("/api/v2/og-image/{card_id}")
def api_v2_og_image(card_id: str, title: str = "Verified Candidate Profile", subtitle: str = "JobHunt Pro Autopoietic Match", score: int = 98):
    """Returns dynamic SVG OpenGraph card for social sharing."""
    from backend.og_card_generator import generate_og_card_svg
    svg_data = generate_og_card_svg(title=title, subtitle=subtitle, score=score)
    return Response(content=svg_data, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})


@router.get("/api/v2/multi-llm/health")
def api_v2_multi_llm_health():
    """Returns health and latency stats for multi-LLM dynamic router."""
    from backend.multi_llm_router import llm_router
    return {"success": True, "providers": llm_router.get_provider_health()}

