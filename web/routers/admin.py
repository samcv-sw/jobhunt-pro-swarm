"""
routers/admin.py - Admin Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])

def _deps():
    from web.app_v2 import _build_dashboard_shell, render_template
    from web.shared import config, get_db, get_verified_user_id, templates
    return get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell

@router.post("/admin/panic-toggle")
def admin_panic_toggle(request: Request):
    """Toggles the Iron Cloak Panic Mode on or off."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        pass  # conn.close()

        if not user or user.get("user_type") != "admin":
            return JSONResponse({"status": "error", "error": "Forbidden"}, status_code=403)

        from core.panic_mode import toggle_panic_mode
        new_state = toggle_panic_mode()
        return JSONResponse({"status": "success", "panic_mode_active": new_state})

@router.get("/admin/viral-factory", response_class=HTMLResponse)
def admin_viral_factory(request: Request):
    """View and download generated viral MP4 videos."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        pass  # conn.close()

        if not user or user.get("user_type") != "admin":
            return HTMLResponse("<h2>403 Forbidden</h2><p>You do not have permission to view this page.</p>", status_code=403)

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
    from fastapi.responses import FileResponse
    file_path = os.path.join("cache/viral_videos", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename, media_type="video/mp4")
    return HTMLResponse("File not found", status_code=404)

@router.get("/admin/logs", response_class=HTMLResponse)
def admin_logs(request: Request):
    """Secure Log Viewer - Only accessible by admins."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        pass  # conn.close()

        if not user or user.get("user_type") != "admin":
            return HTMLResponse("<h2>403 Forbidden</h2><p>You do not have permission to view this page.</p>", status_code=403)

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
    get_db, get_verified_user_id, _, _, render_template, _build_dashboard_shell = _deps()
    try:
        admin_id = get_verified_user_id(req)
        if not admin_id:
            return RedirectResponse("/login", status_code=303)

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
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import get_payment_stats, require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

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

        redeem_codes = [dict(r) for r in conn.execute(
            "SELECT code, value_usd, code_type, is_used, used_by, created_at FROM redeem_codes ORDER BY created_at DESC LIMIT 20"
        ).fetchall()]

        manual_emails = [dict(r) for r in conn.execute(
            "SELECT to_email, subject, price_usd, status, created_at FROM manual_emails ORDER BY created_at DESC LIMIT 20"
        ).fetchall()]

        manual_email_count = conn.execute("SELECT COUNT(*) FROM manual_emails").fetchone()[0]
        manual_email_revenue = conn.execute("SELECT COALESCE(SUM(price_usd),0) FROM manual_emails WHERE status='sent'").fetchone()[0]

        flash_sales = [dict(r) for r in conn.execute(
            "SELECT * FROM flash_sales ORDER BY created_at DESC LIMIT 20"
        ).fetchall()]

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
            payment_stats=payment_stats,
            manual_emails=manual_emails,
            flash_sales=flash_sales,
        )
        return HTMLResponse(_build_dashboard_shell(None, require_admin(request), content_html, "Admin Panel", "admin"))


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
        conn.execute("UPDATE users SET password_hash = ? WHERE email = ?",
                     (admin_hash, "samsalameh.cv@gmail.com"))
        conn.commit()
        pass  # conn.close()
        logger.info("Password reset for samsalameh.cv@gmail.com via admin-reset-pw")
        return {"status": "password updated for samsalameh.cv@gmail.com"}


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


@router.post("/admin/toggle-user")
def admin_toggle_user(request: Request, target_user_id: str = Form(...)):
    """Activate or deactivate a user."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        row = conn.execute("SELECT is_active FROM users WHERE user_id = ?", (target_user_id,)).fetchone()
        if row:
            new_status = 0 if row["is_active"] else 1
            conn.execute("UPDATE users SET is_active = ? WHERE user_id = ?", (new_status, target_user_id))
            conn.commit()
        pass  # conn.close()
        return RedirectResponse("/admin", status_code=303)


@router.post("/admin/free-campaign")
def admin_free_campaign(
    request: Request,
    target_email: str = Form(...),
    company_count: int = Form(100),
):
    """Give a user a free campaign."""
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT user_id FROM users WHERE email = ?", (target_email,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/admin?error=user_not_found", status_code=303)

        user_id = user_row["user_id"]
        profile_row = conn.execute("SELECT id FROM cv_profiles WHERE user_id = ? LIMIT 1", (user_id,)).fetchone()
        if not profile_row:
            conn.execute(
                "INSERT INTO cv_profiles (user_id, profile_name, cv_text) VALUES (?, ?, ?)",
                (user_id, "Admin Created Profile", "Professional profile created by admin")
            )
            conn.commit()
            profile_row = conn.execute("SELECT id FROM cv_profiles WHERE user_id = ? LIMIT 1", (user_id,)).fetchone()

        campaign_id = f"camp_{uuid.uuid4().hex[:16]}"
        order_id = f"ord_{uuid.uuid4().hex[:16]}"

        conn.execute(
            "INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status) VALUES (?,?,?,?,?,?,?,?)",
            (order_id, user_id, "campaign", "admin_free", company_count, 0, "admin", "completed")
        )
        conn.execute(
            "INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, total_companies) VALUES (?,?,?,?,?)",
            (campaign_id, user_id, order_id, profile_row["id"], company_count)
        )
        conn.commit()
        pass  # conn.close()

        from core.job_queue import enqueue_task
        try:
            enqueue_task("run_campaign", {"campaign_id": campaign_id})
        except Exception as e:
            logger.error(f"[QUEUE] Error enqueuing admin campaign {campaign_id}: {e}")

        return RedirectResponse(f"/admin?success=Free+campaign+created+for+{target_email}", status_code=303)


@router.post("/admin/create-flash-sale")
def admin_create_flash_sale(
    request: Request,
    title: str = Form(...),
    discount_percent: float = Form(...),
    duration_hours: float = Form(24),
):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from datetime import timedelta

    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)
    with get_db() as conn:
        now = datetime.now()
        end_time = now + timedelta(hours=duration_hours)
        conn.execute(
            "INSERT INTO flash_sales (title, discount_percent, start_time, end_time) VALUES (?, ?, ?, ?)",
            (title, discount_percent, now.isoformat(), end_time.isoformat())
        )
        conn.commit()
        pass  # conn.close()
        return RedirectResponse(f"/admin?success=Flash+sale+created:+{title}+({discount_percent}%+off,+{duration_hours}h)", status_code=303)


@router.post("/admin/end-flash-sale")
def admin_end_flash_sale(request: Request, sale_id: int = Form(...)):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/login", status_code=303)
    with get_db() as conn:
        conn.execute("UPDATE flash_sales SET active = 0 WHERE id = ?", (sale_id,))
        conn.commit()
        pass  # conn.close()
        return RedirectResponse(f"/admin?success=Flash+sale+{sale_id}+ended", status_code=303)


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
        return HTMLResponse(_build_dashboard_shell(None, require_admin(request), content_html, f"User {user.get('name', 'Details')}", "admin"))


@router.get("/antigravity", response_class=HTMLResponse)
def antigravity_page(request: Request):
    get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell = _deps()
    return templates.TemplateResponse(request, "antigravity.html")
