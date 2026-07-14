"""
=============================================================================
APPENDED ROUTES — v3/v4 Templates (Landing, Dashboard, Pricing, Auth, Checkout, Upload CV)
Append this file to the end of app_v2.py on the server.
=============================================================================
"""
import logging
from datetime import datetime
from typing import Any

# The following type stub references are for lint/typing completeness in standalone mode
try:
    from starlette.requests import Request
    from starlette.responses import HTMLResponse, RedirectResponse
except ImportError:
    pass

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. LANDING PAGE V4 — /v4
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/v4", response_class=HTMLResponse)
def landing_v4(request: Request) -> HTMLResponse:
    """Modern landing page v4 with cyberpunk glassmorphism theme."""
    try:
        earnings: dict[str, int] = {"total_all": 15000000, "today": 25000}
        tiers: list[dict[str, Any]] = get_all_pricing() if 'get_all_pricing' in globals() else []
        return templates.TemplateResponse(request, "index_v4.html", {
            "earnings": earnings,
            "tiers": tiers,
            "VERSION": config.VERSION,
        })
    except Exception as e:
        logger.error(f"Error rendering landing_v4 page: {e}")
        return HTMLResponse("<h3>Internal Server Error</h3>", status_code=500)

# ─────────────────────────────────────────────────────────────────────────────
# 2. DASHBOARD V3 — /dashboard/v3
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/dashboard/v3", response_class=HTMLResponse)
def dashboard_v3(request: Request) -> Any:
    """Enhanced dashboard v3 with loading states, notifications, keyboard shortcuts."""
    try:
        user_id = get_verified_user_id(request)
        if not user_id:
            return RedirectResponse("/login", status_code=303)

        conn = get_db()
        try:
            user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if not user_row:
                return RedirectResponse("/login", status_code=303)
            user = dict(user_row)

            profiles = [dict(r) for r in conn.execute(
                "SELECT * FROM cv_profiles WHERE user_id = ?", (user_id,)
            ).fetchall()]

            campaigns = [dict(r) for r in conn.execute("""
                SELECT c.*, COUNT(ce.id) as total_emails,
                SUM(CASE WHEN ce.status = 'sent' THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN ce.opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened
                FROM campaigns c
                LEFT JOIN campaign_emails ce ON c.campaign_id = ce.campaign_id
                WHERE c.user_id = ?
                GROUP BY c.campaign_id
                ORDER BY c.created_at DESC LIMIT 10
            """, (user_id,)).fetchall()]

            transactions = [dict(r) for r in conn.execute(
                "SELECT * FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
                (user_id,)
            ).fetchall()]

            referrals_row = conn.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,)
            ).fetchone()
            referrals = referrals_row[0] if referrals_row else 0

            pipeline_emails = [dict(r) for r in conn.execute('''
                SELECT ce.id, ce.company_name, ce.job_title,
                ce.pipeline_stage, ce.status, ce.sent_at, ce.opened_at, ce.responded_at
                FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE c.user_id = ?
                ORDER BY ce.sent_at DESC LIMIT 30
            ''', (user_id,)).fetchall()]

            pipeline_counts = {s: 0 for s in ["discovered", "applied", "followed_up", "interview", "offer"]}
            for row in conn.execute('''
                SELECT COALESCE(ce.pipeline_stage, 'discovered') as stage, COUNT(*) as cnt
                FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE c.user_id = ?
                GROUP BY COALESCE(ce.pipeline_stage, 'discovered')
            ''', (user_id,)).fetchall():
                pipeline_counts[row["stage"]] = row["cnt"]
        finally:
            conn.close()

        total_sent = sum(c.get('sent', 0) or 0 for c in campaigns)
        total_opened = sum(c.get('opened', 0) or 0 for c in campaigns)
        responses = sum(1 for e in pipeline_emails if e.get('responded_at'))
        interviews = sum(1 for e in pipeline_emails if e.get('pipeline_stage') == 'interview')
        open_rate = round((total_opened / total_sent * 100) if total_sent > 0 else 0)
        response_rate = round((responses / total_sent * 100) if total_sent > 0 else 0)

        stats: dict[str, Any] = {
            'emails_sent': total_sent,
            'emails_opened': total_opened,
            'responses': responses,
            'interviews': interviews,
            'open_rate': open_rate,
            'response_rate': response_rate,
        }

        referral_link = f"{config.SITE_URL}/register?ref={user_id}"
        content = render_template("dashboard_v3.html",
            request=request, active_page="dashboard",
            user=user, profiles=profiles, profile_count=len(profiles),
            campaigns=campaigns, campaign_count=len(campaigns),
            transactions=transactions, referrals=referrals,
            referral_link=referral_link,
            pipeline_emails=pipeline_emails, pipeline_counts=pipeline_counts,
            stats=stats, candidates=[]
        )
        return HTMLResponse(_build_dashboard_shell(user, user_id, content, "Dashboard", "dashboard"))
    except Exception as e:
        logger.error(f"Error rendering dashboard_v3: {e}")
        return HTMLResponse("<h3>Internal Server Error</h3>", status_code=500)

# ─────────────────────────────────────────────────────────────────────────────
# 3. PRICING V3 — /pricing/v3
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/pricing/v3", response_class=HTMLResponse)
def pricing_v3(request: Request) -> HTMLResponse:
    """Enhanced pricing page v3 with billing toggle, flash sale countdown, bulk discount."""
    try:
        tiers: list[dict[str, Any]] = get_all_pricing() if 'get_all_pricing' in globals() else []
        services_list: list[dict[str, Any]] = [
            {"name": "AI Auto-Apply Engine", "desc": "Automated job applications 24/7", "price": 9.99},
            {"name": "Smart Resume Tailoring", "desc": "AI optimizes your CV per job", "price": 4.99},
            {"name": "Email Follow-up Automation", "desc": "Auto follow-ups with tracking", "price": 6.99},
            {"name": "Interview Scheduler", "desc": "AI schedules your interviews", "price": 14.99},
            {"name": "LinkedIn Profile Optimizer", "desc": "AI-enhanced LinkedIn presence", "price": 3.99},
            {"name": "Cover Letter Generator", "desc": "Custom cover letters per job", "price": 2.99},
        ]
        pricing: dict[str, Any] = {"tiers": tiers, "services": services_list}
        return templates.TemplateResponse(request, "pricing_v3.html", {
            "pricing": pricing,
            "VERSION": config.VERSION,
        })
    except Exception as e:
        logger.error(f"Error rendering pricing_v3 page: {e}")
        return HTMLResponse("<h3>Internal Server Error</h3>", status_code=500)

# ─────────────────────────────────────────────────────────────────────────────
# 4. LOGIN V2 — /login/v2
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/login/v2", response_class=HTMLResponse)
def login_v2(request: Request) -> HTMLResponse:
    """Enhanced login page v2 with password strength meter, particles."""
    try:
        return templates.TemplateResponse(request, "login_v2.html", {
            "VERSION": config.VERSION,
        })
    except Exception as e:
        logger.error(f"Error rendering login_v2 page: {e}")
        return HTMLResponse("<h3>Internal Server Error</h3>", status_code=500)

# ─────────────────────────────────────────────────────────────────────────────
# 5. REGISTER V2 — /register/v2
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/register/v2", response_class=HTMLResponse)
def register_v2(request: Request) -> HTMLResponse:
    """Enhanced registration page v2 with plan selector UX."""
    try:
        return templates.TemplateResponse(request, "register_v2.html", {
            "VERSION": config.VERSION,
        })
    except Exception as e:
        logger.error(f"Error rendering register_v2 page: {e}")
        return HTMLResponse("<h3>Internal Server Error</h3>", status_code=500)

# ─────────────────────────────────────────────────────────────────────────────
# 6. CHECKOUT V3 — /checkout/v3
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/checkout/v3", response_class=HTMLResponse)
def checkout_v3(request: Request) -> HTMLResponse:
    """Enhanced checkout page v3 with payment progress steps, QR codes."""
    try:
        order: dict[str, Any] = {
            "id": "DEMO-ORDER-001",
            "status": "pending",
            "amount_usd": 29.99,
            "package_name": "Premium JobHunter Pro",
            "created_at": datetime.now().isoformat(),
            "payment_method": "crypto",
        }
        return templates.TemplateResponse(request, "checkout_v3.html", {
            "order": order,
            "VERSION": config.VERSION,
        })
    except Exception as e:
        logger.error(f"Error rendering checkout_v3 page: {e}")
        return HTMLResponse("<h3>Internal Server Error</h3>", status_code=500)

# ─────────────────────────────────────────────────────────────────────────────
# 7. UPLOAD CV V3 — /upload-cv/v3
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/upload-cv/v3", response_class=HTMLResponse)
def upload_cv_v3(request: Request) -> Any:
    """Enhanced CV upload page v3 with drag-drop, progress bar, AI analysis."""
    try:
        user_id = get_verified_user_id(request)
        if not user_id:
            return RedirectResponse("/login", status_code=303)
        conn = get_db()
        try:
            user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            user = dict(user_row) if user_row else {}
        finally:
            conn.close()
        content = render_template("upload_cv_v3.html", user=user, user_id=user_id)
        return HTMLResponse(_build_dashboard_shell(user, user_id, content, "Upload CV", "upload-cv"))
    except Exception as e:
        logger.error(f"Error rendering upload_cv_v3 page: {e}")
        return HTMLResponse("<h3>Internal Server Error</h3>", status_code=500)

# ─────────────────────────────────────────────────────────────────────────────
# END OF APPENDED ROUTES
# ─────────────────────────────────────────────────────────────────────────────
