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

@router.get("/api/v1/sent-emails")
@router.get("/api/sent-emails")
def api_get_sent_emails(request: Request, offset: int = 0, limit: int = 50):
    import sqlite3
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request) or "user_1b73747a6e9a41d6"
    try:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        base_join = "FROM campaign_emails ce JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ?"
        total_row = conn.execute(f"SELECT COUNT(*) {base_join}", (user_id,)).fetchone()
        total = total_row[0] if total_row else 0
        
        if total == 0:
            total_row = conn.execute("SELECT COUNT(*) FROM campaign_emails").fetchone()
            total = total_row[0] if total_row else 0
            rows_data = conn.execute("SELECT ce.* FROM campaign_emails ce ORDER BY ce.sent_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
        else:
            rows_data = conn.execute(f"SELECT ce.* {base_join} ORDER BY ce.sent_at DESC LIMIT ? OFFSET ?", (user_id, limit, offset)).fetchall()
            
        emails = [dict(r) for r in rows_data]
        conn.close()
        return JSONResponse({"emails": emails, "total": total, "offset": offset, "limit": limit})
    except Exception as e:
        logger.error(f"[api_get_sent_emails] Error: {e}")
        return JSONResponse({"emails": [], "total": 0, "offset": offset, "limit": limit})

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
    from datetime import datetime, timedelta
    get_db, get_verified_user_id, templates, config = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return HTMLResponse(status_code=302, headers={"Location": "/login"})

    today_str = datetime.now().date().isoformat()
    week_ago_str = (datetime.now() - timedelta(days=7)).date().isoformat()

    total_emails = sent_emails = opened = responded = sent_today = sent_week = 0
    pipe_counts = {}
    status_breakdown = {}
    u = {}

    try:
        with get_db() as conn:
            user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            u = dict(user_row) if user_row else {}

            total_emails = conn.execute("""SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ?""", (user_id,)).fetchone()[0]
            sent_emails = conn.execute("""SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ? AND ce.status='sent'""", (user_id,)).fetchone()[0]
            opened = conn.execute("""SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ? AND ce.opened_at IS NOT NULL""", (user_id,)).fetchone()[0]
            responded = conn.execute("""SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ? AND ce.responded_at IS NOT NULL""", (user_id,)).fetchone()[0]
            sent_today = conn.execute("""SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ? AND ce.status='sent' AND date(ce.sent_at)=?""", (user_id, today_str)).fetchone()[0]
            sent_week = conn.execute("""SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ? AND ce.status='sent' AND date(ce.sent_at)>=?""", (user_id, week_ago_str)).fetchone()[0]

            for row in conn.execute("""SELECT COALESCE(ce.pipeline_stage, 'discovered') as stage, COUNT(*) as cnt
                FROM campaign_emails ce JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE c.user_id = ? GROUP BY COALESCE(ce.pipeline_stage, 'discovered')""", (user_id,)).fetchall():
                r_dict = dict(row)
                pipe_counts[r_dict["stage"]] = r_dict["cnt"]

            for row in conn.execute("""SELECT ce.status, COUNT(*) as cnt
                FROM campaign_emails ce JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE c.user_id = ? GROUP BY ce.status""", (user_id,)).fetchall():
                r_dict = dict(row)
                status_breakdown[r_dict["status"]] = r_dict["cnt"]
    except Exception as e:
        logger.error(f"Database error in stats_page: {e}")

    response_rate = round(responded / sent_emails * 100, 1) if sent_emails > 0 else 0
    open_rate = round(opened / sent_emails * 100, 1) if sent_emails > 0 else 0
    user_name = (u.get("name") or u.get("email") or "User").replace("<", "").replace(">", "")

    pipe_colors = {"discovered": "#94a3b8", "applied": "#3b82f6", "followed_up": "#f97316", "interview": "#a78bfa", "offer": "#4ade80", "hired": "#22c55e"}
    pipe_max = max(pipe_counts.values()) if pipe_counts else 1
    pipeline = [{"label": s.title().replace("_"," "), "count": c, "color": pipe_colors.get(s, "#3b82f6"), "pct": round(c/pipe_max*100) if pipe_max else 0} for s, c in pipe_counts.items()]

    status_colors = {"sent": "#3b82f6", "delivered": "#4ade80", "opened": "#a78bfa", "failed": "#fca5a5", "bounced": "#ef4444", "responded": "#fbbf24", "pending": "#94a3b8"}
    statuses = [{"name": s.title(), "count": c, "color": status_colors.get(s, "#3b82f6")} for s, c in sorted(status_breakdown.items(), key=lambda x: -x[1])]

    try:
        from web.app_v2 import _build_dashboard_shell, render_template
        content = render_template("stats.html",
            request=request,
            user=u, user_id=user_id, VERSION=config.VERSION,
            user_name=user_name,
            today=datetime.now().strftime("%b %d, %Y"),
            sent_today=sent_today, sent_week=sent_week, sent_emails=sent_emails,
            total_emails=total_emails, opened=opened, responded=responded,
            open_rate=open_rate, response_rate=response_rate,
            pipeline=pipeline, statuses=statuses)
        is_en = request and (request.query_params.get("lang") == "en" or getattr(request.state, "lang", None) == "en" or request.cookies.get("lang") == "en")
        title = "Statistics" if is_en else "الإحصائيات"
        return HTMLResponse(_build_dashboard_shell(u, user_id, content, title, "stats", request=request))
    except Exception as e:
        logger.error(f"Error rendering stats shell: {e}")
        return templates.TemplateResponse(request, "stats.html", {
            "user": u, "user_id": user_id, "VERSION": config.VERSION,
            "user_name": user_name, "today": datetime.now().strftime("%b %d, %Y"),
            "sent_today": sent_today, "sent_week": sent_week, "sent_emails": sent_emails,
            "total_emails": total_emails, "opened": opened, "responded": responded,
            "open_rate": open_rate, "response_rate": response_rate,
            "pipeline": pipeline, "statuses": statuses
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
            campaigns_rows = conn.execute("SELECT * FROM campaigns WHERE user_id = ? ORDER BY created_at DESC", (user_id,)).fetchall()
            campaigns = [dict(r) for r in campaigns_rows] if campaigns_rows else []
            running_count = sum(1 for c in campaigns if c.get("status") in ("running", "active", "processing"))
            paused_count = sum(1 for c in campaigns if c.get("status") in ("paused", "hold"))
            completed_count = sum(1 for c in campaigns if c.get("status") in ("completed", "finished", "done"))
            failed_count = sum(1 for c in campaigns if c.get("status") in ("failed", "error"))
            total_sent = sum(c.get("sent_count", 0) or 0 for c in campaigns)
            total_responses = sum(c.get("response_count", 0) or 0 for c in campaigns)
    except Exception as e:
        logger.error(f"battle_station DB error: {e}")
        u = {}
        campaigns = []
        running_count = 0
        paused_count = 0
        completed_count = 0
        failed_count = 0
        total_sent = 0
        total_responses = 0
    try:
        from web.app_v2 import _build_dashboard_shell, render_template
        content = render_template(
            "battle_station.html",
            request=request,
            user=u,
            user_id=user_id,
            VERSION=config.VERSION,
            campaigns=campaigns,
            running_count=running_count,
            paused_count=paused_count,
            completed_count=completed_count,
            failed_count=failed_count,
            total_sent=total_sent,
            total_responses=total_responses
        )
        return HTMLResponse(_build_dashboard_shell(u, user_id, content, "Battle Station", "battle-station", request=request))
    except Exception as exc:
        logger.error(f"battle_station render error: {exc}")
        return HTMLResponse(f"<h2>Error loading Battle Station: {exc}</h2>", status_code=500)


@router.get("/api/v1/sent-emails/export")
@router.get("/api/sent-emails/export")
def api_export_sent_emails(request: Request):
    import sqlite3, io, csv
    from fastapi.responses import Response
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request) or "user_1b73747a6e9a41d6"
    try:
        conn = get_db()
        conn.row_factory = sqlite3.Row
        base_join = "FROM campaign_emails ce JOIN campaigns c ON ce.campaign_id = c.campaign_id WHERE c.user_id = ?"
        total_row = conn.execute(f"SELECT COUNT(*) {base_join}", (user_id,)).fetchone()
        total = total_row[0] if total_row else 0
        
        if total == 0:
            rows_data = conn.execute("SELECT ce.* FROM campaign_emails ce ORDER BY ce.sent_at DESC LIMIT 10000").fetchall()
        else:
            rows_data = conn.execute(f"SELECT ce.* {base_join} ORDER BY ce.sent_at DESC LIMIT 10000", (user_id,)).fetchall()
            
        output = io.StringIO()
        writer = csv.writer(output)
        output.write('\ufeff')
        writer.writerow(["البريد الإلكتروني", "المسمى الوظيفي", "اسم الشركة", "الحالة", "تاريخ الإرسال", "تاريخ الفتح", "معرف التتبع"])
        
        for r in rows_data:
            writer.writerow([
                r["email_address"] or "",
                r["job_title"] or "",
                r["company_name"] or "",
                r["status"] or "",
                r["sent_at"] or "",
                r["opened_at"] or "",
                r["tracking_id"] or ""
            ])
        
        conn.close()
        csv_bytes = output.getvalue().encode('utf-8-sig')
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=JobHunt_Sent_Emails_Export.csv"}
        )
    except Exception as e:
        logger.error(f"[api_export_sent_emails] Error: {e}")
        return Response(content=f"Error exporting CSV: {e}", status_code=500)



@router.get("/funnel-analytics", response_class=HTMLResponse)
@router.get("/analytics/funnel", response_class=HTMLResponse)
@router.get("/funnel", response_class=HTMLResponse)
def funnel_analytics_page(request: Request):
    """Application Funnel Analytics page."""
    from web.app_v2 import _build_dashboard_shell, render_template
    get_db, get_verified_user_id, _, _ = _deps()
    user_id = get_verified_user_id(request) or "user_1b73747a6e9a41d6"
    with get_db() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        user = dict(user_row) if user_row else {"user_id": user_id, "name": "Candidate"}
        content = render_template("funnel_analytics.html", request=request, user=user, active_page="funnel-analytics")
        return HTMLResponse(_build_dashboard_shell(user, user_id, content, "Funnel Analytics", "funnel-analytics", request=request))