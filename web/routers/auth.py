from core.pg_sqlite_shim import get_db
import os
import logging
import time
import requests
import bcrypt
import secrets
import uuid
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse


router = APIRouter()
logger = logging.getLogger(__name__)

# Constants and environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "https://jhfguf.pythonanywhere.com/auth/google/callback"
)

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_REDIRECT_URI = os.getenv(
    "MICROSOFT_REDIRECT_URI",
    "https://jhfguf.pythonanywhere.com/auth/microsoft/callback",
)

_login_attempts = {}
_forgot_attempts = {}


def get_session_serializer():
    from itsdangerous import URLSafeTimedSerializer
    import config

    SECRET_KEY = os.getenv("SECRET_KEY") or getattr(config, "SECRET_KEY", None)
    if not SECRET_KEY:
        raise RuntimeError("SECRET_KEY not set")
    return URLSafeTimedSerializer(SECRET_KEY)


def generate_api_key():
    import uuid

    return f"jh_{uuid.uuid4().hex}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    import bcrypt

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def _check_rate_limit(
    store: dict, ip: str, window_seconds: int = 3600, max_count: int = 10
) -> bool:
    now = time.time()
    try:
        conn = get_db()
        db_key = f"rate_limit:{ip}"
        row = conn.execute(
            "SELECT value FROM system_config WHERE key = ?", (db_key,)
        ).fetchone()
        if row:
            db_time, db_count = map(float, row["value"].split(":"))
            if now - db_time > window_seconds:
                conn.execute(
                    "REPLACE INTO system_config (key, value) VALUES (?, ?)",
                    (db_key, f"{now}:1"),
                )
                conn.commit()
                conn.close()
                store[ip] = [now, 1]
                return True
            if db_count >= max_count:
                conn.close()
                return False
            conn.execute(
                "REPLACE INTO system_config (key, value) VALUES (?, ?)",
                (db_key, f"{db_time}:{int(db_count) + 1}"),
            )
            conn.commit()
            conn.close()
            store[ip] = [db_time, db_count + 1]
            return True
        else:
            conn.execute(
                "REPLACE INTO system_config (key, value) VALUES (?, ?)",
                (db_key, f"{now}:1"),
            )
            conn.commit()
            conn.close()
            store[ip] = [now, 1]
            return True
    except Exception:
        pass  # Fallback to in-memory

    if ip not in store:
        store[ip] = [now, 1]
        return True

    last_time, count = store[ip]
    if now - last_time > window_seconds:
        store[ip] = [now, 1]
        return True

    if count >= max_count:
        return False

    store[ip] = [last_time, count + 1]
    return True


def _check_login_rate_limit(ip: str) -> bool:
    return _check_rate_limit(_login_attempts, ip, max_count=10)


@router.get("/auth/google/login")
def google_login():
    scopes = [
        "openid",
        "email",
        "profile",
        "https://www.googleapis.com/auth/gmail.send",
    ]
    import urllib.parse

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(GOOGLE_REDIRECT_URI)}&"
        "response_type=code&"
        f"scope={' '.join(scopes)}&"
        "access_type=offline&prompt=consent"
    )
    return RedirectResponse(auth_url)


@router.get("/auth/google/callback")
def google_callback(code: str = None, error: str = None):
    if error or not code:
        return HTMLResponse(
            "<html><body><h3>OAuth Error</h3><p>Google authentication failed.</p><a href='/login'>Try again</a></body></html>"
        )

    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    if not resp.ok:
        return HTMLResponse(
            "<html><body><h3>OAuth Error</h3><p>Failed to exchange token.</p></body></html>"
        )

    tokens = resp.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_at = time.time() + tokens.get("expires_in", 3599)

    user_info = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()
    email, name = user_info.get("email"), user_info.get("name", "User")
    if not email:
        return HTMLResponse(
            "<html><body><h3>OAuth Error</h3><p>Email not provided by Google.</p></body></html>"
        )

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user:
        temp_pwd = secrets.token_urlsafe(16)
        pwd_hash = bcrypt.hashpw(temp_pwd.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        user_id = f"user_{uuid.uuid4().hex[:16]}"
        conn.execute(
            """INSERT INTO users (user_id, email, password_hash, name, api_key, oauth_provider, oauth_access_token, oauth_refresh_token, oauth_expires_at)
               VALUES (?, ?, ?, ?, ?, 'google', ?, ?, ?)""",
            (
                user_id,
                email,
                pwd_hash,
                name,
                generate_api_key(),
                access_token,
                refresh_token,
                expires_at,
            ),
        )
    else:
        user_id = user["user_id"]
        if refresh_token:
            conn.execute(
                "UPDATE users SET oauth_provider='google', oauth_access_token=?, oauth_refresh_token=?, oauth_expires_at=? WHERE user_id=?",
                (access_token, refresh_token, expires_at, user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET oauth_provider='google', oauth_access_token=?, oauth_expires_at=? WHERE user_id=?",
                (access_token, expires_at, user_id),
            )
    conn.commit()
    conn.close()

    response = RedirectResponse("/user-dashboard", status_code=303)
    response.set_cookie(
        "user_id",
        get_session_serializer().dumps(user_id),
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )
    return response


@router.get("/auth/microsoft/login")
def microsoft_login():
    scopes = [
        "openid",
        "email",
        "profile",
        "offline_access",
        "https://graph.microsoft.com/Mail.Send",
        "https://graph.microsoft.com/User.Read",
    ]
    import urllib.parse

    auth_url = (
        "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={MICROSOFT_CLIENT_ID}&"
        f"redirect_uri={urllib.parse.quote(MICROSOFT_REDIRECT_URI)}&"
        "response_type=code&"
        f"scope={'%20'.join(scopes)}&"
        "prompt=select_account"
    )
    return RedirectResponse(auth_url)


@router.get("/auth/microsoft/callback")
def microsoft_callback(code: str = None, error: str = None):
    if error or not code:
        return HTMLResponse(
            "<html><body><h3>OAuth Error</h3><p>Microsoft authentication failed.</p><a href='/login'>Try again</a></body></html>"
        )

    resp = requests.post(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        data={
            "client_id": MICROSOFT_CLIENT_ID,
            "client_secret": MICROSOFT_CLIENT_SECRET,
            "code": code,
            "redirect_uri": MICROSOFT_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
    )
    if not resp.ok:
        return HTMLResponse(
            "<html><body><h3>OAuth Error</h3><p>Token exchange failed.</p></body></html>"
        )

    tokens = resp.json()
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_at = time.time() + tokens.get("expires_in", 3599)

    user_info = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {access_token}"},
    ).json()
    email = user_info.get("mail") or user_info.get("userPrincipalName")
    name = user_info.get("displayName", "User")

    if not email:
        return HTMLResponse(
            "<html><body><h3>OAuth Error</h3><p>Email address not provided.</p></body></html>"
        )

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if not user:
        temp_pwd = secrets.token_urlsafe(16)
        pwd_hash = bcrypt.hashpw(temp_pwd.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        user_id = f"user_{uuid.uuid4().hex[:16]}"
        conn.execute(
            """INSERT INTO users (user_id, email, password_hash, name, api_key, oauth_provider, oauth_access_token, oauth_refresh_token, oauth_expires_at)
               VALUES (?, ?, ?, ?, ?, 'microsoft', ?, ?, ?)""",
            (
                user_id,
                email,
                pwd_hash,
                name,
                generate_api_key(),
                access_token,
                refresh_token,
                expires_at,
            ),
        )
    else:
        user_id = user["user_id"]
        if refresh_token:
            conn.execute(
                "UPDATE users SET oauth_provider='microsoft', oauth_access_token=?, oauth_refresh_token=?, oauth_expires_at=? WHERE user_id=?",
                (access_token, refresh_token, expires_at, user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET oauth_provider='microsoft', oauth_access_token=?, oauth_expires_at=? WHERE user_id=?",
                (access_token, expires_at, user_id),
            )
    conn.commit()
    conn.close()

    response = RedirectResponse("/user-dashboard", status_code=303)
    response.set_cookie(
        "user_id",
        get_session_serializer().dumps(user_id),
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )
    return response


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, plan: str = ""):
    from web.app_v2 import templates, config

    selected_plan = plan or request.cookies.get("last_selected_plan", "starter")
    return templates.TemplateResponse(
        request,
        "login_v2.html",
        {"selected_plan": selected_plan, "plan": plan, "VERSION": config.VERSION},
    )


@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    from web.app_v2 import templates

    client_ip = request.client.host if request.client else "unknown"
    if not _check_login_rate_limit(client_ip):
        return templates.TemplateResponse(
            request, "login_v2.html", {"error": "Too many login attempts."}
        )

    conn = get_db()
    account_key = f"login_lock:{email}"
    lockout = conn.execute(
        "SELECT value FROM system_config WHERE key = ?", (account_key,)
    ).fetchone()
    if lockout:
        try:
            if time.time() - float(lockout["value"]) < 1800:
                conn.close()
                return templates.TemplateResponse(
                    request,
                    "login_v2.html",
                    {"error": "Account locked. Try again in 30 minutes."},
                )
        except:
            pass

    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user and (user.get("is_active") == 0 or user.get("banned") == 1):
        conn.close()
        return templates.TemplateResponse(
            request, "login_v2.html", {"error": "Account disabled."}
        )

    if not user or not verify_password(password, user["password_hash"]):
        try:
            fail_key = f"login_fails:{email}"
            row = conn.execute(
                "SELECT value FROM system_config WHERE key = ?", (fail_key,)
            ).fetchone()
            fails = int(row["value"]) + 1 if row else 1
            conn.execute(
                "REPLACE INTO system_config (key, value) VALUES (?, ?)",
                (fail_key, str(fails)),
            )
            if fails >= 5:
                conn.execute(
                    "REPLACE INTO system_config (key, value) VALUES (?, ?)",
                    (account_key, str(time.time())),
                )
            conn.commit()
        except:
            pass
        conn.close()
        return templates.TemplateResponse(
            request, "login_v2.html", {"error": "Invalid credentials"}
        )

    try:
        conn.execute(
            "DELETE FROM system_config WHERE key = ?", (f"login_fails:{email}",)
        )
        conn.execute("DELETE FROM system_config WHERE key = ?", (account_key,))
        conn.commit()
    except:
        pass
    conn.close()

    response = RedirectResponse("/user-dashboard", status_code=303)
    response.set_cookie(
        "user_id",
        get_session_serializer().dumps(user["user_id"]),
        httponly=True,
        samesite="lax",
        max_age=86400 * 30,
    )
    return response


@router.get("/logout")
def logout(request: Request):
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("user_id", path="/")
    try:
        request.session.clear()
    except:
        pass
    return resp
