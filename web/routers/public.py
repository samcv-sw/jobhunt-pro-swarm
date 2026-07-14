"""
routers/public.py - Public Routes Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import logging
import os
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["public"])

_contact_attempts: dict = {}

def _deps():
    from web.app_v2 import _public_shell, get_all_pricing, render_template
    from web.shared import (
        _check_rate_limit,
        config,
        get_db,
        get_verified_user_id,
        templates,
    )
    return get_db, get_verified_user_id, templates, config, _check_rate_limit, get_all_pricing, _public_shell, render_template

@router.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    from datetime import timedelta
    get_db, _, templates, config, _, get_all_pricing, _, _ = _deps()
    try:
        conn = get_db()
        now = datetime.now()

        def _earnings_for_period(since=None):
            if since:
                since_str = since.isoformat()
                orders = conn.execute(
                    "SELECT COALESCE(SUM(amount_usd),0) as total, COUNT(*) as cnt FROM orders WHERE payment_status='completed' AND created_at >= ?",
                    (since_str,)
                ).fetchone()
                codes = conn.execute(
                    "SELECT COALESCE(SUM(value_usd),0) as total, COUNT(*) as cnt FROM redeem_codes WHERE is_used=1 AND (code_type IS NULL OR code_type != 'admin_free') AND used_at >= ?",
                    (since_str,)
                ).fetchone()
                emails = conn.execute(
                    "SELECT COALESCE(SUM(price_usd),0) as total, COUNT(*) as cnt FROM manual_emails WHERE status='sent' AND created_at >= ?",
                    (since_str,)
                ).fetchone()
            else:
                orders = conn.execute("SELECT COALESCE(SUM(amount_usd),0) as total, COUNT(*) as cnt FROM orders WHERE payment_status='completed'").fetchone()
                codes = conn.execute("SELECT COALESCE(SUM(value_usd),0) as total, COUNT(*) as cnt FROM redeem_codes WHERE is_used=1 AND (code_type IS NULL OR code_type != 'admin_free')").fetchone()
                emails = conn.execute("SELECT COALESCE(SUM(price_usd),0) as total, COUNT(*) as cnt FROM manual_emails WHERE status='sent'").fetchone()
            return {
                "orders": {"amount": round(float(orders["total"]), 2), "count": orders["cnt"]},
                "codes": {"amount": round(float(codes["total"]), 2), "count": codes["cnt"]},
                "emails": {"amount": round(float(emails["total"]), 2), "count": emails["cnt"]},
            }

        earnings_all = _earnings_for_period()
        earnings_24h = _earnings_for_period(now - timedelta(hours=24))
        earnings_month = _earnings_for_period(now - timedelta(days=30))
        earnings_year = _earnings_for_period(now - timedelta(days=365))

        total_all = round(earnings_all["orders"]["amount"] + earnings_all["codes"]["amount"] + earnings_all["emails"]["amount"], 2)
        total_24h = round(earnings_24h["orders"]["amount"] + earnings_24h["codes"]["amount"] + earnings_24h["emails"]["amount"], 2)
        total_month = round(earnings_month["orders"]["amount"] + earnings_month["codes"]["amount"] + earnings_month["emails"]["amount"], 2)
        total_year = round(earnings_year["orders"]["amount"] + earnings_year["codes"]["amount"] + earnings_year["emails"]["amount"], 2)

        conn.close()

        earnings = {
            "total_all": total_all,
            "total_24h": total_24h,
            "total_month": total_month,
            "total_year": total_year,
            "breakdown_all": earnings_all,
        }
    except Exception as e:
        import traceback
        logger.error(f"ERROR IN HOME ROUTE: {e}")
        traceback.print_exc()
        total_24h = 0
        earnings = {
            "total_all": 0, "total_24h": 0, "total_month": 0, "total_year": 0,
            "breakdown_all": {"orders": {"amount": 0, "count": 0}, "codes": {"amount": 0, "count": 0}, "emails": {"amount": 0, "count": 0}},
        }

    # Fetch featured jobs to show in index_v4.html
    featured_jobs = []
    try:
        conn = get_db()
        rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC LIMIT 6").fetchall()
        for r in rows:
            date_str = "Just now"
            if r["created_at"]:
                try:
                    dt = datetime.strptime(r["created_at"].split(".")[0], "%Y-%m-%d %H:%M:%S")
                    diff = datetime.now() - dt
                    if diff.days == 0:
                        date_str = "Today"
                    elif diff.days == 1:
                        date_str = "1 day ago"
                    else:
                        date_str = f"{diff.days} days ago"
                except Exception:
                    pass
            featured_jobs.append({
                "id": r["id"],
                "title": r["title"],
                "company": r["company"],
                "location": r["location"] or "Remote",
                "salary": r["salary"] if r["salary"] else "$80k - $120k",
                "board": r["source"].upper() if r["source"] else "LINKEDIN",
                "type": "Full-time",
                "date_posted": date_str
            })
        conn.close()
    except Exception as e:
        logger.error(f"Error fetching featured jobs: {e}")

    tiers = get_all_pricing()
    return templates.TemplateResponse(request, "index_v4.html", {
        "earnings": earnings,
        "tiers": tiers,
        "VERSION": config.VERSION,
        "APP_NAME": config.APP_NAME,
        "fomo_apps_today": total_24h if total_24h > 0 else "47",
        "featured_jobs": featured_jobs
    })

@router.get("/api/docs", response_class=HTMLResponse)
def api_docs(request: Request):
    return HTMLResponse("<h1>API Documentation</h1><p>Premium access required.</p>")

@router.get("/pricing", response_class=HTMLResponse)
def pricing(request: Request):
    get_db, get_verified_user_id, templates, config, _, get_all_pricing, _public_shell, render_template = _deps()
    try:
        pricing_data = get_all_pricing()
        flash_discount = 0
        flash_sale_info = None
        try:
            with get_db() as conn:
                now_iso = datetime.now().isoformat()
                fs = conn.execute(
                    "SELECT discount_percent, title, end_time FROM flash_sales WHERE active = 1 AND start_time <= ? AND end_time > ? ORDER BY end_time ASC LIMIT 1",
                    (now_iso, now_iso)
                ).fetchone()
                if fs:
                    flash_discount = float(fs["discount_percent"])
                    flash_sale_info = {"title": fs["title"], "discount": flash_discount, "end_time": fs["end_time"]}
                pass  # conn.close()
        except Exception as e:
            logger.error(e, exc_info=True)
        user_id = get_verified_user_id(request)

        services_list = [
            {"name": "AI Auto-Apply Engine", "desc": "Automated job applications 24/7", "price": 9.99},
            {"name": "Smart Resume Tailoring", "desc": "AI optimizes your CV per job", "price": 4.99},
            {"name": "Email Follow-up Automation", "desc": "Auto follow-ups with tracking", "price": 6.99},
            {"name": "Interview Scheduler", "desc": "AI schedules your interviews", "price": 14.99},
            {"name": "LinkedIn Profile Optimizer", "desc": "AI-enhanced LinkedIn presence", "price": 3.99},
            {"name": "Cover Letter Generator", "desc": "Custom cover letters per job", "price": 2.99},
        ]
        pricing_dict = {"tiers": pricing_data.get("tiers", pricing_data), "services": services_list}

        pricing_content = render_template("pricing_v3.html", request=request,
                                          pricing=pricing_dict,
                                          flash_discount=flash_discount,
                                          flash_sale=flash_sale_info,
                                          is_logged_in=bool(user_id),
                                          VERSION=config.VERSION)
        html = _public_shell(pricing_content, "Pricing - JobHunt Pro", "JobHunt Pro pricing plans.", request=request)
        response = HTMLResponse(content=html)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    except Exception as e:
        logger.error(f"Pricing page crashed: {e}", exc_info=True)
        return HTMLResponse("<h2>Error loading pricing</h2><p>Please try again later.</p>", status_code=500)

@router.get("/referral", response_class=HTMLResponse)
def referral_page(request: Request, ref: str = ""):
    get_db, get_verified_user_id, templates, config, _, _, _public_shell, render_template = _deps()
    try:
        user_id = get_verified_user_id(request)
        if user_id:
            return RedirectResponse("/dashboard", status_code=303)
        content = render_template("referral.html", request=request, ref_code=ref)
        html = _public_shell(content, "You are invited to JobHunt Pro!", request=request)
        response = HTMLResponse(content=html)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response
    except Exception as e:
        logger.error(f"Error rendering referral landing: {e}", exc_info=True)
        return RedirectResponse("/register", status_code=303)

@router.get("/faq", response_class=HTMLResponse)
def faq_page(request: Request):
    get_db, _, templates, config, _, _, _, _ = _deps()
    return templates.TemplateResponse(request, "faq.html", {})

@router.get("/blog", response_class=HTMLResponse)
def blog_page(request: Request):
    get_db, _, templates, config, _, _, _, _ = _deps()
    from core.seo_blog_farm import get_posts, get_stats
    posts = get_posts(published_only=True, limit=20)
    stats = get_stats()
    return templates.TemplateResponse(request, "blog.html", {
        "posts": posts,
        "stats": stats,
        "VERSION": config.VERSION,
    })

@router.get("/blog/{slug}", response_class=HTMLResponse)
def blog_post_page(request: Request, slug: str):
    get_db, _, templates, config, _, _, _, _ = _deps()
    from core.seo_blog_farm import get_post, get_posts
    post = get_post(slug)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    related = get_posts(published_only=True, limit=3)
    return templates.TemplateResponse(request, "blog_post.html", {
        "post": post,
        "related": related,
        "VERSION": config.VERSION,
    })

@router.get("/privacy", response_class=HTMLResponse)
def privacy_page(request: Request):
    _, _, templates, _, _, _, _, _ = _deps()
    return templates.TemplateResponse(request, "privacy.html", {})

@router.get("/trust", response_class=HTMLResponse)
def trust_page(request: Request):
    _, _, templates, config, _, _, _, _ = _deps()
    return templates.TemplateResponse(request, "trust.html", {"request": request, "VERSION": config.VERSION})

@router.get("/war-room", response_class=HTMLResponse)
def war_room_redirect(request: Request):
    _, get_verified_user_id, _, _, _, _, _, _ = _deps()
    if get_verified_user_id(request):
        return RedirectResponse("/user-dashboard", status_code=302)
    return RedirectResponse("/login", status_code=302)

@router.get("/compare", response_class=HTMLResponse)
def compare_page(request: Request):
    _, _, templates, config, _, _, _, _ = _deps()
    return templates.TemplateResponse(request, "compare.html", {"VERSION": config.VERSION})

@router.get("/chrome-extension", response_class=HTMLResponse)
def chrome_extension_page(request: Request):
    _, _, templates, config, _, _, _, _ = _deps()
    return templates.TemplateResponse(request, "chromeext.html", {"VERSION": config.VERSION})

@router.get("/terms", response_class=HTMLResponse)
def terms_page(request: Request):
    _, _, templates, _, _, _, _, _ = _deps()
    return templates.TemplateResponse(request, "terms.html", {})

@router.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    return RedirectResponse("/", status_code=301)

@router.get("/sitemap.xml")
def sitemap():
    site = os.getenv("SITE_URL", "https://jhfguf.pythonanywhere.com")
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{site}/</loc><lastmod>{today}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>
  <url><loc>{site}/pricing</loc><lastmod>{today}</lastmod><changefreq>monthly</changefreq><priority>0.9</priority></url>
</urlset>'''
    return Response(content=xml, media_type="application/xml")

@router.get("/robots.txt")
def robots():
    site = os.getenv("SITE_URL", "https://jhfguf.pythonanywhere.com")
    txt = f"User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: {site}/sitemap.xml"
    return PlainTextResponse(txt)
