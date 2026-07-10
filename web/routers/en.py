"""
routers/en.py - English Language Public Routes (/en/*)
These routes mirror the Arabic public routes but serve English templates
from web/templates/en/ directory.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/en", tags=["en"])


def _deps():
    from web.shared import get_db, get_verified_user_id, templates, config
    return get_db, get_verified_user_id, templates, config


# ── Home (English landing page) ──────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
def en_home(request: Request):
    _, get_verified_user_id, templates, config = _deps()
    user_id = get_verified_user_id(request)
    return templates.TemplateResponse(request, "en/index_v4.html", {
        "VERSION": config.VERSION,
        "is_logged_in": bool(user_id),
    })


# ── Pricing ───────────────────────────────────────────────────────────────────
@router.get("/pricing", response_class=HTMLResponse)
def en_pricing(request: Request):
    get_db, get_verified_user_id, templates, config = _deps()
    try:
        from web.app_v2 import get_all_pricing
        pricing_data = get_all_pricing()
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
        return templates.TemplateResponse(request, "en/pricing_v3.html", {
            "pricing": pricing_dict,
            "flash_discount": 0,
            "flash_sale": None,
            "is_logged_in": bool(user_id),
            "VERSION": config.VERSION,
        })
    except Exception as e:
        logger.error(f"EN Pricing page error: {e}", exc_info=True)
        return HTMLResponse("<h2>Error loading pricing</h2><p>Please try again later.</p>", status_code=500)


# ── Login ─────────────────────────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
def en_login(request: Request, plan: str = ""):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/login_v2.html", {
        "plan": plan,
        "VERSION": config.VERSION,
    })


@router.post("/login")
async def en_login_post(request: Request, email: str = Form(...), password: str = Form(...)):
    from web.shared import get_db, templates, config
    from web.app_v2 import session_serializer
    import bcrypt
    email = email.strip().lower()
    with get_db() as conn:
        user = conn.execute(
            "SELECT user_id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        pass  # conn.close()
        if not user:
            return templates.TemplateResponse(request, "en/login_v2.html", {
                "error": "Invalid credentials",
                "VERSION": config.VERSION,
            })
        pw_hash = user["password_hash"] if hasattr(user, "__getitem__") else user[1]
        if not bcrypt.checkpw(password.encode(), pw_hash.encode() if isinstance(pw_hash, str) else pw_hash):
            return templates.TemplateResponse(request, "en/login_v2.html", {
                "error": "Invalid credentials",
                "VERSION": config.VERSION,
            })
        u_id = user["user_id"] if hasattr(user, "__getitem__") else user[0]
        signed_uid = session_serializer.dumps(u_id)
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie("user_id", signed_uid, max_age=86400 * 30, httponly=True, samesite="lax", secure=True)
        return response


# ── Register ──────────────────────────────────────────────────────────────────
@router.get("/register", response_class=HTMLResponse)
def en_register(request: Request, plan: str = "", ref: str = ""):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/register_v2.html", {
        "plan": plan,
        "ref_code": ref,
        "VERSION": config.VERSION,
    })


# ── FAQ ───────────────────────────────────────────────────────────────────────
@router.get("/faq", response_class=HTMLResponse)
def en_faq(request: Request):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/faq.html", {"VERSION": config.VERSION})


# ── Blog ──────────────────────────────────────────────────────────────────────
@router.get("/blog", response_class=HTMLResponse)
def en_blog(request: Request):
    _, _, templates, config = _deps()
    try:
        from core.seo_blog_farm import get_posts, get_stats
        posts = get_posts(published_only=True, limit=20)
        stats = get_stats()
    except Exception:
        posts, stats = [], {}
    return templates.TemplateResponse(request, "en/blog.html", {
        "posts": posts,
        "stats": stats,
        "VERSION": config.VERSION,
    })


@router.get("/blog/{slug}", response_class=HTMLResponse)
def en_blog_post(request: Request, slug: str):
    _, _, templates, config = _deps()
    try:
        from core.seo_blog_farm import get_post, get_posts
        post = get_post(slug)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        related = get_posts(published_only=True, limit=3)
        return templates.TemplateResponse(request, "en/blog_post.html", {
            "post": post,
            "related": related,
            "VERSION": config.VERSION,
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"EN blog post error: {e}", exc_info=True)
        raise HTTPException(status_code=404, detail="Post not found")


# ── Compare ───────────────────────────────────────────────────────────────────
@router.get("/compare", response_class=HTMLResponse)
def en_compare(request: Request):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/compare.html", {"VERSION": config.VERSION})


# ── Trust / Social Proof ──────────────────────────────────────────────────────
@router.get("/trust", response_class=HTMLResponse)
def en_trust(request: Request):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/trust.html", {"VERSION": config.VERSION})


# ── Chrome Extension ──────────────────────────────────────────────────────────
@router.get("/chrome-extension", response_class=HTMLResponse)
def en_chrome_ext(request: Request):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/chromeext.html", {"VERSION": config.VERSION})


# ── Contact ───────────────────────────────────────────────────────────────────
@router.get("/contact", response_class=HTMLResponse)
def en_contact(request: Request):
    _, get_verified_user_id, templates, config = _deps()
    user_id = get_verified_user_id(request)
    return templates.TemplateResponse(request, "en/contact.html", {
        "VERSION": config.VERSION,
        "is_admin": False,
    })


# ── Privacy & Terms ───────────────────────────────────────────────────────────
@router.get("/privacy", response_class=HTMLResponse)
def en_privacy(request: Request):
    _, _, templates, _ = _deps()
    return templates.TemplateResponse(request, "en/privacy.html", {})


@router.get("/terms", response_class=HTMLResponse)
def en_terms(request: Request):
    _, _, templates, _ = _deps()
    return templates.TemplateResponse(request, "en/terms.html", {})


# ── Services ──────────────────────────────────────────────────────────────────
@router.get("/services", response_class=HTMLResponse)
def en_services(request: Request):
    _, get_verified_user_id, templates, config = _deps()
    try:
        from services.catalog import SERVICE_CATALOG, BOUQUET_CATALOG
        user_id = get_verified_user_id(request)
        return templates.TemplateResponse(request, "en/services_v2.html", {
            "services": SERVICE_CATALOG,
            "bouquets": BOUQUET_CATALOG,
            "is_logged_in": bool(user_id),
            "VERSION": config.VERSION,
        })
    except Exception as e:
        logger.error(f"EN services error: {e}", exc_info=True)
        return templates.TemplateResponse(request, "en/services_v2.html", {
            "services": [],
            "bouquets": [],
            "is_logged_in": False,
            "VERSION": config.VERSION,
        })


# ── Referral ──────────────────────────────────────────────────────────────────
@router.get("/referral", response_class=HTMLResponse)
def en_referral(request: Request, ref: str = ""):
    _, get_verified_user_id, templates, config = _deps()
    user_id = get_verified_user_id(request)
    if user_id:
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse(request, "en/referral.html", {
        "ref_code": ref,
        "VERSION": config.VERSION,
    })


# ── Track Application ─────────────────────────────────────────────────────────
@router.get("/track", response_class=HTMLResponse)
def en_track(request: Request):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/track_application.html", {"VERSION": config.VERSION})


# ── Forgot / Reset Password ───────────────────────────────────────────────────
@router.get("/forgot-password", response_class=HTMLResponse)
def en_forgot_password(request: Request):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/forgot_password.html", {"VERSION": config.VERSION})


@router.get("/reset-password", response_class=HTMLResponse)
def en_reset_password(request: Request, token: str = ""):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/reset_password.html", {
        "token": token,
        "VERSION": config.VERSION,
    })


# ── Roast My CV ───────────────────────────────────────────────────────────────
@router.get("/roast", response_class=HTMLResponse)
def en_roast(request: Request):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/roast.html", {"VERSION": config.VERSION})


# ── For Employers ─────────────────────────────────────────────────────────────
@router.get("/for-employers", response_class=HTMLResponse)
def en_for_employers(request: Request):
    _, _, templates, config = _deps()
    return templates.TemplateResponse(request, "en/for_employers.html", {"VERSION": config.VERSION})
