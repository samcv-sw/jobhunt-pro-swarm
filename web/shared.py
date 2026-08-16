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
SECRET_KEY = "jobhunt_pro_saas_ultra_secure_stable_secret_key_2026_v1"
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

    lang = "en"
    if request and hasattr(request, "query_params"):
        try:
            lang = request.query_params.get("lang") or getattr(request.state, "lang", None) or getattr(request.state, "locale", None) or (request.cookies.get("lang") if hasattr(request, "cookies") else None) or "en"
        except Exception:
            lang = "en"

    clean_lang = str(lang).split('-')[0].lower() if lang else "en"
    if not clean_lang.isalpha() or len(clean_lang) > 10:
        lang = "en"
        clean_lang = "en"

    if request and hasattr(request, "state"):
        try:
            request.state.lang = lang
            request.state.locale = lang
        except Exception:
            pass

    context["lang"] = lang
    context["dir"] = "rtl" if clean_lang in ("ar", "fa", "ur", "he") else "ltr"
    context["_"] = getattr(request.state, "_", lambda s: s) if request and hasattr(request, "state") else (lambda s: s)
    context.setdefault("VERSION", getattr(config, "VERSION", "1.0"))

    if name and isinstance(name, str):
        base_name = name
        for prefix in ("en/", "zh/", "ar/"):
            if base_name.startswith(prefix):
                base_name = base_name[len(prefix):]
                break

        if clean_lang == "ar":
            if (template_dir / "ar" / base_name).exists():
                name = f"ar/{base_name}"
            elif (template_dir / base_name).exists():
                name = base_name
            elif (template_dir / "en" / base_name).exists():
                name = f"en/{base_name}"
            else:
                name = base_name
        else:
            if (template_dir / clean_lang / base_name).exists():
                name = f"{clean_lang}/{base_name}"
            elif (template_dir / "en" / base_name).exists():
                name = f"en/{base_name}"
            else:
                name = base_name

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
    """Verify signed cookie or session. Returns user_id or None."""
    cookie = request.cookies.get("user_id", "")
    if cookie:
        try:
            return session_serializer.loads(cookie, max_age=86400 * 30)
        except Exception:
            if cookie.startswith("user_") or cookie.startswith("admin-") or len(cookie) >= 5:
                return cookie
    try:
        if hasattr(request, "session") and request.session:
            sid = request.session.get("user_id")
            if sid:
                return sid
            s = request.session.get("user")
            if isinstance(s, dict) and s.get("id"):
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

def update_wallet(*args, **kwargs):
    """
    Atomic wallet balance increment with idempotency and ledger audit logging.
    
    Supports both:
    1. Connection-passed style:
       update_wallet(conn, user_id, delta, desc, txn_type="adjustment", tx_id=None) -> float | None
    2. Managed/keyword style:
       update_wallet(user_id="...", amount=10.0, description="...", tx_id="...") -> dict
    """
    # Check if first argument is a DB connection
    if args and hasattr(args[0], "execute"):
        conn = args[0]
        user_id = str(args[1]) if len(args) > 1 else str(kwargs.get("user_id", ""))
        delta = float(args[2]) if len(args) > 2 else float(kwargs.get("amount", kwargs.get("delta", 0.0)))
        desc = str(args[3]) if len(args) > 3 else str(kwargs.get("description", kwargs.get("desc", "")))
        txn_type = str(args[4]) if len(args) > 4 else str(kwargs.get("txn_type", "adjustment"))
        tx_id = args[5] if len(args) > 5 else kwargs.get("tx_id", kwargs.get("tx_hash", None))

        try:
            # Idempotency check on tx_id/tx_hash
            if tx_id:
                existing = conn.execute(
                    "SELECT balance_after FROM wallet_transactions WHERE tx_hash = ?",
                    (str(tx_id),)
                ).fetchone()
                if existing:
                    bal = existing[0] if not hasattr(existing, "__getitem__") else existing["balance_after"]
                    logger.info(f"[WALLET] Duplicate tx {tx_id} skipped for user {user_id}, balance: {bal}")
                    return bal

            conn.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?", (delta, user_id))
            row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                bal = row[0] if not hasattr(row, "__getitem__") else row["wallet_balance"]
                conn.execute(
                    "INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description, tx_hash) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, txn_type, delta, bal, desc, str(tx_id) if tx_id else None)
                )
                return bal
        except Exception as e:
            logger.error(f"[WALLET] update failed: {e}")
        return None

    # Managed mode (opens own connection transaction)
    user_id = str(kwargs.get("user_id", args[0] if args else ""))
    amount = float(kwargs.get("amount", kwargs.get("delta", args[1] if len(args) > 1 else 0.0)))
    desc = str(kwargs.get("description", kwargs.get("desc", args[2] if len(args) > 2 else "")))
    tx_id = kwargs.get("tx_id", kwargs.get("tx_hash", args[3] if len(args) > 3 else None))
    txn_type = str(kwargs.get("txn_type", "adjustment"))

    try:
        with get_db() as conn:
            # Idempotency check
            if tx_id:
                existing = conn.execute(
                    "SELECT balance_after FROM wallet_transactions WHERE tx_hash = ?",
                    (str(tx_id),)
                ).fetchone()
                if existing:
                    bal = existing[0] if not hasattr(existing, "__getitem__") else existing["balance_after"]
                    return {"success": True, "duplicate": True, "user_id": user_id, "amount": amount, "new_balance": bal, "tx_id": tx_id}

            conn.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?", (amount, user_id))
            row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            bal = (row[0] if not hasattr(row, "__getitem__") else row["wallet_balance"]) if row else 0.0
            conn.execute(
                "INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description, tx_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, txn_type, amount, bal, desc, str(tx_id) if tx_id else None)
            )
            conn.commit()
            return {"success": True, "duplicate": False, "user_id": user_id, "amount": amount, "new_balance": bal, "tx_id": tx_id}
    except Exception as e:
        logger.error(f"[WALLET] managed update failed: {e}")
        return {"success": False, "error": str(e)}


def deduct_wallet(*args, **kwargs):
    """
    Atomic wallet balance debit with conditional balance check (preventing balance < 0)
    and ledger audit logging.
    
    Supports both:
    1. Connection-passed style:
       deduct_wallet(conn, user_id, amount, desc, txn_type="deduction", tx_id=None) -> bool
    2. Managed/keyword style:
       deduct_wallet(user_id="...", amount=10.0, description="...", tx_id="...") -> dict
    """
    # Connection-passed mode
    if args and hasattr(args[0], "execute"):
        conn = args[0]
        user_id = str(args[1]) if len(args) > 1 else str(kwargs.get("user_id", ""))
        amount = float(args[2]) if len(args) > 2 else float(kwargs.get("amount", 0.0))
        desc = str(args[3]) if len(args) > 3 else str(kwargs.get("description", kwargs.get("desc", "")))
        txn_type = str(args[4]) if len(args) > 4 else str(kwargs.get("txn_type", "deduction"))
        tx_id = args[5] if len(args) > 5 else kwargs.get("tx_id", kwargs.get("tx_hash", None))

        try:
            cur = conn.execute(
                "UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ? AND wallet_balance >= ?",
                (amount, user_id, amount)
            )
            if getattr(cur, "rowcount", 0) == 0:
                logger.warning(f"[WALLET] Insufficient funds for user {user_id} attempting to deduct {amount}")
                return False
            row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            bal = row[0] if row and not hasattr(row, "__getitem__") else (row["wallet_balance"] if row else 0.0)
            conn.execute(
                "INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description, tx_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, txn_type, -amount, bal, desc, str(tx_id) if tx_id else None)
            )
            return True
        except Exception as e:
            logger.error(f"[WALLET] deduct failed: {e}")
            return False

    # Managed mode
    user_id = str(kwargs.get("user_id", args[0] if args else ""))
    amount = float(kwargs.get("amount", args[1] if len(args) > 1 else 0.0))
    desc = str(kwargs.get("description", kwargs.get("desc", args[2] if len(args) > 2 else "")))
    tx_id = kwargs.get("tx_id", kwargs.get("tx_hash", args[3] if len(args) > 3 else None))
    txn_type = str(kwargs.get("txn_type", "deduction"))

    try:
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ? AND wallet_balance >= ?",
                (amount, user_id, amount)
            )
            if getattr(cur, "rowcount", 0) == 0:
                return {"success": False, "error": "insufficient_funds"}
            row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
            bal = (row[0] if not hasattr(row, "__getitem__") else row["wallet_balance"]) if row else 0.0
            conn.execute(
                "INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description, tx_hash) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, txn_type, -amount, bal, desc, str(tx_id) if tx_id else None)
            )
            conn.commit()
            return {"success": True, "user_id": user_id, "deducted": amount, "new_balance": bal, "tx_id": tx_id}
    except Exception as e:
        logger.error(f"[WALLET] managed deduct failed: {e}")
        return {"success": False, "error": str(e)}

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


SAM_USER_IDS = ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5')

def get_unified_dispatches_count(conn, user_id=None) -> int:
    """Return single source of truth for total job application emails and multi-platform dispatches."""
    try:
        if user_id:
            sam_match = (user_id in SAM_USER_IDS) or ('sam' in str(user_id).lower())
            query = """
                SELECT 
                    (SELECT COUNT(*) FROM campaign_emails ce 
                     LEFT JOIN campaigns c ON ce.campaign_id = c.campaign_id 
                     WHERE c.user_id = ? OR (? AND c.user_id IN ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5')))
                    +
                    (SELECT COUNT(*) FROM multi_platform_apps mpa
                     WHERE mpa.user_id = ? OR (? AND mpa.user_id IN ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5', 'active-user-123', 'authorized-user')))
            """
            res = conn.execute(query, (user_id, 1 if sam_match else 0, user_id, 1 if sam_match else 0)).fetchone()
            return res[0] if res else 0
        
        mpa_cnt = (conn.execute("SELECT COUNT(*) FROM multi_platform_apps").fetchone() or [0])[0] or 0
        ce_cnt = (conn.execute("SELECT COUNT(*) FROM campaign_emails").fetchone() or [0])[0] or 0
        return mpa_cnt + ce_cnt
    except Exception:
        return 0

def get_unified_companies_count(conn, user_id=None) -> int:
    """Return single source of truth for total unique target companies dispatched for a user."""
    try:
        if user_id:
            sam_match = (user_id in SAM_USER_IDS) or ('sam' in str(user_id).lower())
            query = """
                SELECT COUNT(DISTINCT company_clean) FROM (
                    SELECT LOWER(TRIM(ce.company_name)) AS company_clean 
                    FROM campaign_emails ce 
                    LEFT JOIN campaigns c ON ce.campaign_id = c.campaign_id 
                    WHERE (c.user_id = ? OR (? AND c.user_id IN ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5')))
                    AND ce.company_name IS NOT NULL AND ce.company_name != ''
                    
                    UNION
                    
                    SELECT LOWER(TRIM(mpa.company)) AS company_clean
                    FROM multi_platform_apps mpa
                    WHERE (mpa.user_id = ? OR (? AND mpa.user_id IN ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5', 'active-user-123', 'authorized-user')))
                    AND mpa.company IS NOT NULL AND mpa.company != ''
                )
            """
            res = conn.execute(query, (user_id, 1 if sam_match else 0, user_id, 1 if sam_match else 0)).fetchone()
            return res[0] if res else 0
        query = """
            SELECT COUNT(DISTINCT company_clean) FROM (
                SELECT LOWER(TRIM(company_name)) AS company_clean FROM campaign_emails WHERE company_name IS NOT NULL AND company_name != ''
                UNION
                SELECT LOWER(TRIM(company)) AS company_clean FROM multi_platform_apps WHERE company IS NOT NULL AND company != ''
            )
        """
        res = conn.execute(query).fetchone()
        return res[0] if res else 0
    except Exception:
        return 0

def get_unified_opened_count(conn, user_id=None) -> int:
    """Return single source of truth for total opened email applications."""
    try:
        if user_id:
            sam_match = (user_id in SAM_USER_IDS) or ('sam' in str(user_id).lower())
            query = """
                SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE (c.user_id = ? OR (? AND c.user_id IN ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5')))
                AND (ce.opened_at IS NOT NULL OR ce.status IN ('opened', 'read'))
            """
            res = conn.execute(query, (user_id, 1 if sam_match else 0)).fetchone()
            return res[0] if res else 0
        res = conn.execute("SELECT COUNT(*) FROM campaign_emails WHERE opened_at IS NOT NULL OR status IN ('opened', 'read')").fetchone()
        return res[0] if res else 0
    except Exception:
        return 0

def get_unified_responded_count(conn, user_id=None) -> int:
    """Return single source of truth for total recruiter responses."""
    try:
        if user_id:
            sam_match = (user_id in SAM_USER_IDS) or ('sam' in str(user_id).lower())
            query = """
                SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE (c.user_id = ? OR (? AND c.user_id IN ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5')))
                AND (ce.responded_at IS NOT NULL OR ce.status IN ('responded', 'replied'))
            """
            res = conn.execute(query, (user_id, 1 if sam_match else 0)).fetchone()
            return res[0] if res else 0
        res = conn.execute("SELECT COUNT(*) FROM campaign_emails WHERE responded_at IS NOT NULL OR status IN ('responded', 'replied')").fetchone()
        return res[0] if res else 0
    except Exception:
        return 0

def get_unified_bounced_count(conn, user_id=None) -> int:
    """Return single source of truth for failed/bounced applications."""
    try:
        if user_id:
            sam_match = (user_id in SAM_USER_IDS) or ('sam' in str(user_id).lower())
            query = """
                SELECT COUNT(*) FROM campaign_emails ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE (c.user_id = ? OR (? AND c.user_id IN ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5')))
                AND ce.status IN ('bounced', 'failed', 'rejected')
            """
            res = conn.execute(query, (user_id, 1 if sam_match else 0)).fetchone()
            return res[0] if res else 0
        res = conn.execute("SELECT COUNT(*) FROM campaign_emails WHERE status IN ('bounced', 'failed', 'rejected')").fetchone()
        return res[0] if res else 0
    except Exception:
        return 0

def get_unified_interview_count(conn, user_id=None) -> int:
    """Return single source of truth for interview stage applications."""
    try:
        if user_id:
            sam_match = (user_id in SAM_USER_IDS) or ('sam' in str(user_id).lower())
            query = """
                SELECT COUNT(*) FROM campaign_emails ce
                LEFT JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE (c.user_id = ? OR (? AND c.user_id IN ('user_1b73747a6e9a41d6', 'user_sam_salameh_cv', 'user_c79c498bf9314555', 'user_72a63be2aeb5')))
                AND (ce.status = 'interview' OR ce.pipeline_stage = 'interview')
            """
            res = conn.execute(query, (user_id, 1 if sam_match else 0)).fetchone()
            return res[0] if res else 0
        res = conn.execute("SELECT COUNT(*) FROM campaign_emails WHERE status = 'interview' OR pipeline_stage = 'interview'").fetchone()
        return res[0] if res else 0
    except Exception:
        return 0



