"""
routers/system.py - System and Multi-Tenant Router (FastAPI APIRouter)
"""
import logging
import os
import sys
import time

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])

def _deps():
    from web.app_v2 import APP_START_TIME, verify_system_key
    from web.shared import config, get_db, get_verified_user_id, is_admin_email
    return get_db, get_verified_user_id, is_admin_email, config, verify_system_key, APP_START_TIME

@router.get("/api/system/status")
def system_status(request: Request):
    """
    Full system status — RAM, CPU, running campaigns, SMTP health, API keys.
    Uses auto_heal.get_system_health_snapshot() for comprehensive health view.
    """
    get_db_fn, _, _, _, verify_system_key_fn, app_start_time = _deps()
    verify_system_key_fn(request)
    from core import auto_heal as _autoheal
    try:
        snapshot = _autoheal.get_system_health_snapshot()
    except Exception as e:
        logger.error(f"Error generating system health snapshot: {e}", exc_info=True)
        snapshot = {"status": "error", "message": str(e)}

    # Inject server uptime and metadata
    snapshot["server"] = {
        "uptime_seconds": round(time.time() - app_start_time, 1),
        "uptime_human": f"{int((time.time() - app_start_time) / 3600)}h {int(((time.time() - app_start_time) % 3600) / 60)}m",
        "host": os.getenv("HOSTNAME", "PA"),
        "python_version": sys.version.split()[0] if hasattr(sys, 'version') else "unknown",
        "platform": sys.platform,
    }

    return snapshot

@router.post("/api/system/auto-heal")
async def trigger_auto_heal(request: Request):
    """
    Trigger a self-healing cycle manually or via GH Actions.
    Accepts optional JSON body: {"source": "gh-actions", "force": false}
    """
    _, _, _, _, verify_system_key_fn, _ = _deps()
    verify_system_key_fn(request)
    try:
        data = await request.json()
    except Exception:
        data = {}

    force = data.get("force", False)
    if isinstance(force, str):
        force = force.lower() in ("true", "1", "yes")

    source = data.get("source", "manual")
    from core import auto_heal as _autoheal
    try:
        result = await _autoheal.run_heal_cycle(force=force)

        return {
            "status": "ok",
            "source": source,
            "force": force,
            "result": result,
        }
    except Exception as e:
        logger.error(f"auto-heal trigger failed: {e}", exc_info=True)
        return {
            "status": "error",
            "source": source,
            "error": str(e),
        }

@router.get("/api/multi-tenant/demo_user")
def demo_user_status(request: Request):
    """Get Demo User's profile and stats."""
    _, _, _, _, verify_system_key_fn, _ = _deps()
    verify_system_key_fn(request)
    try:
        from core.multi_tenant import TenantManager
        return TenantManager.get_tenant_stats("demo_useruser2@gmail.com")
    except ImportError:
        return {"status": "error", "error": "multi_tenant module not loaded"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/api/system/seed-companies")
def seed_companies(request: Request):
    """Seed Lebanon company database on PA."""
    _, _, _, _, verify_system_key_fn, _ = _deps()
    verify_system_key_fn(request)
    try:
        from core.lebanon_company_seeder import seed_all_companies
        result = seed_all_companies()
        return result
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/api/system/companies-count")
def companies_count(request: Request):
    _, _, _, _, verify_system_key_fn, _ = _deps()
    verify_system_key_fn(request)
    try:
        from core.lebanon_company_seeder import get_companies_count
        return get_companies_count()
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/api/system/force-demo-campaign")
def force_demo_campaign(request: Request):
    _, _, _, _, verify_system_key_fn, _ = _deps()
    verify_system_key_fn(request)
    try:
        from scripts.force_demo_campaign import force_demo_user_campaign as fdc
        return fdc()
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/api/system/force-reset-all")
def force_reset_all(request: Request):
    """Reset ALL completed campaigns to pending for both tenants."""
    _, _, _, _, verify_system_key_fn, _ = _deps()
    verify_system_key_fn(request)
    try:
        from scripts.force_reset_all import force_reset_all_campaigns
        return force_reset_all_campaigns()
    except Exception as e:
        return {"status": "error", "error": str(e)}
