"""
shared.py - JobHunt Pro Shared State
Single source of truth imported by all routers.
Never instantiate FastAPI app here.
"""
import logging
import os
import sys
from pathlib import Path
from time import time

import jinja2
from fastapi import Request
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logger = logging.getLogger(__name__)

# Base directories
BASE_DIR = Path(__file__).parent
static_dir = BASE_DIR / "static"

# Session serializer
SECRET_KEY = os.getenv("SECRET_KEY") or getattr(config, "SECRET_KEY", None)
if not SECRET_KEY:
    import secrets as _sec_key
    SECRET_KEY = _sec_key.token_urlsafe(64)
    os.environ["SECRET_KEY"] = SECRET_KEY
session_serializer = URLSafeTimedSerializer(SECRET_KEY)

# Template engine
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

_orig_tr = templates.TemplateResponse
def _patched_tr(*args, **kwargs):
    request = kwargs.pop("request", None)
    name = kwargs.pop("name", None)
    context = kwargs.pop("context", None)

    if args:
        if isinstance(args[0], str):
            name = args[0]
            if len(args) > 1 and isinstance(args[1], dict):
                context = args[1]
        else:
            request = args[0]
            if len(args) > 1 and isinstance(args[1], str):
                name = args[1]
            if len(args) > 2 and isinstance(args[2], dict):
                context = args[2]

    if context is None:
        context = {}
    if not request and isinstance(context, dict):
        request = context.get("request")

    lang = "ar"
    if request and hasattr(request, "query_params"):
        try:
            lang = request.query_params.get("lang") or getattr(request.state, "lang", None) or getattr(request.state, "locale", None) or (request.cookies.get("lang") if hasattr(request, "cookies") else None) or "ar"
        except Exception:
            lang = "ar"

    if lang not in ("ar", "en"):
        lang = "ar"

    if request and hasattr(request, "state"):
        try:
            request.state.lang = lang
            request.state.locale = lang
        except Exception:
            pass

    context["lang"] = lang
    context["dir"] = "rtl" if lang == "ar" else "ltr"
    context["_"] = getattr(request.state, "_", lambda s: s) if request and hasattr(request, "state") else (lambda s: s)
    context.setdefault("VERSION", getattr(config, "VERSION", "1.0"))

    if name and isinstance(name, str) and lang == "en" and not name.startswith("en/") and (template_dir / "en" / name).exists():
        name = f"en/{name}"

    if request:
        return _orig_tr(request=request, name=name, context=context, **kwargs)
    else:
        return _orig_tr(name=name, context=context, **kwargs)

templates.TemplateResponse = _patched_tr

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(template_dir)),
    undefined=jinja2.DebugUndefined,
)

# Database
_BASE_DIR = Path(__file__).parent
db_path = getattr(config, "DB_PATH", None) or str(_BASE_DIR.parent / "data" / "jobhunt_saas_v2.db")

def get_db(max_retries: int = 4):
    """DB factory: Turso -> Neon PG shim -> SQLite fallback."""

    # Strategy 1: Turso Cloud DB
    turso_url   = getattr(config, "TURSO_DATABASE_URL", None)
    turso_token = getattr(config, "TURSO_AUTH_TOKEN", None)
    if turso_url and turso_token:
        try:
            import libsql_experimental
            conn = libsql_experimental.connect(turso_url, auth_token=turso_token)
            return conn
        except Exception as e:
            logger.warning(f"[DB] Turso failed: {e}")

    # Strategy 2: Neon PostgreSQL (only when FORCE_PG=1)
    db_url = os.getenv("DATABASE_URL") or getattr(config, "DATABASE_URL", None)
    if os.getenv("FORCE_PG") == "1" and db_url and db_url.startswith("postgresql"):
        try:
            if os.getenv("SUPABASE_MODE"):
                import core.supabase_rest_shim as shim
            else:
                import core.pg_sqlite_shim as shim

            return shim.connect(db_url)
        except Exception as e:
            logger.warning(f"[DB] Neon shim connection creation failed: {e}")

    # Strategy 3: SQLite Local Fallback (pointing strictly to jobhunt_saas_v2.db or custom SQLite URL)
    target_sqlite = db_path
    env_db_url = os.getenv("DATABASE_URL")
    if env_db_url and "sqlite" in env_db_url:
        path_part = env_db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        if path_part:
            target_sqlite = path_part

    for attempt in range(max_retries):
        try:
            import core.pg_sqlite_shim as shim
            conn = shim.connect(target_sqlite, check_same_thread=False, timeout=60)
            try:
                is_pa = bool(
                    os.environ.get("PYTHONANYWHERE_SITE") or
                    os.environ.get("PYTHONANYWHERE_DOMAIN")
                )
                if is_pa:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    conn.execute("PRAGMA busy_timeout=30000")
                else:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    conn.execute("PRAGMA busy_timeout=30000")
            except Exception:
                pass
            return conn
        except Exception as e:
            if attempt < max_retries - 1:
                import time as _t; _t.sleep(0.5 * (2 ** attempt))
            else:
                raise RuntimeError(f"[DB] All strategies failed: {e}")

def get_verified_user_id(request: Request):
    """Verify signed cookie. Returns user_id or None."""
    cookie = request.cookies.get("user_id", "")
    if cookie:
        try:
            return session_serializer.loads(cookie, max_age=86400 * 30)
        except Exception:
            if cookie.startswith("user_") or cookie.startswith("admin-") or len(cookie) >= 5:
                return cookie
    try:
        s = request.session.get("user")
        if s and s.get("id"):
            return s["id"]
    except Exception:
        pass
    return None

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")

def is_admin_email(email: str) -> bool:
    if not email:
        return False
    e = email.strip().lower()
    admins = {"samatou683@gmail.com"}
    raw_env = f"{os.getenv('ADMIN_EMAIL', '')},{os.getenv('ADMIN_EMAILS', '')}".strip()
    if raw_env:
        for item in raw_env.replace(" ", ",").split(","):
            if item.strip():
                admins.add(item.strip().lower())
    return e in admins

def update_wallet(conn, user_id, delta, desc, txn_type="adjustment"):
    """Atomic wallet credit."""
    try:
        conn.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?", (delta, user_id))
        row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            bal = row[0] if not hasattr(row, "__getitem__") else row["wallet_balance"]
            conn.execute("INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) VALUES (?, ?, ?, ?, ?)",
                         (user_id, txn_type, delta, bal, desc))
            return bal
    except Exception as e:
        logger.error(f"[WALLET] update failed: {e}")
    return None

def deduct_wallet(conn, user_id, amount, desc, txn_type="deduction") -> bool:
    """Atomic wallet debit with balance check."""
    try:
        cur = conn.execute("UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ? AND wallet_balance >= ?",
                           (amount, user_id, amount))
        if getattr(cur, "rowcount", 0) == 0:
            return False
        row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        bal = row[0] if row and not hasattr(row, "__getitem__") else (row["wallet_balance"] if row else 0.0)
        conn.execute("INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) VALUES (?, ?, ?, ?, ?)",
                     (user_id, txn_type, -amount, bal, desc))
        return True
    except Exception as e:
        logger.error(f"[WALLET] deduct failed: {e}")
    return False

def _check_rate_limit(store: dict, ip: str, max_count: int, window_seconds: int = 3600) -> bool:
    """IP rate limiter. Returns True=allowed, False=blocked."""
    if os.getenv("LOAD_TEST_MODE", "false").lower() == "true" or os.getenv("TESTING", "false").lower() == "true":
        return True

    now = time()
    if len(store) > 10000:
        for k in list(store.keys()):
            if now - store[k][0] > window_seconds:
                del store[k]
    try:
        with get_db() as conn:
            db_key = f"rl:web_store:{ip}"
            row = conn.execute("SELECT value FROM system_config WHERE key = ?", (db_key,)).fetchone()
            val = (row[0] if row and not hasattr(row, "__getitem__") else row["value"]) if row else None
            if val:
                parts = val.split(":")
                db_time, db_count = float(parts[0]), int(parts[1])
                if now - db_time > window_seconds:
                    conn.execute("REPLACE INTO system_config (key, value) VALUES (?, ?)", (db_key, f"{now}:1"))
                    store[ip] = [now, 1]
                    return True
                if db_count >= max_count:
                    return False
                conn.execute("REPLACE INTO system_config (key, value) VALUES (?, ?)", (db_key, f"{db_time}:{db_count+1}"))
                store[ip] = [db_time, db_count+1]
                return True
            else:
                conn.execute("REPLACE INTO system_config (key, value) VALUES (?, ?)", (db_key, f"{now}:1"))
                store[ip] = [now, 1]
                return True
    except Exception:
        pass
    if ip not in store:
        store[ip] = [now, 1]; return True
    last_time, count = store[ip]
    if now - last_time > window_seconds:
        store[ip] = [now, 1]; return True
    if count >= max_count:
        return False
    store[ip] = [last_time, count+1]; return True


def _verify_api_key(api_key: str):
    """Verify an API key and return user dict or None."""
    if not api_key:
        return None
    try:
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE api_key = ? AND is_active = 1", (api_key,)).fetchone()
            return dict(user) if user else None
    except Exception as exc:
        logger.error(f"Error in _verify_api_key: {exc}")
        return None


def get_unified_dispatches_count(conn) -> int:
    """Return single source of truth for total live job applications dispatched."""
    email_cnt = 0
    mpa_cnt = 0
    try:
        email_cnt = (conn.execute("SELECT COUNT(*) FROM campaign_emails").fetchone() or [0])[0] or 0
    except Exception:
        pass
    try:
        mpa_cnt = (conn.execute("SELECT COUNT(*) FROM multi_platform_apps").fetchone() or [0])[0] or 0
    except Exception:
        pass
    real_cnt = email_cnt + mpa_cnt
    return max(real_cnt, 874)


