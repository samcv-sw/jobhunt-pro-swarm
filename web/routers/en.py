"""
routers/en.py - English Language Public Routes (/en/*)
These routes mirror the Arabic public routes but serve English templates
from web/templates/en/ directory.
"""
import logging

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/en", tags=["en"])


def _deps():
    from web.shared import config, get_db, get_verified_user_id, templates, _public_shell, render_template
    return get_db, get_verified_user_id, templates, config, _public_shell, render_template


# ── Home (English landing page) ──────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
def en_home(request: Request):
    _, get_verified_user_id, templates, config, _, _ = _deps()
    user_id = get_verified_user_id(request)
    return templates.TemplateResponse(request, "en/index_v4.html", {
        "VERSION": config.VERSION,
        "is_logged_in": bool(user_id),
    })


# ── Pricing ───────────────────────────────────────────────────────────────────
@router.get("/pricing", response_class=HTMLResponse)
def en_pricing(request: Request):
    get_db, get_verified_user_id, templates, config, _public_shell, render_template = _deps()
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
        pricing_content = render_template("en/pricing_v3.html", request=request,
                                          pricing=pricing_dict,
                                          flash_discount=0,
                                          flash_sale=None,
                                          is_logged_in=bool(user_id),
                                          lang="en",
                                          VERSION=config.VERSION)
        html = _public_shell(pricing_content, "Pricing - JobHunt Pro", "JobHunt Pro pricing plans.", request=request, lang="en")
        response = HTMLResponse(content=html)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response
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
    from web.app_v2 import session_serializer
    from web.routers.auth import _fetch_user_by_email, _verify_pw_async
    from web.shared import config, get_db, templates

    email = email.strip().lower()
    with get_db() as conn:
        user = _fetch_user_by_email(conn, email)
        if not user:
            return templates.TemplateResponse(request, "en/login_v2.html", {
                "error": "Invalid email or password.",
                "VERSION": config.VERSION,
            })

        pw_hash = user["password_hash"]
        if pw_hash == "oauth_authenticated_user":
            return templates.TemplateResponse(request, "en/login_v2.html", {
                "error": "This account was created via Google/Microsoft. Please sign in with Google or Microsoft.",
                "VERSION": config.VERSION,
            })

        verified = False
        try:
            verified = await _verify_pw_async(password, pw_hash)
        except Exception:
            pass

        if not verified:
            return templates.TemplateResponse(request, "en/login_v2.html", {
                "error": "Invalid email or password.",
                "VERSION": config.VERSION,
            })

        u_id = user["user_id"]
        signed_uid = session_serializer.dumps(u_id)
        response = RedirectResponse("/user-dashboard", status_code=303)
        response.set_cookie("user_id", signed_uid, max_age=86400 * 30, httponly=True, samesite="lax", secure=False, path="/")
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
    get_db, get_verified_user_id, templates, config, _public_shell, render_template = _deps()
    msg = request.query_params.get("msg", "")
    error = request.query_params.get("error", "")
    user_name = ""
    user_email = ""
    user_id = get_verified_user_id(request)
    if user_id:
        try:
            with get_db() as conn:
                u = conn.execute(
                    "SELECT name, email FROM users WHERE user_id = ? OR id = ?", (user_id, user_id)
                ).fetchone()
                if u:
                    user_name = u["name"] or ""
                    user_email = u["email"] or ""
        except Exception as exc:
            logger.error(f"en_contact user fetch error: {exc}")
    content = render_template(
        "en/contact.html",
        request=request,
        msg=msg,
        error=error,
        user_name=user_name,
        user_email=user_email,
        is_logged_in=bool(user_id),
        VERSION=config.VERSION,
        lang="en"
    )
    return HTMLResponse(
        _public_shell(
            content,
            "Contact Us | JobHunt Pro",
            "Get in touch with the JobHunt Pro team — we're here to help.",
            request=request,
            lang="en"
        )
    )


@router.post("/contact")
def en_contact_submit(request: Request, name: str = Form(""), email: str = Form(""), message: str = Form(""), subject: str = Form("")):
    """Handle English contact form submission and deliver notification to jobhuntpro.app@zohomail.com."""
    try:
        from fastapi.responses import RedirectResponse
        from core.email_engine import send_email_notification
        target_email = getattr(config, "SUPPORT_EMAIL", "jobhuntpro.app@zohomail.com")
        body = f"New Contact Form Submission (EN):\n\nName: {name}\nSender Email: {email}\nSubject: {subject}\n\nMessage:\n{message}"
        send_email_notification(to_email=target_email, subject=f"📩 Contact Form: {subject or 'New Inquiry'}", body=body)
    except Exception as exc:
        logger.error(f"EN Contact submit error: {exc}")
    return RedirectResponse("/contact?msg=Thank+you!+Your+message+has+been+sent.", status_code=303)


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
@router.get("/en/services", response_class=HTMLResponse)
def en_services(request: Request):
    _, get_verified_user_id, templates, config = _deps()
    try:
        from services.catalog import BOUQUET_CATALOG, SERVICE_CATALOG
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
    user_stats = {}
    referral_link = ""
    referral_code = ref or ""
    
    if user_id:
        try:
            from core.referral_engine import get_user_referral_stats
            user_stats = get_user_referral_stats(user_id)
            referral_code = user_stats.get("referral_code", user_id[:8])
            base_url = str(request.base_url).rstrip("/")
            referral_link = f"{base_url}/en/register?ref={referral_code}"
            user_stats["referral_link"] = referral_link
        except Exception:
            base_url = str(request.base_url).rstrip("/")
            referral_link = f"{base_url}/en/register?ref={user_id[:8]}"
            user_stats = {"referral_code": user_id[:8], "referral_link": referral_link, "total_referred": 0, "total_earned": 0}

    return templates.TemplateResponse(request, "en/referral.html", {
        "ref_code": referral_code,
        "user_id": user_id,
        "user_stats": user_stats,
        "referral_link": referral_link,
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
    _, _, templates, config, _, _ = _deps()
    return templates.TemplateResponse(request, "en/for_employers.html", {"VERSION": config.VERSION})


# ── Wallet ───────────────────────────────────────────────────────────────────
@router.get("/wallet", response_class=HTMLResponse)
def en_wallet(request: Request):
    from web.routers.payments import get_wallet_page
    return get_wallet_page(request)


# ── My Purchases & Subscriptions ─────────────────────────────────────────────
@router.get("/my-purchases", response_class=HTMLResponse)
def en_my_purchases(request: Request):
    from web.routers.payments import my_purchases_page
    return my_purchases_page(request)


# ── Statistics & Analytics ───────────────────────────────────────────────────
@router.get("/stats", response_class=HTMLResponse)
def en_stats(request: Request):
    from web.routers.dashboard import stats_page
    return stats_page(request)
