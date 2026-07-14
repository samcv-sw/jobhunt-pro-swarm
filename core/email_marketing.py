"""
AUTOMATED EMAIL MARKETING ENGINE v1.0
======================================
4 campaign types that run in a background loop:
  1. Welcome Sequence  — new users get a warm welcome + discount offer
  2. Abandoned Cart    — pending orders older than 30 min get a reminder
  3. Re-engagement     — users inactive 7+ days get a "come back" offer
  4. Post-Purchase     — 24 h after purchase → thank-you + upsell

Uses Gmail SMTP (primary) + Brevo REST API (fallback) for sending.
Tracks everything in the `email_campaign_log` table.
"""

import asyncio
import logging
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import config
import core.pg_sqlite_shim as sqlite3
from core.email_engine import send_email_via_brevo_http

logger = logging.getLogger(__name__)

# ── Campaign intervals (seconds) ───────────────────────────────
CHECK_INTERVAL = 300  # main loop every 5 min
ABANDONED_CART_MIN_AGE = 1800  # 30 min before sending reminder
RE_ENGAGE_AFTER_DAYS = 7
POST_PURCHASE_AFTER_HOURS = 24

# ── Sender info ────────────────────────────────────────────────
SENDER_NAME = os.getenv("SENDER_NAME", "Sam Salameh")
SENDER_EMAIL = os.getenv("GMAIL_SMTP_USER", "samsalameh.cv@gmail.com")
BASE_URL = config.SITE_URL


# ════════════════════════════════════════════════════════════════
#  Email senders (Gmail SMTP primary + Brevo REST API fallback)
# ════════════════════════════════════════════════════════════════


def _send_via_gmail_smtp(
    to_email: str, subject: str, html_body: str, sender_name: str = "Sam Salameh"
) -> bool:
    """Send email via Gmail SMTP. Uses GMAIL_SMTP_USER + GMAIL_APP_PASSWORD_1."""
    gmail_user = os.getenv("GMAIL_SMTP_USER", "").strip()
    gmail_password = os.getenv("GMAIL_APP_PASSWORD_1", "").strip()
    if not gmail_user or not gmail_password:
        logger.warning("[EMAIL-MARKETING] Gmail SMTP not configured")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{sender_name} <{gmail_user}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        logger.info(f"[EMAIL-MARKETING] Sent via Gmail SMTP to {to_email}")
        return True
    except Exception as e:
        logger.warning(f"[EMAIL-MARKETING] Gmail SMTP failed for {to_email}: {e}")
        return False


# ════════════════════════════════════════════════════════════════
#  DB helpers
# ════════════════════════════════════════════════════════════════


def _get_db():
    """Open a connection to the main SaaS database."""
    db_path = str(Path(__file__).parent.parent / "jobhunt_saas_v2.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _already_sent(campaign_type: str, user_id: str, since_hours: int = 24) -> bool:
    """Return True if this campaign type was sent to user within since_hours."""
    try:
        conn = _get_db()
        cutoff = (datetime.now() - timedelta(hours=since_hours)).isoformat()
        row = conn.execute(
            "SELECT COUNT(*) as c FROM email_campaign_log WHERE campaign_type=? AND user_id=? AND sent_at>=?",
            (campaign_type, user_id, cutoff),
        ).fetchone()
        conn.close()
        return row and row["c"] > 0
    except Exception:
        return False


def _log_campaign(
    campaign_type: str,
    user_id: str,
    to_email: str,
    subject: str,
    status: str = "sent",
    order_id: str = None,
    error: str = None,
):
    """Insert a row into email_campaign_log."""
    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO email_campaign_log (campaign_type, user_id, to_email, subject, status, order_id, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (campaign_type, user_id, to_email, subject, status, order_id, error),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"[EMAIL-MARKETING] Log failed: {e}")


# ════════════════════════════════════════════════════════════════
#  HTML email templates
# ════════════════════════════════════════════════════════════════


def _tracking_pixel(campaign_id: int) -> str:
    """1×1 transparent GIF tracking pixel for open detection."""
    return f'<img src="{BASE_URL}/api/v2/campaign/track/{campaign_id}" width="1" height="1" style="display:none;" alt=""/>'


def _wrap_html(body: str, title: str = "JobHunt Pro") -> str:
    """Wrap body content in a professional email template."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  body {{ margin:0; padding:0; font-family:'Segoe UI',Arial,sans-serif; background:#f4f6f9; }}
  .container {{ max-width:600px; margin:0 auto; background:#ffffff; }}
  .header {{ background:linear-gradient(135deg,#1a1a2e,#16213e); padding:30px; text-align:center; }}
  .header h1 {{ color:#fff; margin:0; font-size:24px; }}
  .header p {{ color:#94a3b8; margin:5px 0 0; font-size:14px; }}
  .body {{ padding:30px; color:#333; line-height:1.6; }}
  .body h2 {{ color:#1a1a2e; font-size:20px; }}
  .body p {{ margin:0 0 16px; }}
  .cta {{ display:block; background:linear-gradient(135deg,#3b82f6,#2563eb); color:#fff !important; text-decoration:none;
          padding:14px 28px; border-radius:8px; font-weight:600; font-size:16px; text-align:center; margin:24px 0; }}
  .cta:hover {{ background:#2563eb; }}
  .features {{ background:#f8fafc; border-radius:8px; padding:20px; margin:20px 0; }}
  .features li {{ margin:8px 0; color:#475569; }}
  .footer {{ background:#f4f6f9; padding:20px; text-align:center; font-size:12px; color:#94a3b8; }}
  .footer a {{ color:#3b82f6; text-decoration:none; }}
  .badge {{ display:inline-block; background:#fef3c7; color:#92400e; padding:4px 12px; border-radius:20px; font-size:12px; font-weight:600; }}
</style>
</head><body>
<div class="container">
  <div class="header">
    <h1>🚀 JobHunt Pro</h1>
    <p>Supercharge your job search</p>
  </div>
  <div class="body">
    {body}
  </div>
  <div class="footer">
    <p>JobHunt Pro · Beirut, Lebanon</p>
    <p><a href="{BASE_URL}/unsubscribe">Unsubscribe</a> · <a href="{BASE_URL}">Visit Website</a></p>
    <div style="margin-top:20px; padding-top:15px; border-top:1px solid #e2e8f0;">
      <p style="font-size:11px; color:#64748b;">🚀 <i>Sent automatically via <a href="{BASE_URL}?ref=viral_email" style="color:#3b82f6; font-weight:bold;">JobHunt Pro</a> - Get your own AI Job Search Agent for free.</i></p>
    </div>
  </div>
</div>
</body></html>"""


def _welcome_email(name: str, campaign_id: int) -> tuple:
    """Return (subject, html_body) for welcome email."""
    subject = "🎉 Welcome to JobHunt Pro — Let's Land Your Dream Job!"
    body = f"""
    <h2>Welcome, {name}! 🎉</h2>
    <p>You've just unlocked a powerful job-hunting arsenal. Here's what's waiting for you:</p>
    <div class="features">
      <ul>
        <li>✅ <strong>AI-powered CV review</strong> — get a score + improvement tips</li>
        <li>✅ <strong>Automated job alerts</strong> — never miss an opportunity</li>
        <li>✅ <strong>Smart follow-up sequences</strong> — 3× more responses</li>
        <li>✅ <strong>Real-time analytics</strong> — track every application</li>
      </ul>
    </div>
    <p style="text-align:center;"><span class="badge">🎁 FIRST-TIME OFFER</span></p>
    <p>As a <strong>new member</strong>, here's a special gift: <strong>50% off</strong> your first CV Review or any micro-service!</p>
    <a class="cta" href="{BASE_URL}/services?ref=welcome">🎯 Claim Your Discount Now</a>
    <p style="color:#64748b;font-size:13px;">Use code <strong>WELCOME50</strong> at checkout · Expires in 7 days</p>
    <p>Ready to take control of your career? Let's go! 🚀</p>
    {_tracking_pixel(campaign_id)}
    """
    return subject, _wrap_html(body, "Welcome to JobHunt Pro")


def _abandoned_cart_email(
    name: str, service_name: str, price_usd: float, order_id: str, campaign_id: int
) -> tuple:
    """Return (subject, html_body) for abandoned cart recovery."""
    subject = "⏳ You left something behind — complete your order!"
    body = f"""
    <h2>Hey {name}, your order is waiting! 👋</h2>
    <p>You started checking out <strong>{service_name}</strong> — but didn't finish. Don't let this opportunity slip away!</p>
    <div style="background:#f0f9ff;border-left:4px solid #3b82f6;padding:16px;margin:20px 0;border-radius:4px;">
      <p style="margin:0;font-size:14px;color:#1e40af;">📦 <strong>Pending Order</strong></p>
      <p style="margin:4px 0 0;font-size:18px;font-weight:700;color:#1e40af;">${price_usd:.2f} — {service_name}</p>
    </div>
    <p>Complete your purchase now and get instant access to your service!</p>
    <a class="cta" href="{BASE_URL}/checkout/v2/{order_id}">💰 Complete Purchase Now</a>
    <p style="font-size:13px;color:#64748b;">⏰ This link expires in 24 hours</p>
    {_tracking_pixel(campaign_id)}
    """
    return subject, _wrap_html(body, "Complete Your Order")


def _re_engagement_email(name: str, campaign_id: int) -> tuple:
    """Return (subject, html_body) for re-engagement."""
    subject = "👋 We miss you! Here's a special comeback offer"
    body = f"""
    <h2>We miss you, {name}! 💙</h2>
    <p>It's been a while since you last visited JobHunt Pro. We've added some <strong>amazing new features</strong> since then:</p>
    <div class="features">
      <ul>
        <li>🔥 <strong>Flash Sales</strong> — time-limited discounts up to 50% off</li>
        <li>📊 <strong>Live Earnings Counter</strong> — see real-time revenue on our landing page</li>
        <li>🎯 <strong>Bulk Discount Calculator</strong> — save more when you buy more</li>
        <li>⚡ <strong>Faster AI processing</strong> — get results in seconds</li>
      </ul>
    </div>
    <p style="text-align:center;"><span class="badge">🎁 COMEBACK OFFER</span></p>
    <p>As a welcome back gift, here's <strong>30% off</strong> any service! Don't miss out on landing your dream job.</p>
    <a class="cta" href="{BASE_URL}/services?ref=comeback">🔥 Claim Your 30% Off</a>
    <p style="color:#64748b;font-size:13px;">Use code <strong>COMEBACK30</strong> at checkout · Expires in 5 days</p>
    {_tracking_pixel(campaign_id)}
    """
    return subject, _wrap_html(body, "Come Back to JobHunt Pro")


def _post_purchase_email(name: str, service_name: str, campaign_id: int) -> tuple:
    """Return (subject, html_body) for post-purchase follow-up + upsell."""
    subject = "✅ Purchase Confirmed — Here's What's Next!"
    body = f"""
    <h2>Thank you, {name}! 🎉</h2>
    <p>Your <strong>{service_name}</strong> purchase is confirmed and being processed. You'll receive your results shortly.</p>
    <p>While you wait, here are some <strong>complementary services</strong> that work great together:</p>
    <div class="features">
      <ul>
        <li>📝 <strong>Professional CV Review</strong> — $2 only (get your CV scored + optimized)</li>
        <li>✉️ <strong>Email Templates</strong> — $2 (custom templates that get responses)</li>
        <li>📊 <strong>Application Tracker</strong> — $4 (track every application in one dashboard)</li>
      </ul>
    </div>
    <p style="text-align:center;"><span class="badge">🎁 EXCLUSIVE UPSELL</span></p>
    <p>Since you just purchased, here's a <strong>special bundle deal</strong>: add any 2 more services for only <strong>$5 extra</strong>!</p>
    <a class="cta" href="{BASE_URL}/services?ref=upsell">🚀 Explore Bundle Deals</a>
    <p style="color:#64748b;font-size:13px;">Use code <strong>BUNDLE5</strong> at checkout</p>
    {_tracking_pixel(campaign_id)}
    """
    return subject, _wrap_html(body, "Purchase Confirmed")


# ════════════════════════════════════════════════════════════════
#  Campaign logic
# ════════════════════════════════════════════════════════════════


async def send_welcome_email(user_id: str, email: str, name: str) -> bool:
    """Send welcome email to a new user."""
    if _already_sent("welcome", user_id):
        return False
    try:
        conn = _get_db()
        conn.execute(
            "INSERT INTO email_campaign_log (campaign_type, user_id, to_email, subject, status) VALUES (?, ?, ?, ?, 'sending')",
            ("welcome", user_id, email, "🎉 Welcome to JobHunt Pro"),
        )
        conn.commit()
        campaign_id = conn.execute("SELECT last_insert_rowid() as id").fetchone()["id"]
        conn.close()

        subject, html = _welcome_email(name, campaign_id)

        # Try Gmail SMTP first, fall back to Brevo REST API
        success = _send_via_gmail_smtp(
            to_email=email,
            subject=subject,
            html_body=html,
            sender_name=SENDER_NAME,
        )
        if not success:
            success = send_email_via_brevo_http(
                to_email=email,
                company_name="Welcome",
                custom_body=html,
                sender_name=SENDER_NAME,
                subject=subject,
            )

        # Update status
        conn = _get_db()
        conn.execute(
            "UPDATE email_campaign_log SET status=? WHERE id=?",
            ("sent" if success else "failed", campaign_id),
        )
        if not success:
            conn.execute(
                "UPDATE email_campaign_log SET error='Send failed' WHERE id=?",
                (campaign_id,),
            )
        conn.commit()
        conn.close()

        if success:
            logger.info(f"[EMAIL-MARKETING] Welcome sent to {email}")
        return success
    except Exception as e:
        logger.warning(f"[EMAIL-MARKETING] Welcome error for {email}: {e}")
        return False


async def process_abandoned_carts():
    """Find pending orders older than ABANDONED_CART_MIN_AGE and send reminders."""
    try:
        conn = _get_db()
        cutoff = (
            datetime.now() - timedelta(seconds=ABANDONED_CART_MIN_AGE)
        ).isoformat()
        rows = conn.execute(
            """SELECT o.order_id, o.amount_usd, o.user_id, o.package_name, u.email, COALESCE(u.name,'User') as name
               FROM orders o JOIN users u ON o.user_id = u.user_id
               WHERE o.payment_status='pending' AND o.created_at <= ?""",
            (cutoff,),
        ).fetchall()
        conn.close()

        sent = 0
        for row in rows:
            if _already_sent("abandoned_cart", row["user_id"]):
                continue

            service_name = row["package_name"] or "Service"
            subject, html = _abandoned_cart_email(
                row["name"], service_name, float(row["amount_usd"]), row["order_id"], 0
            )

            success = _send_via_gmail_smtp(
                to_email=row["email"],
                subject=subject,
                html_body=html,
                sender_name=SENDER_NAME,
            )
            if not success:
                success = send_email_via_brevo_http(
                    to_email=row["email"],
                    company_name="Abandoned Cart",
                    custom_body=html,
                    sender_name=SENDER_NAME,
                    subject=subject,
                )

            _log_campaign(
                "abandoned_cart",
                row["user_id"],
                row["email"],
                subject,
                "sent" if success else "failed",
                order_id=row["order_id"],
                error=None if success else "Send failed",
            )
            if success:
                sent += 1

        if sent:
            logger.info(f"[EMAIL-MARKETING] Abandoned cart reminders sent: {sent}")
    except Exception as e:
        logger.warning(f"[EMAIL-MARKETING] Abandoned cart error: {e}")


async def process_re_engagement():
    """Find users inactive for RE_ENGAGE_AFTER_DAYS days and send comeback email."""
    try:
        conn = _get_db()
        cutoff = (datetime.now() - timedelta(days=RE_ENGAGE_AFTER_DAYS)).isoformat()
        rows = conn.execute(
            """SELECT user_id, email, COALESCE(name,'User') as name FROM users
               WHERE (last_login IS NULL OR last_login <= ?)
               AND created_at <= ?""",
            (cutoff, cutoff),
        ).fetchall()
        conn.close()

        sent = 0
        for row in rows:
            if _already_sent(
                "re_engagement", row["user_id"], since_hours=24 * 30
            ):  # once per month
                continue

            subject, html = _re_engagement_email(row["name"], 0)

            success = _send_via_gmail_smtp(
                to_email=row["email"],
                subject=subject,
                html_body=html,
                sender_name=SENDER_NAME,
            )
            if not success:
                success = send_email_via_brevo_http(
                    to_email=row["email"],
                    company_name="Re-engagement",
                    custom_body=html,
                    sender_name=SENDER_NAME,
                    subject=subject,
                )

            _log_campaign(
                "re_engagement",
                row["user_id"],
                row["email"],
                subject,
                "sent" if success else "failed",
            )
            if success:
                sent += 1

        if sent:
            logger.info(f"[EMAIL-MARKETING] Re-engagement emails sent: {sent}")
    except Exception as e:
        logger.warning(f"[EMAIL-MARKETING] Re-engagement error: {e}")


async def process_post_purchase():
    """Find completed orders from 24h ago without follow-up sent."""
    try:
        conn = _get_db()
        cutoff_start = (
            datetime.now() - timedelta(hours=POST_PURCHASE_AFTER_HOURS)
        ).isoformat()
        cutoff_end = (
            datetime.now() - timedelta(hours=1)
        ).isoformat()  # within last 23h window
        rows = conn.execute(
            """SELECT o.order_id, o.user_id, COALESCE(o.package_name,'Service') as service_name,
                      u.email, COALESCE(u.name,'User') as name
               FROM orders o JOIN users u ON o.user_id = u.user_id
               WHERE o.payment_status='completed'
               AND o.completed_at BETWEEN ? AND ?""",
            (cutoff_start, cutoff_end),
        ).fetchall()
        conn.close()

        sent = 0
        for row in rows:
            if _already_sent("post_purchase", row["user_id"], since_hours=48):
                continue

            subject, html = _post_purchase_email(row["name"], row["service_name"], 0)

            success = _send_via_gmail_smtp(
                to_email=row["email"],
                subject=subject,
                html_body=html,
                sender_name=SENDER_NAME,
            )
            if not success:
                success = send_email_via_brevo_http(
                    to_email=row["email"],
                    company_name="Post-Purchase",
                    custom_body=html,
                    sender_name=SENDER_NAME,
                    subject=subject,
                )

            _log_campaign(
                "post_purchase",
                row["user_id"],
                row["email"],
                subject,
                "sent" if success else "failed",
                order_id=row["order_id"],
            )
            if success:
                sent += 1

        if sent:
            logger.info(f"[EMAIL-MARKETING] Post-purchase follow-ups sent: {sent}")
    except Exception as e:
        logger.warning(f"[EMAIL-MARKETING] Post-purchase error: {e}")


# ════════════════════════════════════════════════════════════════
#  Background loop
# ════════════════════════════════════════════════════════════════


async def email_marketing_loop():
    """Background loop that runs every CHECK_INTERVAL seconds."""
    logger.info("[EMAIL-MARKETING] Background engine started")
    cycle = 0
    while True:
        try:
            cycle += 1
            # Run abandoned cart check every cycle (5 min)
            await process_abandoned_carts()

            # Run re-engagement every 12th cycle (~1 hour)
            if cycle % 12 == 0:
                await process_re_engagement()

            # Run post-purchase every 6th cycle (~30 min)
            if cycle % 6 == 0:
                await process_post_purchase()

        except Exception as e:
            logger.warning(f"[EMAIL-MARKETING] Loop error: {e}")

        import random

        # Stagger background loop to avoid exact 5-min intervals
        jitter = random.randint(-45, 90)
        await asyncio.sleep(max(60, CHECK_INTERVAL + jitter))

def get_campaign_stats() -> dict:
    """Return aggregated campaign stats for reporting."""
    try:
        conn = _get_db()
        rows = conn.execute(
            """SELECT campaign_type, status, COUNT(*) as cnt
               FROM email_campaign_log GROUP BY campaign_type, status"""
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) as c FROM email_campaign_log").fetchone()[
            "c"
        ]
        conn.close()

        stats = {"total": total, "breakdown": {}}
        for row in rows:
            ct = row["campaign_type"]
            if ct not in stats["breakdown"]:
                stats["breakdown"][ct] = {}
            stats["breakdown"][ct][row["status"]] = row["cnt"]
        return stats
    except Exception as e:
        return {"total": 0, "error": str(e)}
