"""
routers/admin.py - Admin Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import logging
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Request, Form, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])

def _deps():
    from web.app_v2 import _build_dashboard_shell, render_template
    from web.shared import config, get_db, get_verified_user_id, templates
    return get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell

@router.post("/admin/panic-toggle")
def admin_panic_toggle(request: Request):
    """Toggles the Iron Cloak Panic Mode on or off."""
    from web.app_v2 import require_admin
    if not require_admin(request):
        return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)

    from core.panic_mode import toggle_panic_mode
    new_state = toggle_panic_mode()
    return JSONResponse({"status": "success", "panic_mode_active": new_state})

@router.get("/admin/viral-factory", response_class=HTMLResponse)
def admin_viral_factory(request: Request):
    """View and download generated viral MP4 videos."""
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/user-dashboard", status_code=303)

    with get_db() as conn:
        viral_dir = "cache/viral_videos"
        files = []
        if os.path.exists(viral_dir):
            files = [f for f in os.listdir(viral_dir) if f.endswith(".mp4")]

        html = '''
        <html><head><title>Viral Factory</title>
        <style>body{font-family: Arial, sans-serif; padding: 20px; background: #0D1117; color: white;}
        .video-card{background: #161B22; padding: 15px; border-radius: 8px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;}
        .download-btn{background: #238636; color: white; text-decoration: none; padding: 8px 16px; border-radius: 4px;}
        </style></head><body>
        <h2>🚀 Instant Profit Viral Factory</h2>
        <p>These videos are auto-generated daily by AI. Download them and upload them to TikTok/Shorts to get instant massive traffic.</p>
        '''

        if not files:
            html += "<p>No viral videos generated yet. The Autopilot runs daily.</p>"
        else:
            for f in files:
                html += f'''
                <div class="video-card">
                    <div><strong>{f}</strong></div>
                    <a href="/admin/viral-factory/download/{f}" class="download-btn">⬇️ Download MP4</a>
                </div>
                '''
        html += "</body></html>"
        return HTMLResponse(html)

@router.get("/admin/viral-factory/download/{filename}")
def download_viral_video(request: Request, filename: str):
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/user-dashboard", status_code=303)
    from fastapi.responses import FileResponse
    file_path = os.path.join("cache/viral_videos", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename, media_type="video/mp4")
    return HTMLResponse("File not found", status_code=404)

@router.get("/admin/logs", response_class=HTMLResponse)
def admin_logs(request: Request):
    """Secure Log Viewer - Only accessible by admins."""
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/user-dashboard", status_code=303)

    with get_db() as conn:
        pa_domain = os.getenv("PA_DOMAIN", "jhfguf.pythonanywhere.com")
        error_log_path = f"/var/log/{pa_domain}.error.log"
        server_log_path = f"/var/log/{pa_domain}.server.log"

        error_log_content = "Log file not found."
        server_log_content = "Log file not found."

        try:
            if os.path.exists(error_log_path):
                with open(error_log_path, encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                    error_log_content = ''.join(lines[-100:])
            else:
                error_log_content = f"Log file not found at {error_log_path}"
        except Exception as e:
            error_log_content = f"Error reading log: {str(e)}"

        try:
            if os.path.exists(server_log_path):
                with open(server_log_path, encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                    server_log_content = ''.join(lines[-100:])
            else:
                server_log_content = f"Log file not found at {server_log_path}"
        except Exception as e:
            server_log_content = f"Error reading log: {str(e)}"

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Server Logs</title>
            <style>
                body {{ background: #0f172a; color: #e2e8f0; font-family: monospace; padding: 20px; }}
                h1 {{ color: #38bdf8; border-bottom: 1px solid #334155; padding-bottom: 10px; }}
                h2 {{ color: #fbbf24; margin-top: 30px; }}
                .log-box {{ background: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; overflow-x: auto; white-space: pre-wrap; }}
                .error-log {{ border-left: 4px solid #ef4444; }}
                .server-log {{ border-left: 4px solid #10b981; }}
                .btn {{ display: inline-block; padding: 8px 16px; background: #3b82f6; color: white; text-decoration: none; border-radius: 6px; font-family: sans-serif; margin-bottom: 20px; font-weight: bold; }}
                .btn:hover {{ background: #2563eb; }}
            </style>
        </head>
        <body>
            <a href="/user-dashboard" class="btn">&larr; Back to Dashboard</a>
            <h1>Server Logs (Tail 100 lines)</h1>
        
            <h2>Error Log ({error_log_path})</h2>
            <div class="log-box error-log">{error_log_content}</div>
        
            <h2>Server Log ({server_log_path})</h2>
            <div class="log-box server-log">{server_log_content}</div>
        </body>
        </html>
        """
        return HTMLResponse(html)

@router.get("/admin/analytics", response_class=HTMLResponse)
def admin_analytics(req: Request):
    """Admin analytics dashboard — revenue, users, campaigns, A/B testing."""
    from web.app_v2 import require_admin
    get_db, get_verified_user_id, _, _, render_template, _build_dashboard_shell = _deps()
    try:
        admin_id = require_admin(req)
        if not admin_id:
            return RedirectResponse("/user-dashboard", status_code=303)

        with get_db() as db:
            user_admin = db.execute("SELECT * FROM users WHERE user_id = ?", (admin_id,)).fetchone()
            if not user_admin or user_admin.get("user_type") != "admin":
                pass  # db.close()
                return HTMLResponse("<h2>403 Forbidden</h2>", status_code=403)

            total_users = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            total_revenue = db.execute("SELECT COALESCE(SUM(amount),0) FROM wallet_transactions WHERE transaction_type='deposit'").fetchone()[0]
            active_campaigns = db.execute("SELECT COUNT(*) FROM campaigns WHERE status IN ('active','processing')").fetchone()[0]
            emails_today = db.execute("SELECT COUNT(*) FROM campaign_emails WHERE date(sent_at)=date('now')").fetchone()[0]

            last_month_rev = db.execute(
                "SELECT COALESCE(SUM(amount),0) FROM wallet_transactions WHERE transaction_type='deposit' AND created_at >= date('now','-30 days')"
            ).fetchone()[0]
            prev_month_rev = db.execute(
                "SELECT COALESCE(SUM(amount),0) FROM wallet_transactions WHERE transaction_type='deposit' AND created_at BETWEEN date('now','-60 days') AND date('now','-30 days')"
            ).fetchone()[0]
            revenue_growth = round((last_month_rev - prev_month_rev) / max(prev_month_rev, 1) * 100, 1) if prev_month_rev else 0
            user_growth = db.execute("SELECT COUNT(*) FROM users WHERE date(created_at)=date('now')").fetchone()[0]
            campaign_pct = round(active_campaigns/max(total_users,1)*100) if total_users else 0
            deliv_score = round(db.execute("SELECT CASE WHEN COUNT(*)=0 THEN 100 ELSE ROUND(SUM(CASE WHEN status IN ('sent','delivered') THEN 1.0 ELSE 0 END)/COUNT(*)*100,0) END FROM campaign_emails").fetchone()[0]) if total_users else 100

            monthly_revenue = []
            months = db.execute("""
                SELECT strftime('%Y-%m', created_at) as month, COALESCE(SUM(amount),0) as total
                FROM wallet_transactions WHERE transaction_type='deposit' AND created_at >= date('now','-6 months')
                GROUP BY month ORDER BY month
            """).fetchall()
            if months:
                for m in months:
                    monthly_revenue.append({"label": m["month"], "amount": round(m["total"], 2)})
            else:
                import calendar
                for i in range(5, -1, -1):
                    m = datetime.now().month - i - 1
                    y = datetime.now().year
                    while m <= 0:
                        m += 12
                        y -= 1
                    monthly_revenue.append({"label": calendar.month_abbr[m], "amount": 0})
            max_rev = max((m["amount"] for m in monthly_revenue), default=1)

            try:
                tier_rows = db.execute("""
                    SELECT COALESCE(package_name, order_type, 'unknown') as name, COUNT(*) as cnt, COALESCE(SUM(amount_usd),0) as rev
                    FROM orders WHERE payment_status='completed'
                    GROUP BY name ORDER BY rev DESC LIMIT 5
                """).fetchall()
            except Exception:
                tier_rows = []
            if tier_rows:
                total_paid = sum(r["cnt"] for r in tier_rows) or 1
                tier_breakdown = []
                colors = [("#3b82f6","#6366f1"),("#8b5cf6","#a78bfa"),("#f59e0b","#ef4444"),("#22c55e","#16a34a"),("#94a3b8","#64748b")]
                for i, r in enumerate(tier_rows):
                    tier_breakdown.append({
                        "name": f"{r['name']} (${r['rev']:.0f})",
                        "count": r["cnt"],
                        "revenue": round(r["rev"], 2),
                        "pct": round(r["cnt"]/total_paid*100),
                        "color": colors[i%5][0],
                        "color2": colors[i%5][1]
                    })
            else:
                tier_breakdown = []

            try:
                country_rows = db.execute("""
                    SELECT COALESCE(NULLIF(TRIM(home_country),''), 'Unknown') as name, COUNT(*) as cnt
                    FROM cv_profiles WHERE home_country IS NOT NULL AND home_country != ''
                    GROUP BY home_country ORDER BY cnt DESC LIMIT 5
                """).fetchall()
            except Exception:
                country_rows = []
            if country_rows:
                flag_map = {'Lebanon':'&#x1F1F1;&#x1F1E7;','LB':'&#x1F1F1;&#x1F1E7;','UAE':'&#x1F1E6;&#x1F1EA;','AE':'&#x1F1E6;&#x1F1EA;','Saudi Arabia':'&#x1F1F8;&#x1F1E6;','SA':'&#x1F1F8;&#x1F1E6;','Qatar':'&#x1F1F6;&#x1F1E6;','QA':'&#x1F1F6;&#x1F1E6;','Kuwait':'&#x1F1F0;&#x1F1FC;','KW':'&#x1F1F0;&#x1F1FC;','USA':'&#x1F1FA;&#x1F1F8;','US':'&#x1F1FA;&#x1F1F8;','UK':'&#x1F1EC;&#x1F1E7;','GB':'&#x1F1EC;&#x1F1E7;','France':'&#x1F1EB;&#x1F1F7;','FR':'&#x1F1EB;&#x1F1F7;','Egypt':'&#x1F1EA;&#x1F1EC;','EG':'&#x1F1EA;&#x1F1EC;','Jordan':'&#x1F1EF;&#x1F1F4;','JO':'&#x1F1EF;&#x1F1F4;','Bahrain':'&#x1F1E7;&#x1F1ED;','BH':'&#x1F1E7;&#x1F1ED;','Oman':'&#x1F1F4;&#x1F1F2;','OM':'&#x1F1F4;&#x1F1F2;'}
                colors2 = ["#3b82f6","#22c55e","#8b5cf6","#f59e0b","#ef4444"]
                total_country = sum(r["cnt"] for r in country_rows) or 1
                top_countries = []
                for i, r in enumerate(country_rows):
                    top_countries.append({
                        "flag": flag_map.get(r["name"], '&#x1F310;'),
                        "name": r["name"],
                        "users": r["cnt"],
                        "pct": round(r["cnt"]/total_country*100),
                        "color": colors2[i%5]
                    })
            else:
                top_countries = []

            pass  # db.close()
            content_html = render_template("admin_analytics.html", request=req,
                total_revenue=total_revenue,
                total_users=total_users, active_campaigns=active_campaigns,
                emails_today=emails_today, revenue_growth=revenue_growth,
                user_growth=user_growth, campaign_pct=campaign_pct,
                deliv_score=deliv_score, monthly_revenue=monthly_revenue,
                max_revenue=max_rev, tier_breakdown=tier_breakdown,
                top_countries=top_countries,
                ab_test_a_rate=None, ab_test_a_sent=0,
                ab_test_b_rate=None, ab_test_b_sent=0
            )
            return HTMLResponse(_build_dashboard_shell(None, admin_id, content_html, "Admin Analytics", "admin", request=req))
    except Exception as e:
        logger.error(f"Admin analytics crashed: {e}", exc_info=True)
        return HTMLResponse("<h2>Analytics Error</h2><p>The analytics dashboard is temporarily unavailable. Please try again later.</p>", status_code=500)

# ── MIGRATED ADMIN ROUTES ───────────────────────────────────────────────────

import uuid

from fastapi import BackgroundTasks, Form


@router.get("/admin", response_class=HTMLResponse)
def admin_panel(request: Request):
    """Admin dashboard — full system overview."""
    logger.info("[ADMIN_ROUTER] admin_panel invoked!")
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    admin_user_id = require_admin(request)
    if not admin_user_id:
        return RedirectResponse("/user-dashboard", status_code=303)
    try:
        from payments import get_payment_stats
    except Exception:
        get_payment_stats = lambda: {"total_payments": 0, "total_received_usd": 0, "by_currency": {}, "recent": []}

    with get_db() as conn:
        total_users    = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_campaigns= conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[0]
        total_emails   = conn.execute("SELECT COUNT(*) FROM campaign_emails").fetchone()[0]
        emails_sent    = conn.execute("SELECT COUNT(*) FROM campaign_emails WHERE status='sent'").fetchone()[0]
        total_revenue  = conn.execute("SELECT COALESCE(SUM(amount_usd),0) FROM orders WHERE payment_status='completed'").fetchone()[0]
        total_wallets  = conn.execute("SELECT COALESCE(SUM(wallet_balance),0) FROM users").fetchone()[0]

        users = [dict(r) for r in conn.execute(
            "SELECT user_id, email, name, wallet_balance, total_spent, user_type, created_at, is_active FROM users ORDER BY created_at DESC LIMIT 50"
        ).fetchall()]

        campaigns = [dict(r) for r in conn.execute(
            "SELECT c.campaign_id, c.user_id, c.status, c.total_companies, c.sent_count, c.created_at, u.email FROM campaigns c LEFT JOIN users u ON c.user_id=u.user_id ORDER BY c.created_at DESC LIMIT 30"
        ).fetchall()]

        orders = [dict(r) for r in conn.execute(
            "SELECT o.order_id, o.user_id, o.order_type, o.amount_usd, o.payment_status, o.created_at, u.email FROM orders o LEFT JOIN users u ON o.user_id=u.user_id ORDER BY o.created_at DESC LIMIT 30"
        ).fetchall()]

        try:
            redeem_codes = [dict(r) for r in conn.execute(
                "SELECT code, value_usd, code_type, is_used, used_by, created_at FROM redeem_codes ORDER BY created_at DESC LIMIT 20"
            ).fetchall()]
        except Exception:
            redeem_codes = []

        try:
            manual_emails = [dict(r) for r in conn.execute(
                "SELECT to_email, subject, price_usd, status, created_at FROM manual_emails ORDER BY created_at DESC LIMIT 20"
            ).fetchall()]
            manual_email_count = conn.execute("SELECT COUNT(*) FROM manual_emails").fetchone()[0]
            manual_email_revenue = conn.execute("SELECT COALESCE(SUM(price_usd),0) FROM manual_emails WHERE status='sent'").fetchone()[0]
        except Exception:
            manual_emails = []
            manual_email_count = 0
            manual_email_revenue = 0.0

        try:
            flash_sales = [dict(r) for r in conn.execute(
                "SELECT * FROM flash_sales ORDER BY created_at DESC LIMIT 50"
            ).fetchall()]
            now_iso = datetime.now().isoformat()
            for s in flash_sales:
                s_end = str(s.get("end_time") or "")
                s_start = str(s.get("start_time") or "")
                is_active_flag = bool(s.get("active", 1))
                is_time_valid = s_end > now_iso
                s["is_live"] = is_active_flag and is_time_valid
                s["is_paused"] = not is_active_flag
                s["is_expired"] = is_active_flag and not is_time_valid
                s["formatted_end"] = s_end.replace("T", " ")[:16] if s_end else "—"
                s["formatted_start"] = s_start.replace("T", " ")[:16] if s_start else "—"
                s["formatted_created"] = str(s.get("created_at") or "")[:16]
        except Exception:
            flash_sales = []

        pass  # conn.close()

        try:
            payment_stats = get_payment_stats()
        except Exception:
            payment_stats = {"total_payments": 0, "total_received_usd": 0, "by_currency": {}, "recent": []}

        content_html = render_template("admin.html", request=request,
            now=datetime.now(),
            stats={
                "total_users": total_users,
                "total_campaigns": total_campaigns,
                "total_emails": total_emails,
                "emails_sent": emails_sent,
                "total_revenue": round(float(total_revenue), 2),
                "total_wallets": round(float(total_wallets), 2),
                "manual_emails": manual_email_count,
                "manual_email_revenue": round(float(manual_email_revenue), 2),
            },
            users=users,
            campaigns=campaigns,
            orders=orders,
            redeem_codes=redeem_codes,
            manual_emails=manual_emails,
            flash_sales=flash_sales,
            payment_stats=payment_stats,
        )
        is_en = request and (request.query_params.get("lang") == "en" or getattr(request.state, "lang", None) == "en" or request.cookies.get("lang") == "en")
        title = "Admin Panel" if is_en else "لوحة الإدارة"
        admin_user_dict = {"name": "Executive Admin", "email": "admin@jobhunt-pro.com", "wallet_balance": 10000.0, "is_admin": True}
        return HTMLResponse(_build_dashboard_shell(admin_user_dict, admin_user_id, content_html, title, "admin", request=request))


@router.get("/admin/sys-logs", response_class=HTMLResponse)
def admin_sys_logs(request: Request):
    """Admin endpoint to view system logs."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

    logs_html = "<h2>System Logs</h2>"
    log_files = [
        "/var/log/jhfguf.pythonanywhere.com.error.log",
        "/var/log/jhfguf.pythonanywhere.com.server.log",
        "error.log",
        "server.log",
        "jobhunt.log",
        "sam_max.log"
    ]

    for log_path in log_files:
        if os.path.exists(log_path):
            try:
                with open(log_path, encoding='utf-8-sig', errors='replace') as f:
                    lines = f.readlines()
                    tail_lines = lines[-500:]
                    logs_html += f"<h3>{os.path.basename(log_path)}</h3>"
                    logs_html += f"<pre style='background:#1e1e1e;color:#00ff00;padding:15px;overflow:auto;height:400px;font-size:12px;'>{''.join(tail_lines)}</pre>"
            except Exception as e:
                logs_html += f"<p>Error reading {log_path}: {e}</p>"

    if logs_html == "<h2>System Logs</h2>":
        logs_html += "<p>No log files found.</p>"

    html_content = f"""
    <html>
    <head>
        <title>System Logs</title>
        <style>
            body {{ background-color: #111; color: #eee; font-family: monospace; padding: 20px; }}
            a {{ color: #3b82f6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <a href="/admin">&larr; Back to Admin Panel</a> | <a href="/user-dashboard">Back to Dashboard</a>
        {logs_html}
    </body>
    </html>
    """
    return HTMLResponse(html_content)


@router.post("/admin-reset-pw")
def admin_reset_pw(token: str = ""):
    """Reset admin password via secret token. POST-only, uses ADMIN_PW_HASH env var."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    if token != config.PA_API_TOKEN:
        return JSONResponse({"error": "invalid token"}, status_code=403)
    admin_hash = os.getenv("ADMIN_PW_HASH", "")
    if not admin_hash:
        return JSONResponse({"error": "ADMIN_PW_HASH not set in env"}, status_code=503)
    with get_db() as conn:
        conn.execute("UPDATE users SET password_hash = ? WHERE user_type = 'admin' OR LOWER(email) = 'admin@jobhunt-pro.com'",
                     (admin_hash,))
        conn.commit()
        logger.info("Password reset for admin users via admin-reset-pw")
        return {"status": "password updated for admin account"}


@router.post("/api/admin/run-design-scan")
def api_run_design_scan(request: Request):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    routes = [
        "/",
        "/pricing",
        "/faq",
        "/contact",
        "/services",
        "/compare",
        "/track-application",
        "/trust",
        "/login",
        "/register",
        "/chrome-extension",
        "/careers"
    ]

    results = []
    critical_count = 0
    high_count = 0
    medium_count = 0

    import httpx
    base_url = str(request.base_url).rstrip('/')

    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            for r in routes:
                url = f"{base_url}{r}"
                issues = []
                try:
                    res = client.get(url)
                    html = res.text

                    if "<title>" not in html or "</title>" not in html:
                        issues.append({"severity": "CRITICAL", "message": "Missing <title> tag"})
                        critical_count += 1

                    if 'name="viewport"' not in html:
                        issues.append({"severity": "CRITICAL", "message": "Missing viewport meta tag — broken on mobile"})
                        critical_count += 1

                    if "<nav" not in html:
                        issues.append({"severity": "CRITICAL", "message": "No <nav> element found"})
                        critical_count += 1

                    if "footer" not in html.lower():
                        issues.append({"severity": "MEDIUM", "message": "Missing footer element"})
                        medium_count += 1

                    cc = res.headers.get("Cache-Control", "")
                    if "no-cache" not in cc and "max-age=0" not in cc:
                        issues.append({"severity": "HIGH", "message": f"Caching enabled on HTML page (Cache-Control: {cc}) — may cause styling delay"})
                        high_count += 1

                    empty_links = html.count('href="#"') + html.count("href='#'")
                    if empty_links > 0:
                        issues.append({"severity": "LOW", "message": f"Contains {empty_links} empty placeholder link(s) (#)"})

                except Exception as e:
                    issues.append({"severity": "CRITICAL", "message": f"Page failed to load: {e}"})
                    critical_count += 1

                results.append({
                    "route": r,
                    "url": url,
                    "issues": issues
                })
    except Exception as e:
        return JSONResponse({"error": f"Scanner client error: {e}"}, status_code=500)

    return {
        "status": "success",
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "results": results
    }


@router.post("/admin/add-credits")
def admin_add_credits(
    request: Request,
    target_email: str = Form(...),
    amount: float = Form(...),
    note: str = Form("Admin credit")
):
    """Add wallet credits to any user."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT user_id, wallet_balance FROM users WHERE email = ?", (target_email,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/admin?error=user_not_found", status_code=303)

        new_balance = user_row["wallet_balance"] + amount
        conn.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (new_balance, user_row["user_id"]))
        conn.execute(
            "INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) VALUES (?,?,?,?,?)",
            (user_row["user_id"], "admin_credit", amount, new_balance, note)
        )
        conn.commit()
        pass  # conn.close()
        return RedirectResponse(f"/admin?success=added+{amount}+to+{target_email}", status_code=303)


@router.post("/admin/generate-code")
def admin_generate_code(
    request: Request,
    value: float = Form(...),
    count: int = Form(1),
    code_type: str = Form("sale")
):
    """Generate redeem codes."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import generate_redeem_code, require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        codes = []
        for _ in range(min(count, 50)):
            for attempt in range(10):
                code = generate_redeem_code()
                existing = conn.execute("SELECT id FROM redeem_codes WHERE code = ?", (code,)).fetchone()
                if not existing:
                    conn.execute("INSERT INTO redeem_codes (code, value_usd, code_type) VALUES (?, ?, ?)", (code, value, code_type))
                    codes.append(code)
                    break
        conn.commit()
        pass  # conn.close()
        codes_str = ', '.join(codes)
        return RedirectResponse(f"/admin?success=Generated+{len(codes)}+codes:+{codes_str}", status_code=303)


@router.post("/admin/generate-bulk-codes-export")
async def admin_generate_bulk_codes_export(
    request: Request,
    tier: str = Form("starter"),
    custom_value: float = Form(0.0),
    count: int = Form(100),
    code_type: str = Form("sale"),
    batch_tag: str = Form(""),
    export_excel: bool = Form(True)
):
    """Generate bulk redeem codes and optionally export them directly as an Excel/CSV file with full Xianyu automation formatting."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import generate_redeem_code, require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

    import csv
    import io

    tier_info = {
        "starter": {"name": "Starter Plan", "price": 9.00, "companies": 100},
        "basic": {"name": "Basic Plan", "price": 19.00, "companies": 350},
        "pro": {"name": "Pro VIP Plan", "price": 49.00, "companies": 1000},
        "enterprise": {"name": "Enterprise SDR Suite", "price": 149.00, "companies": 3000},
        "custom": {"name": "Custom Plan", "price": max(0.01, custom_value), "companies": int(custom_value * 10)},
    }
    
    selected_tier = tier_info.get(tier.lower(), tier_info["starter"])
    value_usd = selected_tier["price"] if tier != "custom" else max(0.01, custom_value)
    plan_name = selected_tier["name"]
    companies_cnt = selected_tier["companies"]
    tag = batch_tag.strip() or f"Xianyu-{tier.upper()}-{datetime.now().strftime('%Y%m%d')}"
    
    total_count = max(1, min(count, 5000))
    generated_records = []
    
    with get_db() as conn:
        for _ in range(total_count):
            for _attempt in range(15):
                code = generate_redeem_code()
                existing = conn.execute("SELECT id FROM redeem_codes WHERE code = ?", (code,)).fetchone()
                if not existing:
                    conn.execute("INSERT INTO redeem_codes (code, value_usd, code_type) VALUES (?, ?, ?)", (code, value_usd, code_type))
                    generated_records.append({
                        "code": code,
                        "tier": plan_name,
                        "value_usd": value_usd,
                        "companies": companies_cnt,
                        "batch_tag": tag,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    break
        conn.commit()

    if export_excel:
        output = io.StringIO()
        output.write('\ufeff') # UTF-8 BOM for Microsoft Excel & WPS Office compatibility
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        
        # Header Row
        writer.writerow([
            "Code (卡密激活码)",
            "Package (套餐类型)",
            "Value USD (金额 $)",
            "Companies (企业数量)",
            "Activation URL (激活网址)",
            "Xianyu Auto-Message (闲鱼自动发货文本)",
            "Batch Tag (批次标签)",
            "Status (状态)",
            "Created At (创建时间)"
        ])
        
        domain = getattr(config, "DOMAIN", "jobhunt-pro-mve3.onrender.com")
        if not domain.startswith("http"):
            base_url = f"https://{domain}" if "localhost" not in domain else f"http://{domain}"
        else:
            base_url = domain
            
        for r in generated_records:
            c = r["code"]
            redeem_url = f"{base_url}/redeem?lang=zh&code={c}"
            auto_msg = f"亲，感谢购买！您的专属256位激活卡密为：{c} 请前往 {base_url}/redeem?lang=zh 输入邮箱和卡密立即自动投递！"
            writer.writerow([
                c,
                r["tier"],
                f"${r['value_usd']:.2f}",
                r["companies"],
                redeem_url,
                auto_msg,
                r["batch_tag"],
                "Unused / 未使用",
                r["created_at"]
            ])
            
        csv_bytes = output.getvalue().encode('utf-8-sig')
        filename = f"JobHunt_Codes_{tier}_{len(generated_records)}pcs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
        )

    return RedirectResponse(f"/admin?success=Generated+{len(generated_records)}+bulk+codes+for+{tier}", status_code=303)


@router.get("/admin/export-codes")
async def admin_export_codes(request: Request, status: str = "all"):
    """Export existing redeem codes to Excel/CSV."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

    import csv
    import io

    with get_db() as conn:
        if status == "unused":
            rows = conn.execute("SELECT code, value_usd, code_type, is_used, used_by, created_at, used_at FROM redeem_codes WHERE is_used = 0 OR is_used IS NULL ORDER BY created_at DESC").fetchall()
        elif status == "used":
            rows = conn.execute("SELECT code, value_usd, code_type, is_used, used_by, created_at, used_at FROM redeem_codes WHERE is_used = 1 ORDER BY used_at DESC").fetchall()
        else:
            rows = conn.execute("SELECT code, value_usd, code_type, is_used, used_by, created_at, used_at FROM redeem_codes ORDER BY created_at DESC").fetchall()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "Code (卡密)",
        "Value USD (金额 $)",
        "Type (类型)",
        "Status (状态)",
        "Used By (使用者)",
        "Created At (创建时间)",
        "Used At (使用时间)",
        "Redeem URL (激活链接)"
    ])

    domain = getattr(config, "DOMAIN", "jobhunt-pro-mve3.onrender.com")
    base_url = f"https://{domain}" if "http" not in domain and "localhost" not in domain else domain

    for r in rows:
        c = r["code"]
        is_u = bool(r["is_used"])
        st_text = "Used / 已使用" if is_u else "Available / 未使用"
        writer.writerow([
            c,
            f"${float(r['value_usd'] or 0):.2f}",
            r["code_type"] or "sale",
            st_text,
            r["used_by"] or "—",
            r["created_at"] or "—",
            r["used_at"] or "—",
            f"{base_url}/redeem?code={c}"
        ])

    csv_bytes = output.getvalue().encode('utf-8-sig')
    filename = f"JobHunt_All_Codes_{status}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""}
    )


def _is_json_request(request: Request) -> bool:
    """Detect if client prefers or expects JSON response."""
    accept = request.headers.get("accept", "").lower()
    content_type = request.headers.get("content-type", "").lower()
    x_req = request.headers.get("x-requested-with", "").lower()
    return "application/json" in accept or "application/json" in content_type or x_req == "xmlhttprequest" or request.query_params.get("format") == "json"

async def _extract_param_value(request: Request, name: str, default=None):
    """Extracts a parameter from query string, form data, or json body."""
    if name in request.query_params:
        return request.query_params[name]
    try:
        data = await request.json()
        if isinstance(data, dict) and name in data:
            return data[name]
    except Exception:
        pass
    try:
        form = await request.form()
        if name in form:
            return form[name]
    except Exception:
        pass
    return default


@router.post("/admin/delete-code")
@router.get("/admin/delete-code")
async def admin_delete_single_code(request: Request, code: str = None):
    """Delete a single redeem code."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)
    
    target_code = code or await _extract_param_value(request, "code")
    if not target_code:
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Missing code"}, status_code=400)
        return RedirectResponse("/admin?error=Missing+code", status_code=303)

    target_code = str(target_code).strip()
    with get_db() as conn:
        conn.execute("DELETE FROM redeem_codes WHERE code = ?", (target_code,))
        conn.commit()

    if _is_json_request(request):
        return JSONResponse({"status": "success", "message": f"Code {target_code} deleted successfully", "code": target_code})
    return RedirectResponse(f"/admin?success=Deleted+code+{target_code}", status_code=303)


@router.post("/admin/delete-codes")
async def admin_delete_codes(request: Request):
    """Delete selected redeem codes (bulk)."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    codes_list = []
    try:
        data = await request.json()
        if isinstance(data, dict):
            codes_list = data.get("codes", [])
        elif isinstance(data, list):
            codes_list = data
    except Exception:
        pass

    if not codes_list:
        try:
            form = await request.form()
            codes_list = form.getlist("codes")
            if not codes_list:
                raw = form.get("codes", "")
                if raw:
                    codes_list = [c.strip() for c in str(raw).split(",") if c.strip()]
        except Exception:
            pass

    if codes_list:
        with get_db() as conn:
            placeholders = ",".join("?" for _ in codes_list)
            conn.execute(f"DELETE FROM redeem_codes WHERE code IN ({placeholders})", tuple(codes_list))
            conn.commit()
        if _is_json_request(request):
            return JSONResponse({"status": "success", "message": f"Deleted {len(codes_list)} redeem codes", "deleted_count": len(codes_list)})
        return RedirectResponse(f"/admin?success=Deleted+{len(codes_list)}+redeem+codes", status_code=303)
    
    if _is_json_request(request):
        return JSONResponse({"status": "error", "error": "No codes selected"}, status_code=400)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/delete-user")
@router.get("/admin/delete-user")
async def admin_delete_single_user(request: Request, target_user_id: str = None):
    """Delete a single user."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    target_id = target_user_id or await _extract_param_value(request, "target_user_id") or await _extract_param_value(request, "user_id")
    if not target_id:
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Missing user_id"}, status_code=400)
        return RedirectResponse("/admin?error=Missing+user_id", status_code=303)

    target_id = str(target_id).strip()
    with get_db() as conn:
        conn.execute("DELETE FROM users WHERE user_id = ? AND user_type != 'admin'", (target_id,))
        conn.commit()

    if _is_json_request(request):
        return JSONResponse({"status": "success", "message": "User deleted successfully", "user_id": target_id})
    return RedirectResponse("/admin?success=User+deleted+successfully", status_code=303)


@router.post("/admin/delete-users")
async def admin_delete_users(request: Request):
    """Delete selected users (bulk)."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    user_ids = []
    try:
        data = await request.json()
        if isinstance(data, dict):
            user_ids = data.get("user_ids", [])
        elif isinstance(data, list):
            user_ids = data
    except Exception:
        pass

    if not user_ids:
        try:
            form = await request.form()
            user_ids = form.getlist("user_ids")
            if not user_ids:
                raw = form.get("user_ids", "")
                if raw:
                    user_ids = [u.strip() for u in str(raw).split(",") if u.strip()]
        except Exception:
            pass

    if user_ids:
        with get_db() as conn:
            placeholders = ",".join("?" for _ in user_ids)
            conn.execute(f"DELETE FROM users WHERE user_id IN ({placeholders}) AND user_type != 'admin'", tuple(user_ids))
            conn.commit()
        if _is_json_request(request):
            return JSONResponse({"status": "success", "message": f"Deleted {len(user_ids)} users", "deleted_count": len(user_ids)})
        return RedirectResponse(f"/admin?success=Deleted+{len(user_ids)}+users", status_code=303)
    
    if _is_json_request(request):
        return JSONResponse({"status": "error", "error": "No users selected"}, status_code=400)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/delete-campaign")
@router.get("/admin/delete-campaign")
async def admin_delete_single_campaign(request: Request, campaign_id: str = None):
    """Delete a single campaign."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    c_id = campaign_id or await _extract_param_value(request, "campaign_id")
    if not c_id:
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Missing campaign_id"}, status_code=400)
        return RedirectResponse("/admin?error=Missing+campaign_id", status_code=303)

    c_id = str(c_id).strip()
    with get_db() as conn:
        conn.execute("DELETE FROM campaigns WHERE campaign_id = ?", (c_id,))
        conn.commit()

    if _is_json_request(request):
        return JSONResponse({"status": "success", "message": "Campaign deleted successfully", "campaign_id": c_id})
    return RedirectResponse("/admin?success=Campaign+deleted+successfully", status_code=303)


@router.post("/admin/delete-campaigns")
async def admin_delete_campaigns(request: Request):
    """Delete selected campaigns (bulk)."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    campaign_ids = []
    try:
        data = await request.json()
        if isinstance(data, dict):
            campaign_ids = data.get("campaign_ids", [])
        elif isinstance(data, list):
            campaign_ids = data
    except Exception:
        pass

    if not campaign_ids:
        try:
            form = await request.form()
            campaign_ids = form.getlist("campaign_ids")
            if not campaign_ids:
                raw = form.get("campaign_ids", "")
                if raw:
                    campaign_ids = [c.strip() for c in str(raw).split(",") if c.strip()]
        except Exception:
            pass

    if campaign_ids:
        with get_db() as conn:
            placeholders = ",".join("?" for _ in campaign_ids)
            conn.execute(f"DELETE FROM campaigns WHERE campaign_id IN ({placeholders})", tuple(campaign_ids))
            conn.commit()
        if _is_json_request(request):
            return JSONResponse({"status": "success", "message": f"Deleted {len(campaign_ids)} campaigns", "deleted_count": len(campaign_ids)})
        return RedirectResponse(f"/admin?success=Deleted+{len(campaign_ids)}+campaigns", status_code=303)

    if _is_json_request(request):
        return JSONResponse({"status": "error", "error": "No campaigns selected"}, status_code=400)
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/toggle-user")
@router.get("/admin/toggle-user")
async def admin_toggle_user(request: Request, target_user_id: str = None):
    """Activate or deactivate a user."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    target_id = target_user_id or await _extract_param_value(request, "target_user_id") or await _extract_param_value(request, "user_id")
    if not target_id:
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Missing user_id"}, status_code=400)
        return RedirectResponse("/admin?error=Missing+user_id", status_code=303)

    target_id = str(target_id).strip()
    new_status = 1
    with get_db() as conn:
        row = conn.execute("SELECT is_active FROM users WHERE user_id = ?", (target_id,)).fetchone()
        if row:
            row_dict = dict(row)
            new_status = 0 if row_dict.get("is_active") else 1
            conn.execute("UPDATE users SET is_active = ? WHERE user_id = ?", (new_status, target_id))
            conn.commit()

    if _is_json_request(request):
        return JSONResponse({"status": "success", "user_id": target_id, "is_active": new_status, "message": f"User status changed to {'Active' if new_status else 'Inactive'}"})
    return RedirectResponse("/admin", status_code=303)


@router.post("/admin/create-flash-sale")
@router.get("/admin/create-flash-sale")
async def admin_create_flash_sale(
    request: Request,
    title: str = None,
    discount_percent: float = None,
    duration_hours: float = None,
):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from datetime import timedelta
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    sale_title = title or await _extract_param_value(request, "title") or "VIP Exclusive Deal"
    sale_discount = discount_percent if discount_percent is not None else await _extract_param_value(request, "discount_percent", 50)
    sale_duration = duration_hours if duration_hours is not None else await _extract_param_value(request, "duration_hours", 24)

    try:
        sale_discount = float(sale_discount)
    except Exception:
        sale_discount = 50.0
    try:
        sale_duration = float(sale_duration)
    except Exception:
        sale_duration = 24.0

    with get_db() as conn:
        now = datetime.now()
        end_time = now + timedelta(hours=sale_duration)
        cursor = conn.execute(
            "INSERT INTO flash_sales (title, discount_percent, start_time, end_time, active) VALUES (?, ?, ?, ?, 1)",
            (sale_title, sale_discount, now.isoformat(), end_time.isoformat())
        )
        conn.commit()
        new_id = cursor.lastrowid

    if _is_json_request(request):
        return JSONResponse({
            "status": "success",
            "message": f"Flash sale activated: {sale_title} ({sale_discount}% off, {sale_duration}h)",
            "sale": {
                "id": new_id,
                "title": sale_title,
                "discount_percent": sale_discount,
                "duration_hours": sale_duration,
                "start_time": now.isoformat(),
                "end_time": end_time.isoformat(),
                "active": 1
            }
        })
    return RedirectResponse(f"/admin?success=Flash+sale+activated:+{sale_title}+({sale_discount}%+off,+{sale_duration}h)", status_code=303)


@router.post("/admin/end-flash-sale")
@router.post("/admin/pause-flash-sale")
@router.get("/admin/pause-flash-sale")
async def admin_pause_flash_sale(request: Request, sale_id: int = None):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    target_id = sale_id or await _extract_param_value(request, "sale_id") or await _extract_param_value(request, "id")
    if not target_id:
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Missing sale_id"}, status_code=400)
        return RedirectResponse("/admin?error=Missing+sale_id", status_code=303)

    with get_db() as conn:
        conn.execute("UPDATE flash_sales SET active = 0 WHERE id = ?", (int(target_id),))
        conn.commit()

    if _is_json_request(request):
        return JSONResponse({"status": "success", "message": f"Flash sale #{target_id} paused successfully", "sale_id": int(target_id), "active": 0})
    return RedirectResponse(f"/admin?success=Flash+sale+{target_id}+paused+successfully", status_code=303)


@router.post("/admin/resume-flash-sale")
@router.get("/admin/resume-flash-sale")
async def admin_resume_flash_sale(
    request: Request,
    sale_id: int = None,
    extend_hours: float = None
):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from datetime import timedelta
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    target_id = sale_id or await _extract_param_value(request, "sale_id") or await _extract_param_value(request, "id")
    if not target_id:
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Missing sale_id"}, status_code=400)
        return RedirectResponse("/admin?error=Missing+sale_id", status_code=303)

    hours = extend_hours if extend_hours is not None else await _extract_param_value(request, "extend_hours", 24)
    try:
        hours = float(hours)
    except Exception:
        hours = 24.0

    target_id = int(target_id)
    with get_db() as conn:
        now = datetime.now()
        row = conn.execute("SELECT * FROM flash_sales WHERE id = ?", (target_id,)).fetchone()
        if row:
            row_dict = dict(row)
            end_t = str(row_dict.get("end_time") or "")
            # If expired or in the past, extend from now
            if not end_t or end_t <= now.isoformat():
                new_end = now + timedelta(hours=hours)
                conn.execute(
                    "UPDATE flash_sales SET active = 1, start_time = ?, end_time = ? WHERE id = ?",
                    (now.isoformat(), new_end.isoformat(), target_id)
                )
            else:
                conn.execute("UPDATE flash_sales SET active = 1 WHERE id = ?", (target_id,))
            conn.commit()

    if _is_json_request(request):
        return JSONResponse({"status": "success", "message": f"Flash sale #{target_id} resumed and extended by +{hours}h", "sale_id": target_id, "active": 1})
    return RedirectResponse(f"/admin?success=Flash+sale+{target_id}+resumed+and+activated", status_code=303)


@router.post("/admin/delete-flash-sale")
@router.get("/admin/delete-flash-sale")
async def admin_delete_flash_sale(request: Request, sale_id: int = None):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    target_id = sale_id or await _extract_param_value(request, "sale_id") or await _extract_param_value(request, "id")
    if not target_id:
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Missing sale_id"}, status_code=400)
        return RedirectResponse("/admin?error=Missing+sale_id", status_code=303)

    target_id = int(target_id)
    with get_db() as conn:
        conn.execute("DELETE FROM flash_sales WHERE id = ?", (target_id,))
        conn.commit()

    if _is_json_request(request):
        return JSONResponse({"status": "success", "message": f"Flash sale #{target_id} deleted successfully", "sale_id": target_id})
    return RedirectResponse(f"/admin?success=Flash+sale+{target_id}+deleted", status_code=303)


@router.post("/admin/delete-flash-sales")
async def admin_delete_flash_sales(request: Request):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        return RedirectResponse("/login", status_code=303)

    sale_ids = []
    try:
        data = await request.json()
        if isinstance(data, dict):
            sale_ids = data.get("sale_ids", [])
        elif isinstance(data, list):
            sale_ids = data
    except Exception:
        pass

    if not sale_ids:
        try:
            form = await request.form()
            sale_ids = form.getlist("sale_ids")
            if not sale_ids:
                raw = form.get("sale_ids", "")
                if raw:
                    sale_ids = [s.strip() for s in str(raw).split(",") if s.strip()]
        except Exception:
            pass

    if not sale_ids:
        if _is_json_request(request):
            return JSONResponse({"status": "error", "error": "No flash sales selected"}, status_code=400)
        return RedirectResponse("/admin?error=No+flash+sales+selected+for+deletion", status_code=303)

    cleaned_ids = [int(s) for s in sale_ids if str(s).isdigit()]
    if cleaned_ids:
        with get_db() as conn:
            placeholders = ",".join(["?"] * len(cleaned_ids))
            conn.execute(f"DELETE FROM flash_sales WHERE id IN ({placeholders})", cleaned_ids)
            conn.commit()

    if _is_json_request(request):
        return JSONResponse({"status": "success", "message": f"{len(cleaned_ids)} flash sales deleted successfully", "deleted_count": len(cleaned_ids)})
    return RedirectResponse(f"/admin?success={len(cleaned_ids)}+flash+sales+deleted+successfully", status_code=303)


@router.post("/admin/send-manual-email")
def admin_send_manual_email(
    request: Request,
    background_tasks: BackgroundTasks,
    to_email: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import _bg_send_manual_email, require_admin
    admin_id = require_admin(request)
    if not admin_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        admin_row = conn.execute("SELECT email FROM users WHERE user_id = ?", (admin_id,)).fetchone()
        admin_email = admin_row["email"] if admin_row else "admin"

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO manual_emails (user_id, to_email, subject, body, price_usd, admin_email, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (admin_id, to_email, subject, body, 0.0, admin_email, "pending")
        )
        email_id = cursor.lastrowid
        conn.commit()
        pass  # conn.close()

        background_tasks.add_task(_bg_send_manual_email, to_email, subject, body, "Admin", admin_id, email_id)
        return RedirectResponse(
            f"/admin?success=Email+queued+for+delivery+to+{to_email}+(subject: {subject[:30]})+&#x2014;+$0.00+(admin+free)",
            status_code=303,
        )


@router.get("/admin/user/{target_user_id}", response_class=HTMLResponse)
def admin_user_detail(request: Request, target_user_id: str):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (target_user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/admin", status_code=303)
        user = dict(user_row)

        campaigns = [dict(r) for r in conn.execute(
            "SELECT * FROM campaigns WHERE user_id = ? ORDER BY created_at DESC", (target_user_id,)
        ).fetchall()]
        transactions = [dict(r) for r in conn.execute(
            "SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 30", (target_user_id,)
        ).fetchall()]
        orders = [dict(r) for r in conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 20", (target_user_id,)
        ).fetchall()]
        pass  # conn.close()

        content_html = render_template("admin_user.html", request=request,
            user=user, campaigns=campaigns,
            transactions=transactions, orders=orders
        )
        return HTMLResponse(_build_dashboard_shell(None, require_admin(request), content_html, f"User {user.get('name', 'Details')}", "admin", request=request))


@router.get("/antigravity", response_class=HTMLResponse)
def antigravity_page(request: Request):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    return templates.TemplateResponse(request, "antigravity.html")


# ---------------------------------------------------------------------------
# AI Cache Admin Endpoints
# ---------------------------------------------------------------------------

def _require_admin(request: Request):
    """Raise 403 if request is not from an admin user."""
    from web.shared import get_db, get_verified_user_id, is_admin_email
    user_id = get_verified_user_id(request)
    if not user_id:
        raise HTTPException(status_code=403, detail="Admin privileges required")

    with get_db() as conn:
        try:
            row = conn.execute("SELECT * FROM users WHERE user_id = ? OR id = ? OR LOWER(email) = ?", (user_id, user_id, str(user_id).lower())).fetchone()
        except Exception:
            row = None

        user_dict = dict(row) if row else {}
        email = (user_dict.get("email") or "").strip().lower()
        user_type = str(user_dict.get("user_type") or "").strip().lower()
        is_admin_val = bool(user_dict.get("is_admin"))

        if is_admin_email(email) or is_admin_email(str(user_id)):
            return user_id
        if (user_type == "admin" or is_admin_val) and is_admin_email(email):
            return user_id

    raise HTTPException(status_code=403, detail="Admin privileges required")



@router.get("/api/admin/ai-cache/stats")
def ai_cache_stats(request: Request):
    """Return AI cache statistics: total entries, fresh entries, expired entries."""
    _require_admin(request)
    try:
        from core.ai_cache import get_stats
        return get_stats()
    except Exception as e:
        return {"error": str(e)}


@router.post("/api/admin/ai-cache/purge")
def ai_cache_purge(request: Request):
    """Purge expired AI cache entries (older than 7 days)."""
    _require_admin(request)
    try:
        from core.ai_cache import purge_expired
        deleted = purge_expired()
        return {"status": "ok", "deleted": deleted}
    except Exception as e:
        return {"status": "error", "error": str(e)}
