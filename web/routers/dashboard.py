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
@router.get("/dashboard/v3", response_class=HTMLResponse)
def dashboard_page(request: Request):
    from fastapi.responses import RedirectResponse
    return RedirectResponse("/user-dashboard", status_code=302)

@router.get("/api/dashboard/stats")
@router.get("/api/v1/dashboard/stats")
@router.get("/api/v1/dashboard/stats/")
def dashboard_stats(request: Request):
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        with get_db() as conn:
            row = conn.execute(
                "SELECT "
                "COALESCE(SUM(c.sent_count), 0) AS total_sent, "
                "COALESCE(SUM(CASE WHEN c.status = 'running' THEN 1 ELSE 0 END), 0) AS active_campaigns, "
                "COALESCE(SUM(CASE WHEN c.status = 'completed' THEN 1 ELSE 0 END), 0) AS completed_campaigns, "
                "COALESCE(u.wallet_balance, 0.0) AS wallet_balance "
                "FROM users u "
                "LEFT JOIN campaigns c ON c.user_id = u.user_id "
                "WHERE u.user_id = ? "
                "GROUP BY u.user_id, u.wallet_balance",
                (user_id,)
            ).fetchone()

            if row:
                try:
                    ts = row["total_sent"]
                    act = row["active_campaigns"]
                    cmp = row["completed_campaigns"]
                    bal = row["wallet_balance"]
                except (TypeError, KeyError, IndexError):
                    try:
                        ts = getattr(row, "total_sent", row[0])
                        act = getattr(row, "active_campaigns", row[1])
                        cmp = getattr(row, "completed_campaigns", row[2])
                        bal = getattr(row, "wallet_balance", row[3])
                    except Exception:
                        ts, act, cmp, bal = row[0], row[1], row[2], row[3]
            else:
                ts, act, cmp, bal = 0, 0, 0, 0.0
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
            user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            u = dict(user_row) if user_row else {}
    except Exception as e:
        logger.error(f"Database error in stats_page: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")

    try:
        from web.app_v2 import _build_dashboard_shell, render_template
        content = render_template("stats.html", request=request, user=u, user_id=user_id, VERSION=config.VERSION)
        return HTMLResponse(_build_dashboard_shell(u, user_id, content, "الإحصائيات", "stats", request=request))
    except Exception:
        # Fallback to naked template if shell fails
        return templates.TemplateResponse(request, "stats.html", {
            "user": u, "user_id": user_id, "VERSION": config.VERSION
        })


@router.get("/battle-station", response_class=HTMLResponse)
def battle_station_page(request: Request):
    """Battle Station — live campaign monitoring and control center."""
    get_db, get_verified_user_id, _, config = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/login", status_code=303)
    try:
        with get_db() as conn:
            user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            u = dict(user_row) if user_row else {}
    except Exception as e:
        logger.error(f"battle_station DB error: {e}")
        u = {}
    try:
        from web.app_v2 import _build_dashboard_shell, render_template
        content = render_template("battle_station.html", request=request, user=u, user_id=user_id, VERSION=config.VERSION)
        return HTMLResponse(_build_dashboard_shell(u, user_id, content, "Battle Station", "battle-station", request=request))
    except Exception as exc:
        logger.error(f"battle_station render error: {exc}")
        return HTMLResponse(f"<h2>Error loading Battle Station: {exc}</h2>", status_code=500)
