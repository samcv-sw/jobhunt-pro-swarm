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
    raise RuntimeError("SECRET_KEY environment variable is not set.")
session_serializer = URLSafeTimedSerializer(SECRET_KEY)

# Template engine
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

_orig_tr = templates.TemplateResponse
def _patched_tr(request, name, context=None, **kwargs):
    if context is None:
        context = {}
    lang = getattr(request.state, "locale", "ar")
    context.setdefault("lang", lang)
    context.setdefault("dir", "rtl" if lang == "ar" else "ltr")
    context.setdefault("_", getattr(request.state, "_", lambda s: s))
    context.setdefault("VERSION", getattr(config, "VERSION", "1.0"))
    if lang == "en" and (template_dir / "en" / name).exists():
        name = f"en/{name}"
    return _orig_tr(request, name, context, **kwargs)
templates.TemplateResponse = _patched_tr

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(template_dir)),
    undefined=jinja2.DebugUndefined,
)

# Database
_BASE_DIR = Path(__file__).parent
_db_val = getattr(config, "DB_PATH", None) or "data/jobhunt_saas_v2.db"
if os.path.isabs(_db_val):
    db_path = _db_val
else:
    db_path = str(_BASE_DIR.parent / _db_val)

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

    # Strategy 2: Neon PostgreSQL
    db_url = os.getenv("DATABASE_URL") or getattr(config, "DATABASE_URL", None)
    if db_url and db_url.startswith("postgresql"):
        try:
            if os.getenv("SUPABASE_MODE"):
                import core.supabase_rest_shim as shim
            else:
                import core.pg_sqlite_shim as shim

            # Simple connection builder utilizing pg_sqlite_shim connection mapping
            return shim.connect(db_url)
        except Exception as e:
            logger.warning(f"[DB] Neon shim connection creation failed: {e}")

    # Strategy 3: SQLite Local Fallback (pointing strictly to jobhunt_saas_v2.db)
    for attempt in range(max_retries):
        try:
            import core.pg_sqlite_shim as shim
            conn = shim.connect(db_path, check_same_thread=False, timeout=60)
            try:
                is_pa = bool(
                    os.environ.get("PYTHONANYWHERE_SITE") or
                    os.environ.get("PYTHONANYWHERE_DOMAIN")
                )
                if is_pa:
                    conn.execute("PRAGMA journal_mode=DELETE")
                    conn.execute("PRAGMA synchronous=FULL")
                else:
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
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
        except (BadSignature, SignatureExpired):
            pass
    try:
        s = request.session.get("user")
        if s and s.get("id"):
            return s["id"]
    except Exception:
        pass
    return None

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "")
def is_admin_email(email: str) -> bool:
    admins = {"samatou683@gmail.com", "samsalameh.cv@gmail.com"}
    if ADMIN_EMAIL:
        admins.add(ADMIN_EMAIL)
    return email in admins

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

    is_pa = bool(
        os.environ.get("PYTHONANYWHERE_SITE") or
        os.environ.get("PYTHONANYWHERE_DOMAIN")
    )
    if is_pa:
        if ip not in store:
            store[ip] = [now, 1]
            return True
        last_time, count = store[ip]
        if now - last_time > window_seconds:
            store[ip] = [now, 1]
            return True
        if count >= max_count:
            return False
        store[ip] = [last_time, count+1]
        return True

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
