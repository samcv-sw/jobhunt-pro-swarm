import os
import json
import logging
import random
import sqlite3
import time
from datetime import datetime, date
from threading import Lock
from filelock import FileLock

logger = logging.getLogger(__name__)

_mutex = Lock()
_db_path = None
STATE_FILE = "ban_shield_state.json"
LOCK_FILE = "ban_shield_state.json.lock"

# ── Limits ────────────────────────────────────────────────────────────────
GMAIL_DAILY_CAP = 100
GMAIL_HOURLY_CAP = 15
BREVO_DAILY_CAP = 250
HOTMAIL_DAILY_CAP = 20000  # 1000 accounts x 50/day x 0.4 safety factor
HOTMAIL_HOURLY_CAP = 2000  # Spread across 1000 accounts = 2/hr each
GROQ_RPM_CAP = 20
GROQ_COOLDOWN_MS = 8000
GLOBAL_HOURLY_CAP = 2150  # Hotmail 2000 + Gmail 150
GLOBAL_DAILY_CAP = 21500  # Hotmail 20000 + Gmail 1500
WEEKEND_MULTIPLIER = 0.3
BUSINESS_HOURS_START = 7
BUSINESS_HOURS_END = 23  # Extended to 11PM for wider send window
MAX_FAILURES_BEFORE_COOLDOWN = 5
FAILURE_COOLDOWN_MINUTES = 30


def set_db_path(path: str):
    global _db_path, STATE_FILE, LOCK_FILE
    _db_path = path
    db_dir = os.path.dirname(path)
    STATE_FILE = os.path.join(db_dir, "ban_shield_state.json")
    LOCK_FILE = os.path.join(db_dir, "ban_shield_state.json.lock")
    _init_db()


def _init_db():
    if not _db_path:
        return
    with _mutex:
        try:
            conn = sqlite3.connect(_db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_sends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    account TEXT NOT NULL,
                    to_email TEXT NOT NULL,
                    success INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_sends_date ON email_sends(date, provider)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_sends_hour ON email_sends(date, hour, provider)"
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning(f"BanShield DB init failed: {e}")


def _count_today(provider: str, account: str = "*") -> int:
    if not _db_path:
        return 0
    today = date.today().isoformat()
    try:
        conn = sqlite3.connect(_db_path)
        if account == "*":
            row = conn.execute(
                "SELECT COUNT(*) FROM email_sends WHERE date = ? AND provider = ?",
                (today, provider),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM email_sends WHERE date = ? AND provider = ? AND account = ?",
                (today, provider, account),
            ).fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0


def _count_hour(provider: str, account: str = "*") -> int:
    if not _db_path:
        return 0
    today = date.today().isoformat()
    hour = datetime.now().hour
    try:
        conn = sqlite3.connect(_db_path)
        if account == "*":
            row = conn.execute(
                "SELECT COUNT(*) FROM email_sends WHERE date = ? AND hour = ? AND provider = ?",
                (today, hour, provider),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM email_sends WHERE date = ? AND hour = ? AND provider = ? AND account = ?",
                (today, hour, provider, account),
            ).fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0


def _record_send(provider: str, account: str, to_email: str, success: bool):
    if not _db_path:
        return
    today = date.today().isoformat()
    hour = datetime.now().hour
    try:
        conn = sqlite3.connect(_db_path)
        conn.execute(
            "INSERT INTO email_sends (date, hour, provider, account, to_email, success) VALUES (?, ?, ?, ?, ?, ?)",
            (today, hour, provider, account, to_email, 1 if success else 0),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"BanShield record failed: {e}")


def can_send_gmail(account_email: str) -> tuple[bool, str]:
    daily = _count_today("gmail", account_email)
    hourly = _count_hour("gmail", account_email)
    if daily >= GMAIL_DAILY_CAP:
        return False, f"Gmail daily cap ({GMAIL_DAILY_CAP}) reached for {account_email}"
    if hourly >= GMAIL_HOURLY_CAP:
        return (
            False,
            f"Gmail hourly cap ({GMAIL_HOURLY_CAP}) reached for {account_email}",
        )
    return True, "ok"


def can_send_brevo() -> tuple[bool, str]:
    daily = _count_today("brevo")
    if daily >= BREVO_DAILY_CAP:
        return False, f"Brevo daily cap ({BREVO_DAILY_CAP}) reached"
    return True, "ok"


def record_send(provider: str, account: str, to_email: str, success: bool):
    _record_send(provider, account, to_email, success)


def get_daily_stats() -> dict:
    return {
        "brevo": _count_today("brevo"),
        "brevo_remaining": max(0, BREVO_DAILY_CAP - _count_today("brevo")),
        "gmail_total": _count_today("gmail"),
        "gmail_remaining_per_account": GMAIL_DAILY_CAP,
    }


def random_delay(min_s: float = 15.0, max_s: float = 45.0) -> float:
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)
    return delay


def groq_throttle(key_index: int) -> float:
    base_delay = 0.5 + (key_index * 0.1)
    jitter = random.uniform(0, 1.0)
    delay = base_delay + jitter
    time.sleep(delay)
    return delay


# ── Zero-Risk Intelligence ─────────────────────────────────────────────────

PROVIDER_SAFE_LIMITS = {
    "gmail": {"daily": 80, "hourly": 12, "delay": (25, 70)},
    "brevo": {"daily": 250, "hourly": 40, "delay": (8, 25)},
    "sendgrid": {"daily": 100, "hourly": 15, "delay": (10, 30)},
    "mailjet": {"daily": 200, "hourly": 25, "delay": (8, 20)},
    "mailgun": {"daily": 100, "hourly": 15, "delay": (10, 30)},
    "elastic": {"daily": 100, "hourly": 15, "delay": (10, 30)},
    "zoho": {"daily": 250, "hourly": 30, "delay": (12, 35)},
    "outlook": {"daily": 300, "hourly": 40, "delay": (15, 40)},
    "yahoo": {"daily": 500, "hourly": 50, "delay": (10, 25)},
    "yandex": {"daily": 500, "hourly": 50, "delay": (10, 25)},
    "hotmail_pool": {"daily": 20000, "hourly": 2000, "delay": (5, 15)},
    "default": {"daily": 100, "hourly": 20, "delay": (15, 45)},
}

MULTI_PROVIDER_CAPS = {
    1: 21500,  # Single provider (Hotmail) = 21500/day
    2: 22000,
    3: 22500,
    4: 23000,
    5: 24000,
}


def _get_state():
    try:
        with FileLock(LOCK_FILE, timeout=5):
            if os.path.exists(STATE_FILE):
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
            else:
                state = {
                    "provider_counts": {},
                    "global_counts": {
                        "daily": 0,
                        "hourly": 0,
                        "last_reset_day": "",
                        "last_reset_hour": -1,
                    },
                    "failure_tracker": {"consecutive": 0, "cooldown_until": 0},
                }

            # Reset counters if needed
            today = date.today().isoformat()
            hour = datetime.now().hour
            if state["global_counts"]["last_reset_day"] != today:
                state["global_counts"]["daily"] = 0
                state["global_counts"]["last_reset_day"] = today
                for pc in state["provider_counts"].values():
                    pc["daily"] = 0

            if state["global_counts"]["last_reset_hour"] != hour:
                state["global_counts"]["hourly"] = 0
                state["global_counts"]["last_reset_hour"] = hour
                for pc in state["provider_counts"].values():
                    pc["hourly"] = 0

            return state
    except Exception:
        return {
            "provider_counts": {},
            "global_counts": {
                "daily": 0,
                "hourly": 0,
                "last_reset_day": "",
                "last_reset_hour": -1,
            },
            "failure_tracker": {"consecutive": 0, "cooldown_until": 0},
        }


def _save_state(state):
    try:
        with FileLock(LOCK_FILE, timeout=5):
            with open(STATE_FILE, "w") as f:
                json.dump(state, f)
    except Exception:
        pass


def is_business_hours() -> bool:
    hour = datetime.now().hour
    return BUSINESS_HOURS_START <= hour < BUSINESS_HOURS_END


def is_weekend() -> bool:
    return datetime.now().weekday() >= 5


def get_weekend_max() -> int:
    return max(10, int(GLOBAL_DAILY_CAP * WEEKEND_MULTIPLIER))


def can_send_global() -> tuple[bool, str]:
    state = _get_state()

    if state["failure_tracker"]["cooldown_until"] > time.time():
        remaining = int(state["failure_tracker"]["cooldown_until"] - time.time())
        return (
            False,
            f"Cooldown active: {remaining}s remaining after {MAX_FAILURES_BEFORE_COOLDOWN} failures",
        )

    if is_weekend():
        effective_daily = get_weekend_max()
        if state["global_counts"]["daily"] >= effective_daily:
            return False, f"Weekend daily cap ({effective_daily}) reached"
    else:
        if state["global_counts"]["daily"] >= GLOBAL_DAILY_CAP:
            return False, f"Global daily cap ({GLOBAL_DAILY_CAP}) reached"

    if state["global_counts"]["hourly"] >= GLOBAL_HOURLY_CAP:
        return False, f"Global hourly cap ({GLOBAL_HOURLY_CAP}) reached"

    return True, "ok"


def record_failure():
    state = _get_state()
    state["failure_tracker"]["consecutive"] += 1
    if state["failure_tracker"]["consecutive"] >= MAX_FAILURES_BEFORE_COOLDOWN:
        state["failure_tracker"]["cooldown_until"] = time.time() + (
            FAILURE_COOLDOWN_MINUTES * 60
        )
        logger.warning(
            f"BanShield: {MAX_FAILURES_BEFORE_COOLDOWN} consecutive failures — cooldown for {FAILURE_COOLDOWN_MINUTES}min"
        )
    _save_state(state)


def record_success():
    state = _get_state()
    state["failure_tracker"]["consecutive"] = 0
    state["failure_tracker"]["cooldown_until"] = 0
    _save_state(state)


def smart_delay(provider: str) -> float:
    state = _get_state()

    delays = {
        "gmail": (20, 60),
        "brevo": (10, 30),
        "sendgrid": (8, 25),
        "default": (15, 45),
    }
    min_s, max_s = delays.get(provider, delays["default"])

    if is_weekend():
        min_s *= 1.5
        max_s *= 1.5

    if not is_business_hours():
        min_s *= 1.3
        max_s *= 1.3

    usage_ratio = (
        state["global_counts"]["daily"] / GLOBAL_DAILY_CAP if GLOBAL_DAILY_CAP else 0
    )
    slowdown = 1.0 + (usage_ratio * 2.0)
    min_s *= slowdown
    max_s *= slowdown

    delay = random.uniform(min_s, max_s)
    time.sleep(delay)

    state["global_counts"]["daily"] += 1
    state["global_counts"]["hourly"] += 1
    _save_state(state)

    return delay


def can_send_provider(provider_type: str) -> tuple:
    limits = PROVIDER_SAFE_LIMITS.get(provider_type, PROVIDER_SAFE_LIMITS["default"])
    state = _get_state()

    if provider_type not in state["provider_counts"]:
        state["provider_counts"][provider_type] = {"daily": 0, "hourly": 0}

    pc = state["provider_counts"][provider_type]

    if pc["daily"] >= limits["daily"]:
        return False, f"{provider_type} daily cap ({limits['daily']}) reached"
    if pc["hourly"] >= limits["hourly"]:
        return False, f"{provider_type} hourly cap ({limits['hourly']}) reached"

    return True, "ok"


def record_provider_send(provider_type: str):
    state = _get_state()
    if provider_type not in state["provider_counts"]:
        state["provider_counts"][provider_type] = {"daily": 0, "hourly": 0}

    state["provider_counts"][provider_type]["daily"] += 1
    state["provider_counts"][provider_type]["hourly"] += 1
    _save_state(state)


def get_multi_provider_cap() -> int:
    state = _get_state()
    active = (
        len([k for k, v in state["provider_counts"].items() if v.get("daily", 0) > 0])
        or 1
    )
    tier = 1
    for t in sorted(MULTI_PROVIDER_CAPS.keys()):
        if active >= t:
            tier = t
    return MULTI_PROVIDER_CAPS.get(tier, 500)


def get_provider_delay(provider_type: str) -> float:
    limits = PROVIDER_SAFE_LIMITS.get(provider_type, PROVIDER_SAFE_LIMITS["default"])
    min_s, max_s = limits["delay"]
    delay = random.uniform(min_s, max_s)
    time.sleep(delay)
    return delay


def get_all_provider_stats() -> dict:
    state = _get_state()
    stats = {}
    for pt, limits in PROVIDER_SAFE_LIMITS.items():
        if pt == "default":
            continue
        pc = state["provider_counts"].get(pt, {"daily": 0, "hourly": 0})
        stats[pt] = {
            "daily_used": pc.get("daily", 0),
            "daily_cap": limits["daily"],
            "hourly_used": pc.get("hourly", 0),
            "hourly_cap": limits["hourly"],
            "remaining": limits["daily"] - pc.get("daily", 0),
            "available": pc.get("daily", 0) < limits["daily"],
        }
    return stats


def get_safe_send_window() -> dict:
    state = _get_state()
    return {
        "business_hours": is_business_hours(),
        "is_weekend": is_weekend(),
        "global_hourly_used": state["global_counts"]["hourly"],
        "global_hourly_cap": GLOBAL_HOURLY_CAP,
        "global_daily_used": state["global_counts"]["daily"],
        "global_daily_cap": GLOBAL_DAILY_CAP if not is_weekend() else get_weekend_max(),
        "brevo_daily_used": _count_today("brevo"),
        "brevo_daily_cap": BREVO_DAILY_CAP,
        "gmail_daily_cap_per": GMAIL_DAILY_CAP,
        "in_cooldown": state["failure_tracker"]["cooldown_until"] > time.time(),
        "consecutive_failures": state["failure_tracker"]["consecutive"],
        "risk_level": "low"
        if not is_weekend()
        and is_business_hours()
        and state["global_counts"]["daily"] < GLOBAL_DAILY_CAP * 0.5
        else "moderate",
    }
