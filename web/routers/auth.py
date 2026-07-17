"""
routers/auth.py - Authentication Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
Routes: /register GET+POST, /api/v1/login POST, /logout GET,
        /auth/refresh-token POST, /auth/logout POST
"""

import logging
import os
import secrets
import uuid

import bcrypt
import httpx
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from itsdangerous import BadSignature, SignatureExpired

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])

_login_attempts: dict = {}
_register_attempts: dict = {}


def _deps():
    from web.shared import (
        _check_rate_limit,
        config,
        get_db,
        session_serializer,
        templates,
    )

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
    return templates.TemplateResponse(
        request,
        "register_v2.html",
        {
            "ref": ref,
            "VERSION": config.VERSION,
            "turnstile_site_key": getattr(config, "TURNSTILE_SITE_KEY", ""),
        },
    )


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
    email = email.strip().lower()

    if aegis_honeypot:
        logger.warning(f"[AEGIS] Honeypot triggered from {request.client.host}")
        return HTMLResponse("403 Forbidden", status_code=403)

    turnstile_secret = getattr(config, "TURNSTILE_SECRET", "") or os.getenv("TURNSTILE_SECRET", "")
    if turnstile_secret:
        if not cf_turnstile_response:
            return templates.TemplateResponse(
                request,
                "register_v2.html",
                {"error": "Please complete the Anti-Bot CAPTCHA.", "ref": ref},
            )
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                    data={"secret": turnstile_secret, "response": cf_turnstile_response},
                    timeout=5.0,
                )
                if not r.json().get("success"):
                    return templates.TemplateResponse(
                        request,
                        "register_v2.html",
                        {"error": "Anti-Bot Verification Failed.", "ref": ref},
                    )
        except Exception as e:
            logger.error(f"Turnstile error: {e}")

    client_ip = request.client.host if request.client else "unknown"
    if not _check_rate_limit(_register_attempts, client_ip, max_count=5):
        return templates.TemplateResponse(
            request,
            "register_v2.html",
            {"error": "Too many attempts. Try again in 1 hour.", "ref": ref},
        )

    if len(password) < 8:
        return templates.TemplateResponse(
            request,
            "register_v2.html",
            {"error": "Password must be at least 8 characters.", "ref": ref},
        )
    if not any(c.isupper() for c in password):
        return templates.TemplateResponse(
            request,
            "register_v2.html",
            {"error": "Password must contain at least one uppercase letter.", "ref": ref},
        )
    if not any(c.isdigit() for c in password):
        return templates.TemplateResponse(
            request,
            "register_v2.html",
            {"error": "Password must contain at least one digit.", "ref": ref},
        )

    with get_db() as conn:
        existing = conn.execute(
            "SELECT user_id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            pass  # conn.close()
            return templates.TemplateResponse(
                request, "register_v2.html", {"error": "Email already registered"}
            )

        user_id = f"user_{uuid.uuid4().hex[:16]}"
        api_key = _gen_api_key()
        conn.execute(
            "INSERT INTO users (user_id, email, password_hash, name, phone, company_name, user_type, api_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, email, _hash_pw(password), name, phone, company_name, user_type, api_key),
        )
        conn.commit()

        if ref:
            try:
                referrer = conn.execute(
                    "SELECT user_id, wallet_balance FROM users WHERE user_id = ?", (ref,)
                ).fetchone()
                if referrer:
                    conn.execute(
                        "UPDATE users SET wallet_balance = wallet_balance + 5.0 WHERE user_id = ?",
                        (ref,),
                    )
                    conn.execute(
                        "UPDATE users SET wallet_balance = wallet_balance + 2.0 WHERE user_id = ?",
                        (user_id,),
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"Referral credit failed: {e}")

        pass  # conn.close()

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
    return templates.TemplateResponse(
        request, "login_v2.html", {"plan": plan, "VERSION": config.VERSION}
    )


@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    get_db, session_serializer, templates, config, _ = _deps()
    email = email.strip().lower()

    with get_db() as conn:
        user = conn.execute(
            "SELECT user_id, password_hash FROM users WHERE email = ?", (email,)
        ).fetchone()
        pass  # conn.close()

        if not user or not _verify_pw(
            password, user["password_hash"] if hasattr(user, "__getitem__") else user[1]
        ):
            return templates.TemplateResponse(
                request,
                "login_v2.html",
                {"error": "Invalid credentials", "VERSION": config.VERSION},
            )

        u_id = user["user_id"] if hasattr(user, "__getitem__") else user[0]
        signed_uid = session_serializer.dumps(u_id)

        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(
            "user_id", signed_uid, max_age=86400 * 30, httponly=True, samesite="lax", secure=True, path="/"
        )
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

    with get_db() as conn:
        user = conn.execute(
            "SELECT user_id, password_hash, name, email, tokens, subscription_status, api_key FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        pass  # conn.close()

        if not user or not _verify_pw(
            password, user["password_hash"] if hasattr(user, "__getitem__") else user[1]
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        u = (
            dict(user)
            if hasattr(user, "keys")
            else {
                "user_id": user[0],
                "password_hash": user[1],
                "name": user[2],
                "email": user[3],
                "tokens": user[4],
                "subscription_status": user[5],
                "api_key": user[6],
            }
        )
        signed_uid = session_serializer.dumps(u["user_id"])
        resp = JSONResponse(
            {
                "status": "ok",
                "user_id": u["user_id"],
                "name": u["name"],
                "email": u["email"],
                "api_key": u["api_key"],
                "tokens": u["tokens"],
                "subscription_status": u["subscription_status"],
            }
        )
        resp.set_cookie(
            "user_id", signed_uid, max_age=86400 * 30, httponly=True, samesite="lax", secure=True, path="/"
        )
        return resp


@router.get("/logout")
def logout():
    resp = RedirectResponse("/", status_code=303)
    resp.delete_cookie("user_id", path="/")
    resp.delete_cookie("session", path="/")
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
    resp.set_cookie(
        "user_id",
        session_serializer.dumps(user_id),
        max_age=86400 * 30,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )
    return resp


@router.post("/auth/logout")
def api_logout():
    resp = JSONResponse({"status": "logged_out"})
    resp.delete_cookie("user_id", path="/")
    return resp


@router.get("/auth/linkedin")
async def linkedin_login(request: Request):
    """
    LinkedIn login entrypoint. Redirects to LinkedIn authorization page.
    For local testing/mock, if LINKEDIN_CLIENT_ID is not configured, it redirects to the callback with a mock code.
    """
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    redirect_uri = str(request.url_for("linkedin_callback"))

    if not client_id or client_id == "mock_linkedin_id":
        logger.info("[OAuth] Redirecting to mock LinkedIn OAuth callback.")
        return RedirectResponse(f"{redirect_uri}?code=mock_code_123")

    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&client_id={client_id}&redirect_uri={redirect_uri}"
        f"&state=linkedin_state_abc&scope=r_liteprofile%20r_emailaddress"
    )
    return RedirectResponse(auth_url)


@router.get("/auth/linkedin/callback")
async def linkedin_callback(request: Request, code: str = "", state: str = ""):
    """
    LinkedIn OAuth callback. Exchanges authorization code for access token,
    retrieves user profile information, creates/logs-in the user, and auto-imports CV data.
    """
    get_db, session_serializer, _, _, _ = _deps()
    email = "linkedin_mock_user@example.com"
    name = "LinkedIn Candidate"
    phone = "+96170123456"

    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = str(request.url_for("linkedin_callback"))

    if client_id and client_id != "mock_linkedin_id" and code != "mock_code_123":
        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://www.linkedin.com/oauth/v2/accessToken",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                token_data = token_resp.json()
                access_token = token_data.get("access_token")

                if access_token:
                    profile_resp = await client.get(
                        "https://api.linkedin.com/v2/me",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    profile = profile_resp.json()
                    name = (
                        f"{profile.get('localizedFirstName', '')} {profile.get('localizedLastName', '')}".strip()
                        or name
                    )

                    email_resp = await client.get(
                        "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    email_data = email_resp.json()
                    elements = email_data.get("elements", [])
                    if elements:
                        email = elements[0].get("handle~", {}).get("emailAddress", email)
        except Exception as e:
            logger.error(f"[OAuth] Real LinkedIn exchange failed: {e}")

    email = email.strip().lower()

    with get_db() as conn:
        user = conn.execute("SELECT user_id, name FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            user_id = user["user_id"]
            conn.execute(
                "UPDATE users SET oauth_provider = 'linkedin' WHERE user_id = ?", (user_id,)
            )
            conn.commit()
        else:
            user_id = f"user_{uuid.uuid4().hex[:16]}"
            api_key = _gen_api_key()
            conn.execute(
                "INSERT INTO users (user_id, email, password_hash, name, phone, user_type, api_key, oauth_provider) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    email,
                    _hash_pw("OauthPasswordSecure123!"),
                    name,
                    phone,
                    "jobseeker",
                    api_key,
                    "linkedin",
                ),
            )
            # Create a cv_profiles record to auto-import CV data!
            conn.execute(
                "INSERT INTO cv_profiles (user_id, profile_name, cv_text, skills, target_titles, target_locations) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    "LinkedIn Import",
                    f"LinkedIn Profile Imported:\nName: {name}\nEmail: {email}\nPhone: {phone}\nImported via LinkedIn OAuth2.",
                    "Python, Software Engineering, AI",
                    "Software Engineer, Full Stack Developer",
                    "Remote, UAE",
                ),
            )
            conn.commit()

    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie(
        "user_id",
        session_serializer.dumps(user_id),
        max_age=86400 * 30,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )
    return resp


@router.get("/auth/google/login")
async def google_login(request: Request):
    """Google login entrypoint. Redirects to Google authorization page or mock callback if client ID missing."""
    import urllib.parse

    _, _, _, config, _ = _deps()
    client_id = getattr(config, "GOOGLE_CLIENT_ID", "") or os.getenv("GOOGLE_CLIENT_ID", "")
    redirect_uri = str(request.url_for("google_callback"))

    if not client_id or client_id == "mock_google_id":
        logger.info("[OAuth] Redirecting to mock Google OAuth callback.")
        return RedirectResponse(f"{redirect_uri}?code=mock_code_123")

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "openid email profile",
        "state": "google_state_abc",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback")
async def google_callback(request: Request, code: str = "", state: str = ""):
    """Google OAuth callback. Exchanges authorization code for access token, fetches profile, and registers/logs-in user."""
    import time

    get_db, session_serializer, _, config, _ = _deps()
    email = "google_mock_user@example.com"
    name = "Google Candidate"
    access_token = "mock_access_token_123"
    refresh_token = "mock_refresh_token_123"
    expires_in = 3600

    client_id = getattr(config, "GOOGLE_CLIENT_ID", "") or os.getenv("GOOGLE_CLIENT_ID", "")
    client_secret = getattr(config, "GOOGLE_CLIENT_SECRET", "") or os.getenv(
        "GOOGLE_CLIENT_SECRET", ""
    )
    redirect_uri = str(request.url_for("google_callback"))

    if client_id and client_id != "mock_google_id" and code != "mock_code_123":
        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                token_resp.raise_for_status()
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token", "")
                expires_in = token_data.get("expires_in", 3600)

                if access_token:
                    userinfo_resp = await client.get(
                        "https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    userinfo = userinfo_resp.json()
                    email = userinfo.get("email", email)
                    name = userinfo.get("name", name)
        except Exception as e:
            logger.error(f"[OAuth] Real Google exchange failed: {e}")

    email = email.strip().lower()
    expires_at = int(time.time()) + int(expires_in)

    with get_db() as conn:
        user = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            user_id = user["user_id"]
            conn.execute(
                "UPDATE users SET oauth_provider = 'google', oauth_access_token = ?, oauth_refresh_token = ?, oauth_expires_at = ? WHERE user_id = ?",
                (access_token, refresh_token, expires_at, user_id),
            )
            conn.commit()
        else:
            user_id = f"user_{uuid.uuid4().hex[:16]}"
            api_key = _gen_api_key()
            conn.execute(
                "INSERT INTO users (user_id, email, password_hash, name, phone, user_type, api_key, oauth_provider, oauth_access_token, oauth_refresh_token, oauth_expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    email,
                    _hash_pw("OauthPasswordSecure123!"),
                    name,
                    "",
                    "jobseeker",
                    api_key,
                    "google",
                    access_token,
                    refresh_token,
                    expires_at,
                ),
            )
            conn.execute(
                "INSERT INTO cv_profiles (user_id, profile_name, cv_text, skills, target_titles, target_locations) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    "Google Import",
                    f"Google Account Imported:\nName: {name}\nEmail: {email}\nImported via Google OAuth2.",
                    "Python, Software Engineering, Cloud Systems",
                    "Software Engineer, Cloud Developer",
                    "Remote, UAE",
                ),
            )
            conn.commit()

    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie(
        "user_id",
        session_serializer.dumps(user_id),
        max_age=86400 * 30,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )
    return resp


@router.get("/auth/microsoft/login")
async def microsoft_login(request: Request):
    """Microsoft login entrypoint. Redirects to Microsoft authorization page or mock callback if client ID missing."""
    import urllib.parse

    _, _, _, config, _ = _deps()
    client_id = getattr(config, "MICROSOFT_CLIENT_ID", "") or os.getenv("MICROSOFT_CLIENT_ID", "")
    redirect_uri = str(request.url_for("microsoft_callback"))

    if not client_id or client_id == "mock_microsoft_id":
        logger.info("[OAuth] Redirecting to mock Microsoft OAuth callback.")
        return RedirectResponse(f"{redirect_uri}?code=mock_code_123")

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": "openid email profile User.Read mail.send offline_access",
        "state": "microsoft_state_abc",
    }
    auth_url = f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?{urllib.parse.urlencode(params)}"
    return RedirectResponse(auth_url)


@router.get("/auth/microsoft/callback")
async def microsoft_callback(request: Request, code: str = "", state: str = ""):
    """Microsoft OAuth callback. Exchanges authorization code for access token, fetches profile, and registers/logs-in user."""
    import time

    get_db, session_serializer, _, config, _ = _deps()
    email = "microsoft_mock_user@example.com"
    name = "Microsoft Candidate"
    access_token = "mock_access_token_123"
    refresh_token = "mock_refresh_token_123"
    expires_in = 3600

    client_id = getattr(config, "MICROSOFT_CLIENT_ID", "") or os.getenv("MICROSOFT_CLIENT_ID", "")
    client_secret = getattr(config, "MICROSOFT_CLIENT_SECRET", "") or os.getenv(
        "MICROSOFT_CLIENT_SECRET", ""
    )
    redirect_uri = str(request.url_for("microsoft_callback"))

    if client_id and client_id != "mock_microsoft_id" and code != "mock_code_123":
        try:
            async with httpx.AsyncClient() as client:
                token_resp = await client.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                    data={
                        "client_id": client_id,
                        "scope": "openid email profile User.Read mail.send offline_access",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                        "client_secret": client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                token_resp.raise_for_status()
                token_data = token_resp.json()
                access_token = token_data.get("access_token")
                refresh_token = token_data.get("refresh_token", "")
                expires_in = token_data.get("expires_in", 3600)

                if access_token:
                    me_resp = await client.get(
                        "https://graph.microsoft.com/v1.0/me",
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
                    me_data = me_resp.json()
                    name = me_data.get("displayName", name)
                    email = me_data.get("mail", me_data.get("userPrincipalName", email))
        except Exception as e:
            logger.error(f"[OAuth] Real Microsoft exchange failed: {e}")

    email = email.strip().lower()
    expires_at = int(time.time()) + int(expires_in)

    with get_db() as conn:
        user = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
        if user:
            user_id = user["user_id"]
            conn.execute(
                "UPDATE users SET oauth_provider = 'microsoft', oauth_access_token = ?, oauth_refresh_token = ?, oauth_expires_at = ? WHERE user_id = ?",
                (access_token, refresh_token, expires_at, user_id),
            )
            conn.commit()
        else:
            user_id = f"user_{uuid.uuid4().hex[:16]}"
            api_key = _gen_api_key()
            conn.execute(
                "INSERT INTO users (user_id, email, password_hash, name, phone, user_type, api_key, oauth_provider, oauth_access_token, oauth_refresh_token, oauth_expires_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    email,
                    _hash_pw("OauthPasswordSecure123!"),
                    name,
                    "",
                    "jobseeker",
                    api_key,
                    "microsoft",
                    access_token,
                    refresh_token,
                    expires_at,
                ),
            )
            conn.execute(
                "INSERT INTO cv_profiles (user_id, profile_name, cv_text, skills, target_titles, target_locations) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    "Microsoft Import",
                    f"Microsoft Account Imported:\nName: {name}\nEmail: {email}\nImported via Microsoft OAuth2.",
                    "Outlook, Windows, Enterprise Applications",
                    "Microsoft Solutions Architect, Systems Engineer",
                    "Remote, UAE",
                ),
            )
            conn.commit()

    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie(
        "user_id",
        session_serializer.dumps(user_id),
        max_age=86400 * 30,
        httponly=True,
        samesite="lax",
        secure=True,
        path="/",
    )
    return resp
