"""
routers/dashboard.py - Dashboard Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])

def _deps():
    from web.shared import get_db, get_verified_user_id, templates, config
    return get_db, get_verified_user_id, templates, config

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    get_db, get_verified_user_id, templates, config = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return HTMLResponse(status_code=302, headers={"Location": "/login"})
    conn = get_db()
    user = conn.execute(
        "SELECT name, email, tokens, subscription_status, wallet_balance FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    if not user:
        conn.close()
        resp = HTMLResponse(status_code=302, headers={"Location": "/login"})
        resp.delete_cookie("user_id")
        return resp

    campaigns = conn.execute(
        "SELECT campaign_id, job_title, status, total_sent, total_attempted, created_at "
        "FROM campaigns WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()
    conn.close()

    u = dict(user) if hasattr(user, "keys") else {
        "name": user[0], "email": user[1], "tokens": user[2],
        "subscription_status": user[3], "wallet_balance": user[4]
    }
    camps = [dict(c) if hasattr(c, "keys") else {
        "campaign_id": c[0], "job_title": c[1], "status": c[2],
        "total_sent": c[3], "total_attempted": c[4], "created_at": c[5]
    } for c in campaigns]

    return templates.TemplateResponse(request, "dashboard_v3.html", {
        "user": u,
        "user_id": user_id,
        "campaigns": camps,
        "VERSION": config.VERSION,
    })

@router.get("/api/dashboard/stats")
def dashboard_stats(request: Request):
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    conn = get_db()
    try:
        row1 = conn.execute("SELECT COALESCE(SUM(total_sent), 0) FROM campaigns WHERE user_id = ?", (user_id,)).fetchone()
        row2 = conn.execute("SELECT COUNT(*) FROM campaigns WHERE user_id = ? AND status = 'running'", (user_id,)).fetchone()
        row3 = conn.execute("SELECT COUNT(*) FROM campaigns WHERE user_id = ? AND status = 'completed'", (user_id,)).fetchone()
        row4 = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        
        ts = row1[0] if row1 else 0
        act = row2[0] if row2 else 0
        cmp = row3[0] if row3 else 0
        bal = (row4[0] if not hasattr(row4, "__getitem__") else row4["wallet_balance"]) if row4 else 0.0
    finally:
        conn.close()

    return JSONResponse({
        "total_sent": ts,
        "active_campaigns": act,
        "completed_campaigns": cmp,
        "wallet_balance": bal,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@router.get("/api/dashboard/activity")
def dashboard_activity(request: Request):
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT ce.status, ce.sent_at, ce.company_name, ce.job_title "
            "FROM campaign_emails ce JOIN campaigns c ON c.campaign_id = ce.campaign_id "
            "WHERE c.user_id = ? ORDER BY ce.sent_at DESC LIMIT 20", (user_id,)
        ).fetchall()
    finally:
        conn.close()

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
    conn = get_db()
    try:
        running = conn.execute(
            "SELECT campaign_id, job_title, total_sent, total_attempted FROM campaigns "
            "WHERE user_id = ? AND status = 'running' ORDER BY started_at DESC LIMIT 5", (user_id,)
        ).fetchall()
    finally:
        conn.close()
    
    r = [dict(x) if hasattr(x, "keys") else {
        "campaign_id": x[0], "job_title": x[1], "total_sent": x[2], "total_attempted": x[3]
    } for x in running]
    return JSONResponse({
        "running_campaigns": r,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@router.get("/dashboard/stats")
def dashboard_stats_alt(request: Request):
    return dashboard_stats(request)

@router.get("/stats", response_class=HTMLResponse)
def stats_page(request: Request):
    get_db, get_verified_user_id, templates, config = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return HTMLResponse(status_code=302, headers={"Location": "/login"})
    conn = get_db()
    user = conn.execute("SELECT name, email, tokens FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    u = dict(user) if hasattr(user, "keys") else {"name": user[0], "email": user[1], "tokens": user[2]} if user else {}
    return templates.TemplateResponse(request, "stats.html", {
        "user": u, "user_id": user_id, "VERSION": config.VERSION
    })