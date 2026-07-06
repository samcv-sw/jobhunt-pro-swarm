"""
routers/admin.py - Admin Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import os
import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["admin"])

def _deps():
    from web.shared import get_db, get_verified_user_id, templates, config
    from web.app_v2 import render_template, _build_dashboard_shell
    return get_db, get_verified_user_id, templates, config, render_template, _build_dashboard_shell

@router.post("/admin/panic-toggle")
def admin_panic_toggle(request: Request):
    """Toggles the Iron Cloak Panic Mode on or off."""
    get_db, get_verified_user_id, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"status": "error", "error": "Unauthorized"}, status_code=403)
        
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
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
        
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
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
        
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    
    if not user or user.get("user_type") != "admin":
        return HTMLResponse("<h2>403 Forbidden</h2><p>You do not have permission to view this page.</p>", status_code=403)
        
    pa_domain = os.getenv("PA_DOMAIN", "jhfguf.pythonanywhere.com")
    error_log_path = f"/var/log/{pa_domain}.error.log"
    server_log_path = f"/var/log/{pa_domain}.server.log"
    
    error_log_content = "Log file not found."
    server_log_content = "Log file not found."
    
    try:
        if os.path.exists(error_log_path):
            with open(error_log_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                error_log_content = ''.join(lines[-100:])
        else:
            error_log_content = f"Log file not found at {error_log_path}"
    except Exception as e:
        error_log_content = f"Error reading log: {str(e)}"
        
    try:
        if os.path.exists(server_log_path):
            with open(server_log_path, 'r', encoding='utf-8', errors='replace') as f:
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
            
        db = get_db()
        user_admin = db.execute("SELECT * FROM users WHERE user_id = ?", (admin_id,)).fetchone()
        if not user_admin or user_admin.get("user_type") != "admin":
            db.close()
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

        db.close()
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
        return HTMLResponse(f"<h2>Analytics Error</h2><pre>{e}</pre>", status_code=500)