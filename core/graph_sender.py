"""
JobHunt Pro - Microsoft Graph API Email Sender
Sends emails via Microsoft Graph API using OAuth refresh tokens.
Works on PythonAnywhere free tier (HTTPS, no SMTP needed).

Capacity: 500 accounts × 50/account/day × 30 = 750,000 emails/month
Cost: $0 (Microsoft Graph API is free for email sending)

Flow:
  1. Refresh OAuth token via login.microsoftonline.com
  2. Send email via graph.microsoft.com/v1.0/me/sendMail
  3. Rotate through 500 Hotmail accounts
"""

import json
import logging
import random
import time
import requests
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Config ──
CLIENT_ID = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPE = "https://graph.microsoft.com/.default offline_access"
DAILY_CAP_PER_ACCOUNT = 50
MAX_RETRIES = 2
SEND_DELAY_MIN = 1.5
SEND_DELAY_MAX = 4.0

# ── State ──
_data_dir = None
_accounts = []
_daily_counts = {}
_token_cache = {}
_rotation = 0

import sys

_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))
try:
    import config

    SITE_URL = getattr(config, "SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip(
        "/"
    )
except Exception:
    import os

    SITE_URL = os.getenv("SITE_URL", "https://jhfguf.pythonanywhere.com").rstrip("/")


def init(data_dir: str = None):
    global _data_dir, _accounts
    _data_dir = Path(data_dir) if data_dir else Path(__file__).parent.parent / "data"
    _load_accounts()
    _load_daily()


def _load_accounts():
    global _accounts
    pool_file = _data_dir / "hotmail_pool.json"
    if pool_file.exists():
        data = json.load(open(pool_file, "r", encoding="utf-8"))
        _accounts = data.get("accounts", [])
        logger.info(f"Loaded {len(_accounts)} Hotmail accounts")
    else:
        logger.warning(f"No hotmail_pool.json found at {pool_file}")


def _load_daily():
    global _daily_counts
    today = date.today().isoformat()
    df = _data_dir / f"graph_daily_{today}.json"
    if df.exists():
        _daily_counts = json.load(open(df, "r", encoding="utf-8"))
    else:
        _daily_counts = {}


def _save_daily():
    today = date.today().isoformat()
    df = _data_dir / f"graph_daily_{today}.json"
    json.dump(_daily_counts, open(df, "w", encoding="utf-8"))
    # Save stats
    sf = _data_dir / "graph_stats.json"
    stats = {
        "last_updated": datetime.utcnow().isoformat(),
        "total_accounts": len(_accounts),
        "daily_cap_per_account": DAILY_CAP_PER_ACCOUNT,
        "total_daily_cap": len(_accounts) * DAILY_CAP_PER_ACCOUNT,
    }
    json.dump(stats, open(sf, "w", encoding="utf-8"))


def _refresh_token(account: dict) -> Optional[str]:
    """Exchange refresh token for access token."""
    refresh = account.get("refresh", "")
    email = account.get("email", "")

    if not refresh:
        return None

    # Check cache
    cache_key = email
    if cache_key in _token_cache:
        cached = _token_cache[cache_key]
        if cached["expires"] > time.time() + 60:
            return cached["token"]

    try:
        r = requests.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "refresh_token": refresh,
                "grant_type": "refresh_token",
                "scope": SCOPE,
            },
            timeout=15,
        )

        if r.status_code == 200:
            data = r.json()
            access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            _token_cache[cache_key] = {
                "token": access_token,
                "expires": time.time() + expires_in,
            }
            return access_token
        else:
            logger.warning(f"Token refresh failed for {email}: {r.status_code}")
            return None
    except Exception as e:
        logger.error(f"Token refresh error for {email}: {e}")
        return None


def _send_one(
    account: dict, access_token: str, recipient: dict, subject: str, body_html: str
) -> bool:
    """Send one email via Microsoft Graph API."""
    email_addr = account.get("email", "")

    msg = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_html,
            },
            "toRecipients": [{"emailAddress": {"address": recipient.get("email", "")}}],
            "from": {"emailAddress": {"address": email_addr}},
        },
        "saveToSentItems": "false",
    }

    for attempt in range(MAX_RETRIES + 1):
        try:
            r = requests.post(
                f"{GRAPH_BASE}/me/sendMail",
                json=msg,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                timeout=20,
            )
            if r.status_code in (200, 202):
                return True
            if r.status_code == 401:
                # Token expired, get fresh one
                if attempt < MAX_RETRIES:
                    access_token = _refresh_token(account)
                    if access_token:
                        continue
            if r.status_code == 429:
                # Rate limited
                time.sleep(random.uniform(5, 15))
                continue
            logger.warning(f"Send failed [{r.status_code}]: {r.text[:200]}")
            return False
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue
            logger.error(f"Send error: {e}")
            return False

    return False


def send_bulk(
    recipients: list,
    subject: str = None,
    body_html: str = None,
    campaign_name: str = "graph_blast",
    max_sends: int = None,
) -> dict:
    """
    Send bulk emails via Microsoft Graph API using Hotmail pool.

    Args:
        recipients: list of {'email': str, 'name': str} dicts
        subject: email subject (if None, uses AI-generated subject)
        body_html: HTML body (if None, uses AI-generated template)
        campaign_name: label for tracking
        max_sends: cap on number to send

    Returns:
        {'sent': int, 'failed': int, 'tokens_expired': int, 'rate_limited': int}
    """
    global _rotation

    if not _accounts:
        return {"sent": 0, "failed": 0, "error": "No Hotmail accounts loaded"}

    date.today().isoformat()
    sent = 0
    failed = 0
    tokens_expired = 0
    rate_limited = 0

    total_cap = min(
        len(_accounts) * DAILY_CAP_PER_ACCOUNT,
        len(recipients) if max_sends is None else max_sends,
    )

    logger.info(
        f"Graph blast: {campaign_name} | max={total_cap} | accounts={len(_accounts)}"
    )

    for i, recipient in enumerate(recipients[:total_cap]):
        # Pick account via round-robin
        account = _accounts[_rotation % len(_accounts)]
        _rotation += 1

        email_key = account["email"]
        if _daily_counts.get(email_key, 0) >= DAILY_CAP_PER_ACCOUNT:
            # Skip this account, try next
            rate_limited += 1
            continue

        # Get access token
        access_token = _refresh_token(account)
        if not access_token:
            tokens_expired += 1
            failed += 1
            continue

        # Use AI subject/body or provided ones
        if not subject:
            subject = _get_ai_subject(recipient)
        if not body_html:
            body_html = _get_ai_template(recipient, campaign_name)

        # Send
        if _send_one(account, access_token, recipient, subject, body_html):
            sent += 1
            _daily_counts[email_key] = _daily_counts.get(email_key, 0) + 1
        else:
            failed += 1

        # Anti-detection delay
        time.sleep(random.uniform(SEND_DELAY_MIN, SEND_DELAY_MAX))

        # Save state every 50 sends
        if (sent + failed) % 50 == 0:
            _save_daily()
            logger.info(
                f"Progress: {sent} sent, {failed} failed, "
                f"{tokens_expired} expired tokens"
            )

        # Progress log
        if (i + 1) % 500 == 0:
            logger.info(f"Blast milestone: {i + 1}/{total_cap} processed")

    _save_daily()
    return {
        "sent": sent,
        "failed": failed,
        "tokens_expired": tokens_expired,
        "rate_limited": rate_limited,
        "accounts_used": len(set(k for k, v in _daily_counts.items() if v > 0)),
    }


def get_status() -> dict:
    """Get current blaster status."""
    date.today().isoformat()
    total = len(_accounts) * DAILY_CAP_PER_ACCOUNT
    sent_today = sum(_daily_counts.values())
    return {
        "accounts_total": len(_accounts),
        "daily_cap_per_account": DAILY_CAP_PER_ACCOUNT,
        "daily_cap_total": total,
        "sent_today": sent_today,
        "remaining_today": total - sent_today,
        "accounts_used_today": len([k for k, v in _daily_counts.items() if v > 0]),
        "token_cache_size": len(_token_cache),
    }


def test_single(account_index: int, to_email: str) -> dict:
    """Send a test email from one account."""
    if not _accounts:
        return {"ok": False, "error": "No accounts loaded"}

    account = _accounts[account_index % len(_accounts)]
    access_token = _refresh_token(account)

    if not access_token:
        return {
            "ok": False,
            "error": "Token refresh failed",
            "account": account["email"],
        }

    ok = _send_one(
        account,
        access_token,
        {"email": to_email, "name": "Test"},
        "JobHunt Pro — Test Email 🚀",
        "<h2>Test email from JobHunt Pro</h2><p>This is a test.</p>",
    )

    return {
        "ok": ok,
        "account": account["email"],
        "to": to_email,
    }


def _get_ai_subject(recipient: dict) -> str:
    """Get an AI-generated subject line."""
    subjects = [
        "I applied to 1,000 jobs in 10 minutes with AI 🤖",
        "Your job search just got automated 🚀",
        "Stop applying to jobs manually (this is better)",
        "The secret tech workers are using to get hired 💼",
        "200 AI agents applied to jobs for me. Here's what happened.",
        "Job hunting? This tool does it while you sleep 😴",
        "How I automated my entire job search (and got 3 offers)",
        "Want a new job? AI can now apply FOR you ⚡",
        "You're 1 click away from automated job applications",
        "The $2 tool that applies to 1,000 jobs for you",
    ]
    recipient.get("name", "there")
    subj = random.choice(subjects)
    return subj


def _get_ai_template(recipient: dict, campaign: str) -> str:
    """Generate HTML email body."""
    name = recipient.get("name", "there")
    name_display = name.split("@")[0] if "@" in name else name

    return f"""<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;background:#0a0a1a;color:#e0e0e0;max-width:600px;margin:0 auto;padding:20px">
<div style="background:#111;border:1px solid #00f0ff33;border-radius:12px;padding:30px;margin:20px">
  <h1 style="color:#00f0ff;font-size:24px;margin:0 0 8px">⚡ Your Job Search, Automated</h1>
  <p style="color:#888;font-size:14px;margin:0 0 20px">200+ AI agents working 24/7 to get you hired</p>
  
  <div style="background:#fff5;border-radius:8px;padding:15px;margin:15px 0">
    <p style="color:#e0e0e0;font-size:15px;margin:0">Hey {name_display},</p>
    <p style="color:#aaa;font-size:14px;margin:10px 0 0">Tired of filling out the same job applications over and over? JobHunt Pro's AI applies to <strong>1,000+ jobs</strong> for you — automatically. Cover letters, form filling, everything.</p>
  </div>
  
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:15px 0">
    <div style="background:#00f0ff11;padding:12px;border-radius:6px;text-align:center">
      <div style="font-size:22px;color:#00f0ff;font-weight:700">200+</div>
      <div style="font-size:11px;color:#888">AI Agents</div>
    </div>
    <div style="background:#00f0ff11;padding:12px;border-radius:6px;text-align:center">
      <div style="font-size:22px;color:#00f0ff;font-weight:700">40K</div>
      <div style="font-size:11px;color:#888">Apps/Day</div>
    </div>
    <div style="background:#00f0ff11;padding:12px;border-radius:6px;text-align:center">
      <div style="font-size:22px;color:#00f0ff;font-weight:700">50+</div>
      <div style="font-size:11px;color:#888">Countries</div>
    </div>
    <div style="background:#00f0ff11;padding:12px;border-radius:6px;text-align:center">
      <div style="font-size:22px;color:#00f0ff;font-weight:700">$2</div>
      <div style="font-size:11px;color:#888">Starting</div>
    </div>
  </div>
  
  <div style="text-align:center;margin:20px 0">
    <a href="{SITE_URL}/register?ref={campaign}" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#00f0ff,#0088ff);color:#000;border-radius:25px;font-weight:700;font-size:16px;text-decoration:none;box-shadow:0 0 20px #00f0ff33">🚀 Start Auto-Applying — $2</a>
  </div>
  
  <p style="color:#555;font-size:11px;text-align:center;margin-top:20px">
    No credit card. No commitment. Just faster job applications.<br>
    <a href="{SITE_URL}/unsubscribe" style="color:#555">Unsubscribe</a> | Beirut, Lebanon
  </p>
</div>
</body></html>"""


# ── Auto-init on import ──
_init_done = False
if not _init_done:
    try:
        init()
        _init_done = True
    except Exception as e:
        logger.warning(f"Graph sender auto-init failed: {e}")
