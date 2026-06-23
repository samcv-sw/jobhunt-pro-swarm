"""
JobHunt Pro — Cloud Tick API Endpoint
Mounted in app_v2.py as:
  from web.cloud_tick_router import router
  app.include_router(router, prefix="/api/v2")
"""
import json
import logging
import os
import sqlite3
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cloud-tick"])


def _get_db_path():
    db_path = os.getenv("DB_PATH", "jobhunt_saas_v2.db")
    if not os.path.exists(db_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base, "jobhunt_saas_v2.db")
    return db_path


@router.post("/cloud-tick")
async def cloud_tick_handler(request: Request):
    """
    Main cron endpoint called by GH Actions every 15 min.
    Runs CloudOrchestrator.tick() and returns status.
    """
    try:
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
    return {
        "status": "ok",
        "pa_token": bool(os.getenv("PA_API_TOKEN")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
        "dry_run": os.getenv("DRY_RUN", "false"),
        "time": datetime.now().isoformat(),
        "version": "v2.1"
    }


@router.post("/cloud-tick/reset-stuck")
async def reset_stuck_campaigns():
    """
    Reset all 'completed' campaigns that have 0 sent_count back to 'pending'
    so they can be re-processed by the next cloud tick.
    This fixes campaigns that got stuck because DRY_RUN was accidentally enabled.
    """
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row

        # Find stuck campaigns: completed but sent_count = 0
        stuck = conn.execute("""
            SELECT campaign_id, user_id, total_companies, sent_count, status
            FROM campaigns
            WHERE status = 'completed'
            AND (sent_count = 0 OR sent_count IS NULL)
            AND total_companies > 0
        """).fetchall()

        reset_ids = []
        for row in stuck:
            cid = dict(row)["campaign_id"]
            conn.execute(
                "UPDATE campaigns SET status='pending', completed_at=NULL WHERE campaign_id=?",
                (cid,)
            )
            reset_ids.append(cid)

        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "reset_count": len(reset_ids),
            "campaigns": reset_ids,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Reset stuck failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud-tick/campaigns")
async def list_campaigns():
    """List all campaigns with their status and sent counts."""
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT campaign_id, user_id, status, total_companies, sent_count,
                   open_count, response_count, created_at, completed_at
            FROM campaigns
            ORDER BY created_at DESC
            LIMIT 50
        """).fetchall()
        conn.close()
        return {"campaigns": [dict(r) for r in rows], "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cloud-tick/retry-all")
async def retry_all_completed_campaigns():
    """
    Reset ALL completed campaigns back to 'pending' so the next cloud tick
    re-processes them.  Use this after fixing email engine bugs to re-send
    emails for campaigns that completed with 0 or few sends.
    """
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT campaign_id FROM campaigns
            WHERE status = 'completed'
        """).fetchall()

        ids = [r["campaign_id"] for r in rows]
        if ids:
            placeholders = ",".join("?" * len(ids))
            conn.execute(
                f"UPDATE campaigns SET status='pending', completed_at=NULL WHERE campaign_id IN ({placeholders})",
                ids
            )
            conn.commit()

        conn.close()
        return {
            "status": "ok",
            "reset_count": len(ids),
            "campaigns": ids,
            "message": "All completed campaigns reset to pending. Next cloud-tick will process them.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Retry-all failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cloud-tick/create-campaign")
async def create_quick_campaign(request: Request):
    """
    Create a new campaign via API (no browser needed).
    Body JSON: {"user_id": "admin-xxx", "profile_id": 1, "bouquets": "network_engineer_lebanon"}
    """
    try:
        body = await request.json()
        user_id = body.get("user_id")
        profile_id = body.get("profile_id", 1)
        bouquets = body.get("bouquets", "network_engineer_lebanon")
        total = body.get("total_companies", 100)

        if not user_id:
            raise HTTPException(400, "user_id required")

        import uuid
        camp_id = f"camp_{uuid.uuid4().hex[:12]}"

        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("""
            INSERT INTO campaigns (campaign_id, user_id, profile_id, status, total_companies, sent_count, open_count, response_count, bouquets, created_at)
            VALUES (?, ?, ?, 'pending', ?, 0, 0, 0, ?, datetime('now'))
        """, (camp_id, user_id, profile_id, total, bouquets))
        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "campaign_id": camp_id,
            "message": f"Campaign created with {total} companies. Cloud-tick will process it.",
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create campaign failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
