"""
routers/public.py - Public Routes Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import os, logging
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, Response

logger = logging.getLogger(__name__)
router = APIRouter(tags=["public"])

_contact_attempts: dict = {}

def _deps():
    from web.shared import get_db, get_verified_user_id, templates, config, _check_rate_limit
    from web.app_v2 import get_all_pricing, _public_shell, render_template
    return get_db, get_verified_user_id, templates, config, _check_rate_limit, get_all_pricing, _public_shell, render_template

@router.get("/", response_class=HTMLResponse)
def index_page(request: Request):
    from web.app_v2 import home
    return home(request)

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
            conn = get_db()
            now_iso = datetime.now().isoformat()
            fs = conn.execute(
                "SELECT discount_percent, title, end_time FROM flash_sales WHERE active = 1 AND start_time <= ? AND end_time > ? ORDER BY end_time ASC LIMIT 1",
                (now_iso, now_iso)
            ).fetchone()
            if fs:
                flash_discount = float(fs["discount_percent"])
                flash_sale_info = {"title": fs["title"], "discount": flash_discount, "end_time": fs["end_time"]}
            conn.close()
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
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
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