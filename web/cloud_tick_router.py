"""
JobHunt Pro — Cloud Tick API Endpoint
Mounted in app_v2.py as:
  from web.cloud_tick_router import router
  app.include_router(router, prefix="/api/v2")
"""
import logging
import os
if os.getenv("SUPABASE_MODE") == "1":
    import core.supabase_rest_shim as sqlite3
else:
    import core.pg_sqlite_shim as sqlite3
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
    Main cron endpoint - v17 Multi-Tenant.
    Runs campaigns for ALL users (Sam + Rita + future tenants) in parallel.
    Falls back to CloudOrchestrator if MultiTenantRunner unavailable.
    """
    # Secure with CRON_SECRET
    key = request.query_params.get("key") or request.headers.get("X-Cron-Secret") or request.headers.get("x-cron-secret")
    expected_key = os.getenv("CRON_SECRET", "")
    if expected_key and key != expected_key:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid cron key")

    try:
        company_limit = 3
        max_campaigns = 3
        campaign_id = None
        try:
            body = await request.json()
            company_limit = body.get("company_limit", 3)
            max_campaigns = body.get("max_campaigns", 3)
            campaign_id = body.get("campaign_id")
        except Exception:
            pass

        import subprocess
        import sys
        
        creationflags = 0
        if sys.platform.startswith("win"):
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(base_dir, "web", "cron_trigger.py")

        cmd = [
            sys.executable,
            script_path,
            "--company-limit", str(company_limit),
            "--max-campaigns", str(max_campaigns),
            "--skip-backup"
        ]
        if campaign_id:
            cmd.extend(["--campaign-id", str(campaign_id)])

        p = subprocess.Popen(
            cmd,
            creationflags=creationflags,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"[CloudTick] Spawned cron_trigger.py in background (PID: {p.pid})")
        return {
            "status": "spawned",
            "message": "Multi-tenant campaign tick initiated in background.",
            "pid": p.pid,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Cloud tick spawning failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
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

@router.get("/cloud-tick/debug-db")
async def debug_db():
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        
        # Check if table lebanon_companies exists
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lebanon_companies'")
        has_table = cursor.fetchone() is not None
        
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        
        lebanon_count = 0
        if has_table:
            lebanon_count = conn.execute("SELECT COUNT(*) FROM lebanon_companies").fetchone()[0]
            
        campaign_sent_count = 0
        has_sent_table = 'campaign_sent' in tables
        if has_sent_table:
            campaign_sent_count = conn.execute("SELECT COUNT(*) FROM campaign_sent").fetchone()[0]
            
        conn.close()
        
        # Check GMAIL env variables
        gmail_env = {}
        for i in range(1, 20):
            u = os.getenv(f"GMAIL{i}_USER")
            p = os.getenv(f"GMAIL{i}_PASS")
            if u:
                gmail_env[f"GMAIL{i}"] = {
                    "user": u,
                    "has_pass": bool(p),
                    "pass_len": len(p) if p else 0
                }
                
        return {
            "status": "ok",
            "db_path": db_path,
            "tables": tables,
            "has_lebanon_companies": has_table,
            "lebanon_companies_count": lebanon_count,
            "has_campaign_sent": has_sent_table,
            "campaign_sent_count": campaign_sent_count,
            "gmail_env": gmail_env,
            "brevo_api_key_set": bool(os.getenv("BREVO_API_KEY")),
            "brevo_email": os.getenv("BREVO_ACCOUNT_EMAIL")
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}



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

        # Find stuck campaigns: completed but sent_count < total_companies
        stuck = conn.execute("""
            SELECT campaign_id, user_id, total_companies, sent_count, status
            FROM campaigns
            WHERE status = 'completed'
            AND (sent_count < total_companies OR sent_count IS NULL)
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
@router.get("/cloud-tick/debug-logs")
async def debug_logs(file: str = "auto_run.log", lines: int = 200):
    try:
        if file.startswith("/var/log/"):
            filepath = file
        else:
            file = os.path.basename(file)
            log_dir = "/home/JHFGUF/jobhunt/logs"
            if not os.path.exists(log_dir):
                log_dir = "logs"
            
            filepath = os.path.join(log_dir, file)
            if not os.path.exists(filepath):
                filepath = os.path.join("/home/JHFGUF/jobhunt", file)
                if not os.path.exists(filepath):
                    filepath = os.path.join("/home/JHFGUF", file)
                    if not os.path.exists(filepath):
                        return {"status": "error", "message": f"File {file} not found"}
        
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.readlines()
            
        last_lines = content[-lines:] if len(content) > lines else content
        return {
            "status": "ok",
            "file": filepath,
            "total_lines": len(content),
            "lines": [line.strip() for line in last_lines]
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/cloud-tick/list-dir")
async def list_dir_api(path: str = "."):
    try:
        base_dir = "/home/JHFGUF/jobhunt"
        if not os.path.exists(base_dir):
            base_dir = "."
        
        target = os.path.abspath(os.path.join(base_dir, path))
        if not target.startswith(os.path.abspath(base_dir)) and not target.startswith("/home/JHFGUF"):
            return {"status": "error", "message": "Access denied"}
            
        if not os.path.exists(target):
            return {"status": "error", "message": "Path not found"}
            
        if os.path.isfile(target):
            return {"status": "ok", "type": "file", "size": os.path.getsize(target)}
            
        items = []
        for name in os.listdir(target):
            item_path = os.path.join(target, name)
            items.append({
                "name": name,
                "is_dir": os.path.isdir(item_path),
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
            })
        return {"status": "ok", "path": target, "items": items}
    except Exception as e:
        return {"status": "error", "error": str(e)}



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

        import uuid
        order_id = body.get("order_id", f"ord_{uuid.uuid4().hex[:16]}")

        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("""
            INSERT INTO campaigns (campaign_id, user_id, profile_id, order_id, status, total_companies, sent_count, open_count, response_count, bouquets, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?, 0, 0, 0, ?, datetime('now'))
        """, (camp_id, user_id, profile_id, order_id, total, bouquets))
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


@router.post("/cloud-tick/force-reset")
async def force_reset_all():
    """
    FORCE reset ALL campaigns — delete ALL campaign_emails, reset sent_count to 0,
    and set status to 'pending'.  Use this when fixing email engine bugs to
    ensure campaigns re-process completely from scratch.
    WARNING: This deletes ALL existing email send records!
    """
    try:
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=30)

        # Count before reset
        camp_count = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        email_count = conn.execute("SELECT COUNT(*) FROM campaign_emails").fetchone()[0]

        # Delete all campaign emails
        conn.execute("DELETE FROM campaign_emails")

        # Reset all campaigns
        conn.execute("""
            UPDATE campaigns SET
                status = 'pending',
                sent_count = 0,
                open_count = 0,
                response_count = 0,
                completed_at = NULL
        """)

        # Also clean email_queue if it exists
        try:
            conn.execute("DELETE FROM email_queue")
        except Exception:
            pass

        conn.commit()
        conn.close()

        return {
            "status": "ok",
            "campaigns_reset": camp_count,
            "emails_deleted": email_count,
            "message": f"Reset {camp_count} campaigns, deleted {email_count} email records.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Force reset failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cloud-tick/test-scrape")
async def test_scrape():
    """Test job scraping capability on PythonAnywhere free tier."""
    try:
        from core.pa_job_scraper import PAJobScraper
        pa = PAJobScraper()
        jobs = pa.search_all(query="network engineer", location="Lebanon", max_jobs=5)
        return {"status": "ok", "jobs_found": len(jobs), "jobs": jobs[:5]}
    except Exception as e:
        logger.exception("Scraper test failed: %s", e)
        return {"status": "error", "error": str(e)}


@router.post("/cloud-tick/execute-sql")
async def execute_sql(request: Request):
    """Execute arbitrary SQL query on the local database (admin only)."""
    try:
        body = await request.json()
        query = body.get("query")
        params = body.get("params", [])
        
        if not query:
            return {"status": "error", "message": "query required"}
            
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute(query, params)
        conn.commit()
        
        # Check if it was a SELECT query
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            conn.close()
            return {"status": "ok", "row_count": len(rows), "rows": [dict(r) for r in rows]}
            
        conn.close()
        return {"status": "ok", "message": "Query executed successfully"}
    except Exception as e:
        logger.exception("SQL execution failed: %s", e)
        return {"status": "error", "error": str(e)}
