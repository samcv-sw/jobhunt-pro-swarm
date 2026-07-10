"""
routers/employers.py - Employers Router (FastAPI APIRouter)
"""
import os
import uuid
import logging
import re
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["employers"])

def _deps():
    from web.shared import get_db, get_verified_user_id, templates, is_admin_email, config
    from web.app_v2 import render_template, _public_shell, _build_dashboard_shell, send_email_via_brevo_http
    return get_db, get_verified_user_id, templates, is_admin_email, config, render_template, _public_shell, _build_dashboard_shell, send_email_via_brevo_http

@router.get("/employers", response_class=HTMLResponse)
def employers_page(request: Request):
    """Employers landing page — public, no login required."""
    get_db_fn, get_verified_user_id_fn, _, _, _, render_template_fn, _public_shell_fn, _build_dashboard_shell_fn, _ = _deps()
    user_id = get_verified_user_id_fn(request)
    if user_id:
        conn = get_db_fn()
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        user = dict(user_row) if user_row else {}
        content = render_template_fn("for_employers.html", user=user, active_page="employers")
        return HTMLResponse(_build_dashboard_shell_fn(user, user_id, content, "For Employers", "employers", request=request))
    content = render_template_fn("for_employers.html", request=request, active_page="employers", user=None)
    return HTMLResponse(_public_shell_fn(content, "For Employers — JobHunt Pro"))

@router.post("/api/employer/post-job")
def api_employer_post_job(
    request: Request,
    company_name: str = Form(...),
    job_title: str = Form(...),
    location: str = Form(...),
    category: str = Form(""),
    salary: str = Form(""),
    contact_email: str = Form(...),
    description: str = Form(...),
    apply_url: str = Form(""),
    logo_url: str = Form(""),
    tier: str = Form("basic"),
    price: float = Form(1.0),
    duration_days: int = Form(30),
    is_bulk: str = Form("0"),
    bulk_count: int = Form(0),
    addons: str = Form("[]"),
):
    """Employers post jobs — supports subscriptions, add-ons, bulk packages."""
    get_db_fn, _, _, _, _, _, _, _, send_email_via_brevo_http_fn = _deps()

    # Validate
    if not company_name or not job_title or not location or not contact_email or not description:
        return {"status": "error", "message": "All required fields must be filled."}

    # Validate email
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", contact_email):
        return {"status": "error", "message": "Invalid email address."}

    # Validate job is not fake/scam
    scam_keywords = ["make money fast", "work from home earn", "pyramid", "multi-level",
                     "$$$", "get rich", "no experience needed", "earn daily",
                     "passive income", "investment opportunity", "crypto trading",
                     "forex trading", "binary options", "money transfer agent",
                     "work from home $1000", "easy money", "earn $500"]
    combined_text = (description + " " + job_title).lower()
    for kw in scam_keywords:
        if kw in combined_text:
            return {"status": "error", "message": "This job appears to contain prohibited content. Legitimate jobs only."}

    # Validate company name
    if len(company_name) < 2 or len(company_name) > 100:
        return {"status": "error", "message": "Company name must be 2-100 characters."}

    # Parse addons
    try:
        addon_list = json.loads(addons) if addons else []
    except (json.JSONDecodeError, TypeError):
        addon_list = []

    is_bulk_bool = (is_bulk == "1")
    bulk_cnt = bulk_count if is_bulk_bool else 1
    actual_tier = tier  # single post tier, or bulk tier
    duration = max(30, min(365, duration_days))  # clamp 30-365

    try:
        conn = get_db_fn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS posted_jobs (
                job_id TEXT PRIMARY KEY,
                company_name TEXT NOT NULL,
                job_title TEXT NOT NULL,
                location TEXT NOT NULL,
                category TEXT DEFAULT '',
                salary TEXT DEFAULT '',
                contact_email TEXT NOT NULL,
                description TEXT NOT NULL,
                apply_url TEXT DEFAULT '',
                logo_url TEXT DEFAULT '',
                tier TEXT DEFAULT 'basic',
                price REAL DEFAULT 1.0,
                duration_days INTEGER DEFAULT 30,
                is_bulk INTEGER DEFAULT 0,
                bulk_count INTEGER DEFAULT 0,
                addons TEXT DEFAULT '[]',
                status TEXT DEFAULT 'pending',
                views INTEGER DEFAULT 0,
                applications INTEGER DEFAULT 0,
                google_jobs_id TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP DEFAULT (datetime('now', '+30 days'))
            )
        """)
        # Migrate old table — add missing columns if needed
        existing = [c[1] for c in conn.execute("PRAGMA table_info(posted_jobs)").fetchall()]
        for col, coltype in [('duration_days','INTEGER DEFAULT 30'),('is_bulk','INTEGER DEFAULT 0'),('bulk_count','INTEGER DEFAULT 0'),('addons',"TEXT DEFAULT '[]'"),('applications','INTEGER DEFAULT 0'),('google_jobs_id',"TEXT DEFAULT ''")]:
            if col not in existing:
                try:
                    conn.execute(f"ALTER TABLE posted_jobs ADD COLUMN {col} {coltype}")
                except Exception as e:
                    err_msg = str(e).lower()
                    if "already exists" in err_msg or "duplicate column" in err_msg:
                        logger.info(f"Column {col} already exists in posted_jobs (handled gracefully)")
                    else:
                        raise e
        conn.commit()

        job_ids = []
        for i in range(bulk_cnt):
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            job_ids.append(job_id)
            expires = datetime.now() + timedelta(days=duration)
            conn.execute("""
                INSERT INTO posted_jobs (job_id, company_name, job_title, location, category,
                    salary, contact_email, description, apply_url, logo_url, tier, price,
                    duration_days, is_bulk, bulk_count, addons, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, company_name, job_title, location, category,
                  salary, contact_email, description, apply_url, logo_url, actual_tier,
                  price / bulk_cnt, duration, 1 if is_bulk_bool else 0, bulk_cnt,
                  json.dumps(addon_list), expires.isoformat()))

        conn.commit()
        conn.close()

        addon_names = [a.get('name','').replace('_',' ').title() for a in addon_list]
        addon_str = f" + {' + '.join(addon_names)}" if addon_names else ""

        logger.info(f"[EMPLOYER] {bulk_cnt} job(s) posted: {job_title} at {company_name} ({actual_tier} — ${price}{addon_str} / {duration}d)")

        job_tracking_links = ''.join([
            f'<tr><td style="padding:3px 0;">📋 <code>{jid}</code></td>'
            f'<td><a href="https://jhfguf.pythonanywhere.com/employer/track?email={contact_email}&job_id={jid}" '
            f'style="color:#60a5fa;font-size:0.85em;">📊 Track this job →</a></td></tr>'
            for jid in job_ids
        ])
        # Send confirmation email
        try:
            bulk_info = f"<p><strong>Package:</strong> {bulk_cnt} post(s)</p>" if is_bulk_bool else ""
            dur_info = f"<p><strong>Duration:</strong> {duration} days</p>"
            addon_html = ""
            if addon_names:
                addon_html = f"<p><strong>Power-Ups:</strong> {', '.join(addon_names)}</p>"
            send_email_via_brevo_http_fn(
                to_email=contact_email,
                company_name=company_name,
                job_title=job_title,
                custom_body=f"""
                <h2>✅ Your Job Posting is Live!</h2>
                <p>Thank you for choosing <strong>JobHunt Pro</strong>!</p>
                <p><strong>Job:</strong> {job_title}<br>
                <strong>Company:</strong> {company_name}<br>
                <strong>Plan:</strong> {actual_tier.title()} (${price})</p>
                {bulk_info}{dur_info}{addon_html}
                <p>Your job is now visible to thousands of qualified candidates. You'll receive applications directly at this email.</p>
                <hr style="border:1px solid rgba(255,255,255,.1);margin:16px 0;">
                <h3 style="margin-bottom:8px;">📊 Track Your Job Performance</h3>
                <p style="margin-bottom:8px;">Click below to see views, applications, and status:</p>
                <table style="width:100%;border-collapse:collapse;">{job_tracking_links}</table>
                <p style="margin-top:12px;">🔗 <a href="https://jhfguf.pythonanywhere.com/employer/track?email={contact_email}" style="color:#f59e0b;">View ALL your jobs →</a></p>
                <p style="color:#94a3b8;font-size:0.85em;">Job IDs: {', '.join(job_ids)}<br>Expires: {duration} days from now</p>
                """,
                sender_name="JobHunt Pro",
                subject=f"✅ Job Posted: {job_title} at {company_name}"
            )
        except Exception as e:
            logger.warning(f"[EMPLOYER] Confirmation email failed: {e}")

        bulk_msg = f" {bulk_cnt} jobs posted!" if is_bulk_bool else ""
        return {
            "status": "ok",
            "message": f"🎉 Job posted successfully! Your listing is live for {duration} days.{bulk_msg} Confirmation sent to {contact_email}.",
            "job_ids": job_ids,
            "price": price
        }
    except Exception as e:
        logger.error(f"[EMPLOYER] Post job failed: {e}")
        return {"status": "error", "message": "Something went wrong. Please try again or contact us."}

@router.get("/api/employer/jobs")
def api_employer_list_jobs():
    """List all active posted jobs (public)."""
    get_db_fn, _, _, _, _, _, _, _, _ = _deps()
    try:
        conn = get_db_fn()
        conn.execute("""CREATE TABLE IF NOT EXISTS posted_jobs (
            job_id TEXT PRIMARY KEY, company_name TEXT, job_title TEXT, location TEXT,
            category TEXT, salary TEXT, contact_email TEXT, description TEXT,
            apply_url TEXT, logo_url TEXT, tier TEXT, price REAL, status TEXT DEFAULT 'pending',
            views INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP DEFAULT (datetime('now', '+30 days')))""")
        rows = conn.execute(
            "SELECT * FROM posted_jobs WHERE status = 'pending' AND expires_at > datetime('now') ORDER BY CASE tier WHEN 'enterprise' THEN 1 WHEN 'featured' THEN 2 ELSE 3 END, created_at DESC LIMIT 50"
        ).fetchall()
        conn.close()
        return {
            "status": "ok",
            "jobs": [dict(r) for r in rows] if rows else [],
            "count": len(rows) if rows else 0
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/employer/track", response_class=HTMLResponse)
def employer_track_page(request: Request):
    """Employer tracking page — enter email to see all posted jobs."""
    get_db_fn, get_verified_user_id_fn, _, _, _, render_template_fn, _public_shell_fn, _build_dashboard_shell_fn, _ = _deps()
    user_id = get_verified_user_id_fn(request)
    if user_id:
        conn = get_db_fn()
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        user = dict(user_row) if user_row else {}
        content = render_template_fn("employer_track.html", user=user, active_page="employer-track")
        return HTMLResponse(_build_dashboard_shell_fn(user, user_id, content, "Track Jobs", "employer-track", request=request))

    content = render_template_fn("employer_track.html", request=request, active_page="employer-track", user=None)
    return HTMLResponse(_public_shell_fn(content, "Track Jobs &mdash; JobHunt Pro"))

@router.get("/api/employer/dashboard")
def api_employer_dashboard(email: str = "", job_id: str = ""):
    """Get all jobs for an employer email, or a specific job."""
    get_db_fn, _, _, _, _, _, _, _, _ = _deps()
    if not email:
        return {"status": "error", "message": "Email is required."}
    try:
        conn = get_db_fn()
        if job_id:
            rows = conn.execute(
                "SELECT * FROM posted_jobs WHERE job_id = ? AND contact_email = ?",
                (job_id, email)
            ).fetchall()
            if rows:
                conn.execute("UPDATE posted_jobs SET views = views + 1 WHERE job_id = ?", (job_id,))
                conn.commit()
        else:
            rows = conn.execute(
                "SELECT * FROM posted_jobs WHERE contact_email = ? ORDER BY created_at DESC LIMIT 50",
                (email,)
            ).fetchall()
        conn.close()

        jobs = []
        for r in (rows or []):
            j = dict(r)
            for k in ['created_at', 'expires_at']:
                if j.get(k):
                    j[k] = str(j[k])
            jobs.append(j)

        return {
            "status": "ok",
            "jobs": jobs
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/api/employer/preferences")
def api_employer_get_prefs(email: str = ""):
    """Get notification preferences for employer."""
    get_db_fn, _, _, _, _, _, _, _, _ = _deps()
    if not email:
        return {"status": "error", "message": "Email required."}
    try:
        conn = get_db_fn()
        conn.execute("""CREATE TABLE IF NOT EXISTS employer_preferences (
            contact_email TEXT PRIMARY KEY, notify_email INTEGER DEFAULT 0,
            notify_interval_min INTEGER DEFAULT 0, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        row = conn.execute("SELECT * FROM employer_preferences WHERE contact_email = ?", (email,)).fetchone()
        conn.close()
        prefs = dict(row) if row else {"contact_email": email, "notify_email": 0}
        return {"status": "ok", "preferences": prefs}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/api/employer/preferences")
def api_employer_save_prefs(
    email: str = Form(...),
    notify_email: int = Form(0),
):
    """Save notification preferences."""
    get_db_fn, _, _, _, _, _, _, _, _ = _deps()
    try:
        conn = get_db_fn()
        conn.execute("""CREATE TABLE IF NOT EXISTS employer_preferences (
            contact_email TEXT PRIMARY KEY, notify_email INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.execute("""
            INSERT INTO employer_preferences (contact_email, notify_email, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(contact_email) DO UPDATE SET notify_email = ?, updated_at = datetime('now')
        """, (email, notify_email, notify_email))
        conn.commit()
        conn.close()
        state = "ON ✅" if notify_email else "OFF ❌"
        return {"status": "ok", "message": f"Notifications {state}", "notify_email": notify_email}
    except Exception as e:
        return {"status": "error", "message": str(e)}