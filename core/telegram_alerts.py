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


import time

_TELEGRAM_COOLDOWN_UNTIL = 0


def _is_configured() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)


def _send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to Telegram via HTTP. Returns True on success."""
    global _TELEGRAM_COOLDOWN_UNTIL
    if not _is_configured() or time.time() < _TELEGRAM_COOLDOWN_UNTIL:
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
        if r.status_code == 429:
            try:
                data = r.json()
                retry_after = data.get("parameters", {}).get("retry_after", 300)
                _TELEGRAM_COOLDOWN_UNTIL = time.time() + retry_after
                logger.warning(f"Telegram API 429 rate limit hit. Cooldown active for {retry_after}s.")
            except Exception:
                _TELEGRAM_COOLDOWN_UNTIL = time.time() + 300
            return False
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


def alert_lead_captured(
    source: str = "ATS Instant Score",
    role: str = "",
    score: int = 0,
    gulf_score: int = 0,
    name: str = "",
    email: str = "",
    phone: str = "",
    notes: str = "",
) -> bool:
    """Alert when a new lead is captured via ATS score, Roast, or contact form."""
    msg = "🎯 <b>New Lead Captured!</b>\n\n"
    if source:
        msg += f"<b>Source:</b> {source}\n"
    if role:
        msg += f"<b>Target Role:</b> {role}\n"
    if score:
        msg += f"<b>ATS Score:</b> {score}%\n"
    if gulf_score:
        msg += f"<b>Gulf Fit:</b> {gulf_score}%\n"
    if name:
        msg += f"<b>Name:</b> {name}\n"
    if email:
        msg += f"<b>Email:</b> {email}\n"
    if phone:
        msg += f"<b>Phone:</b> {phone}\n"
    if notes:
        snippet = notes[:200]
        msg += f"<b>Notes:</b> <i>{snippet}</i>\n"
    msg += f"\n<i>🕐 Captured at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
    return _send_message(msg)


def alert_payment_received(
    amount: float,
    currency: str = "USD",
    plan: str = "",
    customer_email: str = "",
    payment_method: str = "Card",
    transaction_id: str = "",
) -> bool:
    """Alert when a customer payment / deposit is confirmed."""
    tx_short = transaction_id[:16] if len(transaction_id) > 16 else transaction_id
    msg = (
        f"💰 <b>Payment Confirmed!</b>\n\n"
        f"<b>Amount:</b> {currency.upper()} {amount:.2f}\n"
    )
    if plan:
        msg += f"<b>Plan/Product:</b> {plan}\n"
    if payment_method:
        msg += f"<b>Method:</b> {payment_method}\n"
    if customer_email:
        msg += f"<b>Customer:</b> {customer_email}\n"
    if tx_short:
        msg += f"<b>Tx / Session ID:</b> <code>{tx_short}</code>\n"
    msg += f"\n<i>🕐 Confirmed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n"
    msg += "🎉 <i>Wallet / Tokens credited successfully!</i>"
    return _send_message(msg)


def alert_daily_report(
    sent_today: int,
    opened: int = 0,
    responded: int = 0,
    campaigns_active: int = 0,
    revenue_today: float = 0.0,
    leads_today: int = 0,
    currency: str = "USD",
) -> bool:
    """Send a daily summary report."""
    if not _is_configured():
        return False

    today_str = datetime.now().strftime("%Y-%m-%d")
    open_rate = round((opened / max(sent_today, 1)) * 100, 1)
    response_rate = round((responded / max(sent_today, 1)) * 100, 1)

    msg = (
        f"📊 <b>Daily Swarm Report — {today_str}</b>\n\n"
        f"📧 <b>Emails Sent:</b> {sent_today}\n"
        f"👁️ <b>Opened:</b> {opened} ({open_rate}%)\n"
        f"📬 <b>Responses:</b> {responded} ({response_rate}%)\n"
        f"🚀 <b>Active Campaigns:</b> {campaigns_active}\n"
    )
    if revenue_today > 0 or revenue_today == 0.0:
        msg += f"💰 <b>Revenue:</b> {currency.upper()} {revenue_today:.2f}\n"
    if leads_today > 0:
        msg += f"🎯 <b>Leads Captured:</b> {leads_today}\n"
    msg += "\n<i>Keep going! 📈 Autonomous Swarm is operational.</i>"
    return _send_message(msg)


def generate_and_dispatch_daily_swarm_report(conn=None) -> dict:
    """Aggregates 24-hour swarm telemetry metrics and dispatches daily Telegram report."""
    close_conn = False
    if conn is None:
        try:
            from web.shared import get_db
            conn = get_db().__enter__()
            close_conn = True
        except Exception:
            try:
                from core.database import get_db
                conn = get_db().__enter__()
                close_conn = True
            except Exception as e:
                logger.error(f"[daily_swarm_report] Could not obtain db connection: {e}")
                return {"status": "error", "error": "db_unavailable"}

    try:
        # 1. Total emails sent in last 24h / today
        try:
            sent_row = conn.execute("""
                SELECT COUNT(*) as count FROM campaign_emails
                WHERE sent_at >= datetime('now', '-24 hours') OR sent_at >= date('now')
            """).fetchone()
            sent_today = int(sent_row["count"]) if sent_row and "count" in sent_row.keys() else 0
        except Exception:
            sent_today = 0

        # 2. Total emails opened in last 24h / today
        try:
            opened_row = conn.execute("""
                SELECT COUNT(*) as count FROM campaign_emails
                WHERE (status = 'opened' OR opened_at IS NOT NULL)
                AND (opened_at >= datetime('now', '-24 hours') OR sent_at >= datetime('now', '-24 hours'))
            """).fetchone()
            opened_today = int(opened_row["count"]) if opened_row and "count" in opened_row.keys() else 0
        except Exception:
            opened_today = 0

        # 3. Responses received in last 24h / today
        try:
            replied_row = conn.execute("""
                SELECT COUNT(*) as count FROM campaign_emails
                WHERE status = 'replied'
                OR (replied_at IS NOT NULL AND replied_at >= datetime('now', '-24 hours'))
            """).fetchone()
            responded_today = int(replied_row["count"]) if replied_row and "count" in replied_row.keys() else 0
        except Exception:
            responded_today = 0

        # 4. Active running / pending campaigns
        try:
            camp_row = conn.execute("""
                SELECT COUNT(*) as count FROM campaigns
                WHERE status IN ('running', 'active', 'pending')
            """).fetchone()
            campaigns_active = int(camp_row["count"]) if camp_row and "count" in camp_row.keys() else 0
        except Exception:
            campaigns_active = 0

        # 5. Revenue today from completed orders
        try:
            rev_row = conn.execute("""
                SELECT COALESCE(SUM(amount_usd), 0.0) as total FROM orders
                WHERE payment_status IN ('completed', 'paid')
                AND created_at >= datetime('now', '-24 hours')
            """).fetchone()
            revenue_today = float(rev_row["total"]) if rev_row and "total" in rev_row.keys() else 0.0
        except Exception:
            revenue_today = 0.0

        # 6. Fire Telegram alert
        dispatched = alert_daily_report(
            sent_today=sent_today,
            opened=opened_today,
            responded=responded_today,
            campaigns_active=campaigns_active,
            revenue_today=revenue_today,
            currency="USD",
        )

        return {
            "status": "success",
            "dispatched": dispatched,
            "metrics": {
                "sent_today": sent_today,
                "opened_today": opened_today,
                "responded_today": responded_today,
                "campaigns_active": campaigns_active,
                "revenue_today": revenue_today,
            }
        }
    except Exception as exc:
        logger.error(f"[daily_swarm_report] Telemetry aggregation failed: {exc}")
        return {"status": "error", "error": str(exc)}
    finally:
        if close_conn and conn:
            try:
                conn.close()
            except Exception:
                pass


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


async def async_alert_lead_captured(
    source: str = "ATS Instant Score",
    role: str = "",
    score: int = 0,
    gulf_score: int = 0,
    name: str = "",
    email: str = "",
    phone: str = "",
    notes: str = "",
) -> bool:
    """Async wrapper for lead captured alert."""
    return await asyncio.to_thread(
        alert_lead_captured, source, role, score, gulf_score, name, email, phone, notes
    )


async def async_alert_payment_received(
    amount: float,
    currency: str = "USD",
    plan: str = "",
    customer_email: str = "",
    payment_method: str = "Card",
    transaction_id: str = "",
) -> bool:
    """Async wrapper for payment received alert."""
    return await asyncio.to_thread(
        alert_payment_received, amount, currency, plan, customer_email, payment_method, transaction_id
    )


async def async_alert_daily_report(
    sent_today: int,
    opened: int = 0,
    responded: int = 0,
    campaigns_active: int = 0,
    revenue_today: float = 0.0,
    leads_today: int = 0,
    currency: str = "USD",
) -> bool:
    """Async wrapper for daily report alert."""
    return await asyncio.to_thread(
        alert_daily_report, sent_today, opened, responded, campaigns_active, revenue_today, leads_today, currency
    )

