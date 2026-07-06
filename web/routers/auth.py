"""
routers/auth.py - Authentication Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
Routes: /register GET+POST, /api/v1/login POST, /logout GET,
        /auth/refresh-token POST, /auth/logout POST
"""
import os, uuid, logging, httpx
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from itsdangerous import BadSignature, SignatureExpired
import bcrypt, secrets

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

_login_attempts: dict = {}
_register_attempts: dict = {}

def _deps():
    from web.shared import get_db, session_serializer, templates, config, _check_rate_limit
    return get_db, session_serializer, templates, config, _check_rate_limit

def _hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def _verify_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False

def _gen_api_key() -> str:
    return secrets.token_urlsafe(32)


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, ref: str = ""):
    _, _, templates, config, _ = _deps()
    return templates.TemplateResponse(request, "register_v2.html", {
        "ref": ref,
        "VERSION": config.VERSION,
        "turnstile_site_key": getattr(config, "TURNSTILE_SITE_KEY", ""),
    })


@router.post("/register")
async def register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    phone: str = Form(""),
    company_name: str = Form(""),
    user_type: str = Form("jobseeker"),
    ref: str = Form(""),
    selected_plan: str = Form("starter"),
    cf_turnstile_response: str = Form(None, alias="cf-turnstile-response"),
    aegis_honeypot: str = Form(""),
):
    get_db, _, templates, config, _check_rate_limit = _deps()

    if aegis_honeypot:
        logger.warning(f"[AEGIS] Honeypot triggered from {request.client.host}")
        return HTMLResponse("403 Forbidden", status_code=403)

    turnstile_secret = getattr(config, "TURNSTILE_SECRET", "") or os.getenv("TURNSTILE_SECRET", "")
    if turnstile_secret:
        if not cf_turnstile_response:
            return templates.TemplateResponse(request, "register_v2.html",
                {"error": "Please complete the Anti-Bot CAPTCHA.", "ref": ref})
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post("https://challenges.cloudflare.com/turnstile/v0/siteverify",
                    data={"secret": turnstile_secret, "response": cf_turnstile_response}, timeout=5.0)
                if not r.json().get("success"):
                    return templates.TemplateResponse(request, "register_v2.html",
                        {"error": "Anti-Bot Verification Failed.", "ref": ref})
        except Exception as e:
            logger.error(f"Turnstile error: {e}")

    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(_register_attempts, client_ip, max_count=5):
        return templates.TemplateResponse(request, "register_v2.html",
            {"error": "Too many attempts. Try again in 1 hour.", "ref": ref})

    if len(password) < 8:
        return templates.TemplateResponse(request, "register_v2.html",
            {"error": "Password must be at least 8 characters.", "ref": ref})
    if not any(c.isupper() for c in password):
        return templates.TemplateResponse(request, "register_v2.html",
            {"error": "Password must contain at least one uppercase letter.", "ref": ref})
    if not any(c.isdigit() for c in password):
        return templates.TemplateResponse(request, "register_v2.html",
            {"error": "Password must contain at least one digit.", "ref": ref})

    conn = get_db()
    existing = conn.execute("SELECT user_id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return templates.TemplateResponse(request, "register_v2.html", {"error": "Email already registered"})

    user_id = f"user_{uuid.uuid4().hex[:16]}"
    api_key = _gen_api_key()
    conn.execute(
        "INSERT INTO users (user_id, email, password_hash, name, phone, company_name, user_type, api_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, email, _hash_pw(password), name, phone, company_name, user_type, api_key)
    )
    conn.commit()

    if ref:
        try:
            referrer = conn.execute("SELECT user_id, wallet_balance FROM users WHERE user_id = ?", (ref,)).fetchone()
            if referrer:
                conn.execute("UPDATE users SET wallet_balance = wallet_balance + 5.0 WHERE user_id = ?", (ref,))
                conn.execute("UPDATE users SET wallet_balance = wallet_balance + 2.0 WHERE user_id = ?", (user_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Referral credit failed: {e}")

    conn.close()

    try:
        import asyncio
        from core.email_marketing import send_welcome_email
        asyncio.create_task(send_welcome_email(user_id, email, name))
    except Exception as e:
        logger.error(f"Welcome email failed: {e}")

    resp = RedirectResponse(f"/login?plan={selected_plan}", status_code=303)
    resp.set_cookie("last_selected_plan", selected_plan, max_age=86400)
    return resp


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, plan: str = ""):
    _, _, templates, config, _ = _deps()
    return templates.TemplateResponse(request, "login_v2.html", {
        "plan": plan,
        "VERSION": config.VERSION
    })


@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    get_db, session_serializer, templates, config, _ = _deps()
    email = email.strip().lower()
    
    conn = get_db()
    user = conn.execute(
        "SELECT user_id, password_hash FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    conn.close()
    
    if not user or not _verify_pw(password, user["password_hash"] if hasattr(user, "__getitem__") else user[1]):
        return templates.TemplateResponse(request, "login_v2.html", {
            "error": "Invalid credentials",
            "VERSION": config.VERSION
        })
        
    u_id = user["user_id"] if hasattr(user, "__getitem__") else user[0]
    signed_uid = session_serializer.dumps(u_id)
    
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie("user_id", signed_uid, max_age=86400 * 30, httponly=True, samesite="lax", secure=True)
    return response


@router.post("/api/v1/login")
async def api_login(request: Request):
    """JSON API login - used by Chrome Extension and Telegram MiniApp."""
    get_db, session_serializer, _, _, _ = _deps()
    try:
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password required")

    conn = get_db()
    user = conn.execute(
        "SELECT user_id, password_hash, name, email, tokens, subscription_status, api_key FROM users WHERE email = ?",
        (email,)
    ).fetchone()
    conn.close()

    if not user or not _verify_pw(password, user["password_hash"] if hasattr(user, "__getitem__") else user[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    u = dict(user) if hasattr(user, "keys") else {
        "user_id": user[0], "password_hash": user[1], "name": user[2],
        "email": user[3], "tokens": user[4], "subscription_status": user[5], "api_key": user[6]
    }
    signed_uid = session_serializer.dumps(u["user_id"])
    resp = JSONResponse({
        "status": "ok",
        "user_id": u["user_id"],
        "name": u["name"],
        "email": u["email"],
        "api_key": u["api_key"],
        "tokens": u["tokens"],
        "subscription_status": u["subscription_status"],
    })
    resp.set_cookie("user_id", signed_uid, max_age=86400 * 30, httponly=True, samesite="lax", secure=True)
    return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("user_id")
    resp.delete_cookie("session")
    return resp


@router.post("/auth/refresh-token")
async def refresh_token(request: Request):
    get_db, session_serializer, _, _, _ = _deps()
    cookie = request.cookies.get("user_id", "")
    if not cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user_id = session_serializer.loads(cookie, max_age=86400 * 30)
    except (BadSignature, SignatureExpired):
        raise HTTPException(status_code=401, detail="Session expired")
    resp = JSONResponse({"status": "refreshed", "user_id": user_id})
    resp.set_cookie("user_id", session_serializer.dumps(user_id), max_age=86400 * 30, httponly=True, samesite="lax", secure=True)
    return resp


@router.post("/auth/logout")
def api_logout():
    resp = JSONResponse({"status": "logged_out"})
    resp.delete_cookie("user_id")
    return resp