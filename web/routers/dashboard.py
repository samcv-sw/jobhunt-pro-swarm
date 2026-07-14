"""
routers/dashboard.py - Dashboard Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])

def _deps():
    from web.shared import config, get_db, get_verified_user_id, templates
    return get_db, get_verified_user_id, templates, config

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/user-dashboard", status_code=302)

@router.get("/api/dashboard/stats")
def dashboard_stats(request: Request):
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        with get_db() as conn:
            row_camp = conn.execute(
                "SELECT "
                "COALESCE(SUM(sent_count), 0), "
                "COALESCE(SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END), 0), "
                "COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) "
                "FROM campaigns WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            row4 = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()

            ts = row_camp[0] if row_camp else 0
            act = row_camp[1] if row_camp else 0
            cmp = row_camp[2] if row_camp else 0
            bal = (row4[0] if not hasattr(row4, "__getitem__") else row4["wallet_balance"]) if row4 else 0.0
    except Exception as e:
        logger.error(f"Database error in dashboard_stats: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")

    return JSONResponse({
        "total_sent": ts,
        "active_campaigns": act,
        "completed_campaigns": cmp,
        "wallet_balance": bal,
        "timestamp": datetime.now(UTC).isoformat(),
    }, headers={"Cache-Control": "private, max-age=30"})


@router.get("/api/dashboard/activity")
def dashboard_activity(request: Request):
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        with get_db() as conn:
            rows = conn.execute(
                "SELECT ce.status, ce.sent_at, ce.company_name, ce.job_title "
                "FROM campaign_emails ce JOIN campaigns c ON c.campaign_id = ce.campaign_id "
                "WHERE c.user_id = ? ORDER BY ce.sent_at DESC LIMIT 20", (user_id,)
            ).fetchall()
    except Exception as e:
        logger.error(f"Database error in dashboard_activity: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")

    act = [dict(r) if hasattr(r, "keys") else {
        "status": r[0], "sent_at": r[1], "company_name": r[2], "job_title": r[3]
    } for r in rows]
    return JSONResponse({"activity": act})


@router.get("/api/v2/live-stats")
def live_stats(request: Request):
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        with get_db() as conn:
            running = conn.execute(
                "SELECT c.campaign_id, p.target_titles AS job_title, c.sent_count AS total_sent, c.total_companies AS total_attempted "
                "FROM campaigns c LEFT JOIN cv_profiles p ON c.profile_id = p.id "
                "WHERE c.user_id = ? AND c.status = 'running' ORDER BY c.started_at DESC LIMIT 5", (user_id,)
            ).fetchall()
    except Exception as e:
        logger.error(f"Database error in live_stats: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")

    r = [dict(x) if hasattr(x, "keys") else {
        "campaign_id": x[0], "job_title": x[1], "total_sent": x[2], "total_attempted": x[3]
    } for x in running]
    return JSONResponse({
        "running_campaigns": r,
        "timestamp": datetime.now(UTC).isoformat(),
    }, headers={"Cache-Control": "private, max-age=10"})


@router.get("/dashboard/stats")
def dashboard_stats_alt(request: Request):
    return dashboard_stats(request)


@router.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request):
    get_db, get_verified_user_id, templates, config = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return HTMLResponse(status_code=302, headers={"Location": "/login"})
    try:
        with get_db() as conn:
            user = conn.execute("SELECT name, email, tokens FROM users WHERE user_id = ?", (user_id,)).fetchone()
            u = dict(user) if hasattr(user, "keys") else {"name": user[0], "email": user[1], "tokens": user[2]} if user else {}
    except Exception as e:
        logger.error(f"Database error in stats_page: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")

    return templates.TemplateResponse(request, "stats.html", {
        "user": u, "user_id": user_id, "VERSION": config.VERSION
    })
