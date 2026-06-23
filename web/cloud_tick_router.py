"""
JobHunt Pro — Cloud Tick API Endpoint
Add this route to web/app_v2.py to enable GH Actions cron.
"""
import json
import logging
from datetime import datetime
from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

# This router should be mounted in app_v2.py as:
# from cloud_tick_router import router
# app.include_router(router, prefix="/api/v2")

router = APIRouter(tags=["cloud-tick"])


@router.post("/cloud-tick")
async def cloud_tick_handler(request: Request):
    """
    Main cron endpoint called by GH Actions every 15 min.
    Runs CloudOrchestrator.tick() and returns status.
    """
    try:
        # Import and run cloud orchestrator
        from cloud_orchestrator import CloudOrchestrator
        orch = CloudOrchestrator()
        result = await orch.tick()
        return result
    except Exception as e:
        logger.error(f"Cloud tick failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "partial": {"db": False, "campaigns": 0, "emails": 0}
        }


@router.get("/cloud-tick/status")
async def cloud_tick_status():
    """Quick health check for the tick system itself."""
    import os
    return {
        "status": "ok",
        "pa_token": bool(os.getenv("PA_API_TOKEN")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "nowpayments": bool(os.getenv("NOWPAYMENTS_API_KEY")),
        "time": datetime.now().isoformat(),
        "version": "v2.0"
    }
