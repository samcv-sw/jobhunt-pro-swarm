"""
Telegram Alerts Service — Automatic Campaign & Email Notifications
Hooks into campaign_runner, email_engine, and tracking for real-time alerts.
Uses simple requests HTTP calls (no python-telegram-bot dependency).
"""

import asyncio
import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def _is_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def _send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to Telegram via HTTP. Returns True on success."""
    if not _is_configured():
        return False
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": parse_mode,
        }
        # Truncate to Telegram's 4096 char limit
        if len(text) > 4000:
            payload["text"] = text[:3950] + "\n\n...(truncated)"

        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return True
        logger.warning(f"Telegram send failed: HTTP {r.status_code} — {r.text[:200]}")
        return False
    except Exception as e:
        logger.warning(f"Telegram send error: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# CAMPAIGN ALERTS
# ═══════════════════════════════════════════════════════════════


def alert_campaign_started(
    campaign_id: str,
    total_companies: int,
    job_title: str = "",
    location: str = "",
    user_name: str = "",
) -> bool:
    """Alert when a campaign starts running."""
    cid_short = campaign_id[:12] if len(campaign_id) > 12 else campaign_id
    msg = (
        f"🚀 <b>Campaign Started!</b>\n\n"
        f"<b>ID:</b> <code>{cid_short}</code>\n"
        f"<b>Target:</b> {total_companies} companies\n"
    )
    if job_title:
        msg += f"<b>Role:</b> {job_title}\n"
    if location:
        msg += f"<b>Location:</b> {location}\n"
    if user_name:
        msg += f"<b>User:</b> {user_name}\n"
    msg += f"\n<i>🕐 Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n"
    msg += "<i>🔥 Swarm agents activating now...</i>"

    return _send_message(msg)


def alert_campaign_completed(
    campaign_id: str,
    sent_count: int,
    failed_count: int = 0,
    total_companies: int = 0,
    campaign_duration_sec: float = 0,
) -> bool:
    """Alert when a campaign finishes."""
    cid_short = campaign_id[:12] if len(campaign_id) > 12 else campaign_id
    success_rate = (
        round((sent_count / max(total_companies, 1)) * 100, 1)
        if total_companies
        else 100
    )

    emoji = "✅" if failed_count == 0 else "⚠️"
    msg = (
        f"{emoji} <b>Campaign Completed!</b>\n\n"
        f"<b>ID:</b> <code>{cid_short}</code>\n"
        f"<b>Sent:</b> {sent_count} / {total_companies}\n"
        f"<b>Success Rate:</b> {success_rate}%\n"
    )
    if failed_count > 0:
        msg += f"<b>Failed:</b> {failed_count}\n"
    if campaign_duration_sec > 0:
        mins = int(campaign_duration_sec // 60)
        secs = int(campaign_duration_sec % 60)
        msg += f"<b>Duration:</b> {mins}m {secs}s\n"

    msg += f"\n<i>🕐 Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"

    if sent_count >= 100:
        msg += f"\n\n🎉 <b>{sent_count} applications sent! You're crushing it!</b>"

    return _send_message(msg)


def alert_campaign_failed(campaign_id: str, error: str = "") -> bool:
    """Alert when a campaign fails."""
    cid_short = campaign_id[:12] if len(campaign_id) > 12 else campaign_id
    msg = f"❌ <b>Campaign Failed!</b>\n\n<b>ID:</b> <code>{cid_short}</code>\n"
    if error:
        msg += f"<b>Error:</b> {error[:200]}\n"
    msg += "\n<i>Use /retry to re-run this campaign.</i>"

    return _send_message(msg)


# ═══════════════════════════════════════════════════════════════
# EMAIL ALERTS
# ═══════════════════════════════════════════════════════════════


def alert_email_sent(
    company: str,
    job_title: str,
    email_addr: str,
    campaign_id: str = "",
    sent_count: int = 0,
    total: int = 0,
) -> bool:
    """Alert when an individual email is sent. Throttled — only fires every ~10 sends."""
    if not _is_configured():
        return False

    # Only alert on milestone sends (every 10th, or first/last)
    if sent_count > 0 and sent_count % 10 != 0 and sent_count != 1:
        return False

    cid_short = campaign_id[:8] if len(campaign_id) > 8 else campaign_id
    progress = f" ({sent_count}/{total})" if total > 0 else ""

    msg = (
        f"📧 <b>Email Sent!</b>{progress}\n\n"
        f"<b>To:</b> {company}\n"
        f"<b>Position:</b> {job_title}\n"
        f"<b>Address:</b> {email_addr}\n"
    )
    if campaign_id:
        msg += f"<b>Campaign:</b> <code>{cid_short}</code>\n"

    return _send_message(msg)


def alert_email_opened(
    company: str, job_title: str, opened_at: str = "", campaign_id: str = ""
) -> bool:
    """Alert when a recipient opens the email (tracking pixel)."""
    cid_short = campaign_id[:8] if len(campaign_id) > 8 else campaign_id
    msg = (
        f"👁️ <b>Email Opened!</b>\n\n"
        f"<b>Company:</b> {company}\n"
        f"<b>Position:</b> {job_title}\n"
        f"<b>Opened:</b> {opened_at or datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    if campaign_id:
        msg += f"<b>Campaign:</b> <code>{cid_short}</code>\n"
    msg += "\n<i>💡 The hiring manager just saw your application!</i>"

    return _send_message(msg)


def alert_response_received(
    company: str, response_text: str = "", campaign_id: str = ""
) -> bool:
    """Alert when a response is received."""
    cid_short = campaign_id[:8] if len(campaign_id) > 8 else campaign_id
    msg = f"📬 <b>Response Received!</b>\n\n<b>From:</b> {company}\n"
    if response_text:
        snippet = response_text[:300]
        if len(response_text) > 300:
            snippet += "..."
        msg += f"<b>Message:</b>\n<i>{snippet}</i>\n"
    if campaign_id:
        msg += f"<b>Campaign:</b> <code>{cid_short}</code>\n"

    return _send_message(msg)


# ═══════════════════════════════════════════════════════════════
# SYSTEM ALERTS
# ═══════════════════════════════════════════════════════════════


def alert_rate_limit_warning(sent_last_hour: int, provider: str = "Gmail") -> bool:
    """Warn about approaching rate limits."""
    if sent_last_hour < 60:
        return False

    severity = "⚠️ Warning" if sent_last_hour < 80 else "🚨 CRITICAL"
    msg = (
        f"{severity} — <b>Rate Limit Alert!</b>\n\n"
        f"<b>{sent_last_hour}</b> emails sent in the last hour via {provider}\n"
        f"<b>Limit:</b> 500/day (free), 2000/day (Workspace)\n\n"
        "<i>Consider spreading out sends.</i>"
    )
    return _send_message(msg)


def alert_daily_report(
    sent_today: int, opened: int = 0, responded: int = 0, campaigns_active: int = 0
) -> bool:
    """Send a daily summary report."""
    if not _is_configured():
        return False

    today_str = datetime.now().strftime("%Y-%m-%d")
    open_rate = round((opened / max(sent_today, 1)) * 100, 1)
    response_rate = round((responded / max(sent_today, 1)) * 100, 1)

    msg = (
        f"📊 <b>Daily Report — {today_str}</b>\n\n"
        f"📧 <b>Emails Sent:</b> {sent_today}\n"
        f"👁️ <b>Opened:</b> {opened} ({open_rate}%)\n"
        f"📬 <b>Responses:</b> {responded} ({response_rate}%)\n"
        f"🚀 <b>Active Campaigns:</b> {campaigns_active}\n\n"
        "<i>Keep going! 📈</i>"
    )
    return _send_message(msg)


# ═══════════════════════════════════════════════════════════════
# ASYNC WRAPPERS (for use in async context)
# ═══════════════════════════════════════════════════════════════


async def async_alert_campaign_started(
    campaign_id: str,
    total_companies: int,
    job_title: str = "",
    location: str = "",
    user_name: str = "",
) -> bool:
    """Async wrapper for campaign started alert."""
    return await asyncio.to_thread(
        alert_campaign_started,
        campaign_id,
        total_companies,
        job_title,
        location,
        user_name,
    )


async def async_alert_campaign_completed(
    campaign_id: str,
    sent_count: int,
    failed_count: int = 0,
    total_companies: int = 0,
    duration_sec: float = 0,
) -> bool:
    """Async wrapper for campaign completed alert."""
    return await asyncio.to_thread(
        alert_campaign_completed,
        campaign_id,
        sent_count,
        failed_count,
        total_companies,
        duration_sec,
    )


async def async_alert_campaign_failed(campaign_id: str, error: str = "") -> bool:
    """Async wrapper for campaign failed alert."""
    return await asyncio.to_thread(alert_campaign_failed, campaign_id, error)


async def async_alert_email_sent(
    company: str,
    job_title: str,
    email_addr: str,
    campaign_id: str = "",
    sent_count: int = 0,
    total: int = 0,
) -> bool:
    """Async wrapper for email sent alert."""
    return await asyncio.to_thread(
        alert_email_sent, company, job_title, email_addr, campaign_id, sent_count, total
    )
