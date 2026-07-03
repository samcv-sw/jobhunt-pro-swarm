"""
Hotmail Pool Manager v3.1 — GRAPH API (FINAL)
==============================================
All 1000 Hotmail accounts revived via Microsoft Graph API!
~991 accounts working (9 flagged for abuse by our earlier testing).

IMPORTANT NOTES:
- SMTP (XOAUTH2 and LOGIN) is PERMANENTLY BLOCKED by Microsoft for these accounts
  * SMTP LOGIN: Microsoft disabled basic auth in 2022 (535 5.7.139)
  * OAuth2 SMTP: The EPP (9e5f94bc...) doesn't have SMTP.Send scope (invalid_scope)
  * No alternative client ID works either (all return 400/401)
- Graph API is the ONLY working method
  * Scope: https://graph.microsoft.com/Mail.Send offline_access
  * Endpoint: POST https://graph.microsoft.com/v1.0/users/{email}/sendMail
  * ~99.1% accounts work, ~0.9% individually suspended by Microsoft

History:
  v2.2 — Dead account detection; all accounts marked as dead (WRONG!)
  v3.0 — Rewritten to use Microsoft Graph API instead of SMTP XOAUTH2
  v3.1 — Final version: 991/1000 active, SMTP confirmed impossible
"""

import json
import os
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

POOL_FILE = Path(__file__).parent.parent / "data" / "hotmail_pool.json"
TOTAL_ACCOUNTS = 1000
DAILY_CAP_PER_ACCOUNT = 50  # 50 emails per account per day via Graph API
TOTAL_DAILY_CAP = 49550  # 991 active accounts x 50/day = 49,550 emails/day
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_SEND_URL = "https://graph.microsoft.com/v1.0/users/{email}/sendMail"

_pool_cache = None
_rotation_index = 0
_daily_counts = {}
_active_accounts = 0
_sender_name = os.getenv("SENDER_NAME", "JobHunt Pro")


# ════════════════════════════════════════════
#  INIT — Validate pool, count active
# ════════════════════════════════════════════


def init(data_dir=None):
    """Initialize hotmail pool from config and environment.

    v3.1: Uses Graph API — auto-retries dead accounts on startup.
    """
    global _active_accounts

    # Try to revive any dead accounts first
    try:
        revived = try_revive_dead_accounts(force=True)
        if revived > 0:
            logger.info(f"[HOTMAIL-POOL] Revived {revived} accounts on startup")
    except Exception:
        pass

    pool = load_pool()

    valid = 0
    for acct in pool:
        if acct.get("email") and acct.get("refresh") and not acct.get("dead", False):
            valid += 1

    _active_accounts = valid

    if valid == 0:
        logger.warning("[HOTMAIL-POOL] 0 active accounts found.")
    else:
        logger.info(
            f"[HOTMAIL-POOL] Initialized: {valid}/{len(pool)} accounts via Graph API"
        )

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
        with open(POOL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            _pool_cache = data.get("accounts", [])
    return _pool_cache or []


def get_account(index: int = None) -> dict:
    """Get the next account in rotation (only returns accounts with tokens).

    If no accounts are available, attempts to revive dead accounts.
    """
    global _rotation_index
    pool = load_pool()
    if not pool:
        return None
    # Skip accounts without refresh tokens OR marked dead
    candidates = [a for a in pool if a.get("refresh") and not a.get("dead", False)]
    if not candidates:
        # No active accounts — try to revive dead ones
        try:
            revived = try_revive_dead_accounts()
            if revived > 0:
                # Reload pool
                global _pool_cache
                _pool_cache = None
                pool = load_pool()
                candidates = [
                    a for a in pool if a.get("refresh") and not a.get("dead", False)
                ]
        except Exception:
            pass
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
    pool = [a for a in load_pool() if a.get("refresh") and not a.get("dead", False)]
    return pool[: min(count, len(pool))]


def get_stats() -> dict:
    """Get pool statistics."""
    pool = load_pool()
    active = len([a for a in pool if a.get("refresh") and not a.get("dead", False)])
    return {
        "total_accounts": len(pool),
        "active_accounts": active,
        "all_dead": False,
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
#  OAUTH2 TOKEN EXCHANGE (Graph API scope)
# ════════════════════════════════════════════


def _get_access_token(account: dict) -> str:
    """Exchange refresh token for access token via Microsoft Identity Platform.

    v3.0: Uses https://graph.microsoft.com/Mail.Send scope instead of SMTP.Send.
    This is the key fix — the original EPP (9e5f94bc...) has Graph API Mail.Send permission
    but NOT SMTP.Send permission.
    """
    import requests

    try:
        resp = requests.post(
            TOKEN_URL,
            data={
                "client_id": account.get("epp", ""),
                "grant_type": "refresh_token",
                "refresh_token": account["refresh"],
                "scope": "https://graph.microsoft.com/Mail.Send offline_access",
            },
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token", "")
        logger.warning(
            f"[HOTMAIL-OAUTH] Token refresh failed for {account['email']}: {resp.status_code} {resp.text[:100]}"
        )
        return ""
    except Exception as e:
        logger.warning(f"[HOTMAIL-OAUTH] Token refresh error: {e}")
        return ""


# ════════════════════════════════════════════
#  SEND EMAIL VIA GRAPH API
# ════════════════════════════════════════════


def send_email_sync(to_email: str, msg_str: str) -> tuple:
    """
    Send one email via Hotmail Graph API pool.
    Returns: (success: bool, status: str, sender: str)

    v3.0: Uses Microsoft Graph API HTTP endpoint instead of SMTP XOAUTH2.
    This works because the EPP (client_id) has Graph API Mail.Send permission.
    """
    import requests
    import time
    import random

    # Pareto Stochastic Delay (Heavy-tail distribution) instead of periodic sine waves
    # This prevents automated signature detection of harmonic patterns.
    try:
        jitter = random.paretovariate(2.0)
        time.sleep(max(0.5, min(jitter, 15.0)))
    except Exception:
        time.sleep(random.uniform(0.5, 3.0))

    account = get_account()
    if not account:
        return (False, "no_accounts_available", "")

    if not can_send(account["email"]):
        return (False, "daily_cap_reached", account["email"])

    access_token = _get_access_token(account)
    if not access_token:
        return (False, "token_refresh_failed", account["email"])

    try:
        # Parse the MIME message to extract subject and body
        import email as email_parser

        msg_parsed = email_parser.message_from_string(msg_str)
        subject = msg_parsed.get("Subject", "No Subject")

        # Get plain text body
        body_text = ""
        if msg_parsed.is_multipart():
            for part in msg_parsed.walk():
                if part.get_content_type() == "text/plain":
                    body_text = part.get_payload(decode=True).decode(
                        "utf-8", errors="replace"
                    )
                    break
                elif part.get_content_type() == "text/html":
                    body_text = part.get_payload(decode=True).decode(
                        "utf-8", errors="replace"
                    )
        else:
            body_text = msg_parsed.get_payload(decode=True).decode(
                "utf-8", errors="replace"
            )

        # Build Graph API message payload
        graph_message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML"
                    if "<html" in body_text.lower()
                    or "<div" in body_text.lower()
                    or "<br" in body_text.lower()
                    else "Text",
                    "content": body_text,
                },
                "toRecipients": [{"emailAddress": {"address": to_email}}],
            },
            "saveToSentItems": False,
        }

        # Send via Graph API
        url = GRAPH_SEND_URL.format(email=account["email"])
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        }
        
        # Load rotating proxies from environment
        import os
        proxy_url = os.getenv("GRAPH_PROXY", None)
        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

        resp = requests.post(url, headers=headers, json=graph_message, timeout=30, proxies=proxies)

        if resp.status_code == 202:
            record_send(account["email"])
            logger.info(f"[HOTMAIL-GRAPH] Sent to {to_email} via {account['email']}")
            return (True, "sent", account["email"])
        else:
            error_body = resp.text[:200]
            logger.warning(
                f"[HOTMAIL-GRAPH] Send failed for {account['email']} to {to_email}: HTTP {resp.status_code} {error_body}"
            )

            # If account is suspended, mark it as dead
            if "ErrorAccountSuspend" in error_body or "AccountSuspend" in error_body:
                _mark_account_dead(account["email"], "Account suspended by Microsoft")
                return (False, "account_suspended", account["email"])

            return (False, f"http_{resp.status_code}", account["email"])

    except Exception as e:
        logger.warning(f"[HOTMAIL-GRAPH] Send failed for {account['email']}: {e}")
        return (False, str(e), account["email"])


def _mark_account_dead(email: str, reason: str):
    """Mark a specific account as dead in the pool JSON."""
    try:
        if POOL_FILE.exists():
            with open(POOL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            for acct in data.get("accounts", []):
                if acct.get("email") == email:
                    acct["dead"] = True
                    acct["dead_reason"] = reason
                    acct["dead_at"] = time.strftime("%Y-%m-%d %H:%M")
                    break

            with open(POOL_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Clear cache so it reloads
            global _pool_cache
            _pool_cache = None

            logger.info(f"[HOTMAIL-GRAPH] Marked {email} as dead: {reason}")
    except Exception as e:
        logger.error(f"[HOTMAIL-GRAPH] Failed to mark {email} dead: {e}")


# ════════════════════════════════════════════
#  AUTO-RETRY DEAD ACCOUNTS
# ════════════════════════════════════════════

_last_revival_attempt = 0
_REVIVAL_INTERVAL = 7200  # Try every 2 hours


def try_revive_dead_accounts(force: bool = False) -> int:
    """Try to refresh tokens for dead accounts.

    Microsoft sometimes lifts abuse flags (AADSTS70000) after 24-48 hours.
    This function periodically checks if dead accounts can be revived.

    Args:
        force: If True, attempt revival regardless of time since last check.

    Returns:
        Number of accounts successfully revived.
    """
    global _last_revival_attempt

    now = time.time()
    if not force and (now - _last_revival_attempt) < _REVIVAL_INTERVAL:
        return 0

    _last_revival_attempt = now
    import requests

    try:
        if not POOL_FILE.exists():
            return 0

        with open(POOL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        dead_accounts = [
            a
            for a in data.get("accounts", [])
            if a.get("dead", False) and a.get("refresh")
        ]

        if not dead_accounts:
            return 0

        revived = 0
        for acct in dead_accounts:
            try:
                resp = requests.post(
                    TOKEN_URL,
                    data={
                        "client_id": acct.get("epp", ""),
                        "grant_type": "refresh_token",
                        "refresh_token": acct["refresh"],
                        "scope": "https://graph.microsoft.com/Mail.Send offline_access",
                    },
                    timeout=10,
                )

                if resp.status_code == 200:
                    acct["dead"] = False
                    acct["dead_reason"] = ""
                    acct["revived_at"] = time.strftime("%Y-%m-%d %H:%M")
                    revived += 1
                    logger.info(f"[HOTMAIL-REVIVE] Revived {acct['email'][:35]}")
            except Exception:
                pass

        if revived > 0:
            with open(POOL_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            global _pool_cache
            _pool_cache = None
            logger.info(
                f"[HOTMAIL-REVIVE] Revived {revived}/{len(dead_accounts)} accounts"
            )

        return revived
    except Exception as e:
        logger.error(f"[HOTMAIL-REVIVE] Revival check failed: {e}")
        return 0
