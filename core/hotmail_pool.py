"""
Hotmail Pool Manager v2.1 — 1000 accounts + OAuth2 SMTP Sending
Generated: 2026-06-12 — FINAL: Added init(), send_email_sync(), XOAUTH2 support
"""
import json, os, random, time, logging, base64, smtplib, email
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

POOL_FILE = Path(__file__).parent.parent / "data" / "hotmail_pool.json"
TOTAL_ACCOUNTS = 1000
DAILY_CAP_PER_ACCOUNT = 50       # 50 emails per account per day
TOTAL_DAILY_CAP = TOTAL_ACCOUNTS * DAILY_CAP_PER_ACCOUNT  # 25000
SMTP_HOST = "smtp-mail.outlook.com"
SMTP_PORT = 587
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"

_pool_cache = None
_rotation_index = 0
_daily_counts = {}
_active_accounts = 0
_sender_name = os.getenv("SENDER_NAME", "JobHunt Pro")


# ════════════════════════════════════════════
#  INIT — Validate pool, count active
# ════════════════════════════════════════════

def init(data_dir=None):
    """Initialize hotmail pool from config and environment."""
    global _active_accounts
    pool = load_pool()
    valid = 0
    for acct in pool:
        if acct.get("email") and acct.get("refresh"):
            valid += 1
    _active_accounts = valid
    logger.info(f"[HOTMAIL-POOL] Initialized: {valid}/{len(pool)} accounts with OAuth2 tokens")
    return get_stats()


# ════════════════════════════════════════════
#  ACCOUNT MANAGEMENT
# ════════════════════════════════════════════

def load_pool():
    """Load Hotmail accounts from JSON pool."""
    global _pool_cache
    if _pool_cache:
        return _pool_cache
    if POOL_FILE.exists():
        with open(POOL_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _pool_cache = data.get('accounts', [])
    return _pool_cache or []


def get_account(index: int = None) -> dict:
    """Get the next account in rotation (only returns accounts with tokens)."""
    global _rotation_index
    pool = load_pool()
    if not pool:
        return None
    # Skip accounts without refresh tokens
    candidates = [a for a in pool if a.get("refresh")]
    if not candidates:
        return None
    if index is None:
        idx = _rotation_index % len(candidates)
        _rotation_index += 1
    else:
        idx = index % len(candidates)
    return candidates[idx]


def get_accounts_batch(count: int = 100) -> list:
    """Get a batch of accounts for parallel sending."""
    pool = [a for a in load_pool() if a.get("refresh")]
    return pool[:min(count, len(pool))]


def get_stats() -> dict:
    """Get pool statistics."""
    pool = load_pool()
    active = len([a for a in pool if a.get("refresh")])
    return {
        "total_accounts": len(pool),
        "active_accounts": active,
        "daily_cap_per_account": DAILY_CAP_PER_ACCOUNT,
        "max_daily_capacity": active * DAILY_CAP_PER_ACCOUNT,
        "rotation_index": _rotation_index,
        "sent_today": sum(_daily_counts.values()),
        "accounts_used_today": len(_daily_counts),
    }


def record_send(email: str):
    """Record a successful send for an account."""
    _daily_counts[email] = _daily_counts.get(email, 0) + 1


def can_send(email: str) -> bool:
    """Check if account hasn't hit its daily cap."""
    return _daily_counts.get(email, 0) < DAILY_CAP_PER_ACCOUNT


def reset_daily():
    """Reset daily counters."""
    global _daily_counts, _rotation_index
    _daily_counts = {}
    _rotation_index = 0


# ════════════════════════════════════════════
#  OAUTH2 TOKEN EXCHANGE
# ════════════════════════════════════════════

def _get_access_token(account: dict) -> str:
    """Exchange refresh token for access token via Microsoft Identity Platform."""
    import requests
    try:
        resp = requests.post(TOKEN_URL, data={
            "client_id": account.get("epp", ""),
            "grant_type": "refresh_token",
            "refresh_token": account["refresh"],
            "scope": "https://outlook.office365.com/SMTP.Send offline_access",
        }, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("access_token", "")
        logger.warning(f"[HOTMAIL-OAUTH] Token refresh failed for {account['email']}: {resp.status_code}")
        return ""
    except Exception as e:
        logger.warning(f"[HOTMAIL-OAUTH] Token refresh error: {e}")
        return ""


def _build_xoauth2_string(email: str, access_token: str) -> str:
    """Build base64-encoded XOAUTH2 auth string."""
    auth_str = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
    return base64.b64encode(auth_str.encode()).decode()


# ════════════════════════════════════════════
#  SEND EMAIL VIA XOAUTH2 SMTP
# ════════════════════════════════════════════

def send_email_sync(to_email: str, msg_str: str) -> tuple:
    """
    Send one email via Hotmail OAuth2 pool.
    Returns: (success: bool, status: str, sender: str)
    """
    account = get_account()
    if not account:
        return (False, "no_accounts_available", "")

    if not can_send(account["email"]):
        return (False, "daily_cap_reached", account["email"])

    access_token = _get_access_token(account)
    if not access_token:
        return (False, "token_refresh_failed", account["email"])

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
        server.ehlo()
        server.starttls()
        server.ehlo()

        # XOAUTH2 authentication
        xoauth2_str = _build_xoauth2_string(account["email"], access_token)
        server.docmd("AUTH", f"XOAUTH2 {xoauth2_str}")

        # Send email
        server.sendmail(account["email"], [to_email], msg_str.encode('utf-8'))
        server.quit()

        record_send(account["email"])
        logger.info(f"[HOTMAIL-OAUTH] Sent to {to_email} via {account['email']}")
        return (True, "sent", account["email"])

    except smtplib.SMTPAuthenticationError as e:
        logger.warning(f"[HOTMAIL-OAUTH] Auth failed for {account['email']}: {e}")
        return (False, "auth_failed", account["email"])
    except Exception as e:
        logger.warning(f"[HOTMAIL-OAUTH] Send failed for {account['email']}: {e}")
        return (False, str(e), account["email"])
