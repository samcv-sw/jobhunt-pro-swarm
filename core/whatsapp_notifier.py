"""
WhatsApp Notifier for JobHunt Pro
Supports: wa.me links, Telegram notifications, campaign tracking
"""

import asyncio
import html
import logging
import urllib.parse

import requests as _requests

from config import CANDIDATE_PHONE, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

CANDIDATE_PHONE_STR = "++12494985866"


def _get_phone() -> str:
    phone = CANDIDATE_PHONE
    if callable(phone):
        phone = phone()
    return str(phone) if phone else CANDIDATE_PHONE_STR


def get_whatsapp_contact_url() -> str:
    """Get wa.me URL for Sam's WhatsApp contact"""
    phone = _get_phone().replace("+", "").replace(" ", "").replace("-", "")
    return f"https://wa.me/{phone}"


def generate_wa_me_link(phone: str = None, message: str = "") -> str:
    """Generate wa.me deep link"""
    if not phone:
        phone = _get_phone()
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    encoded = urllib.parse.quote(message[:500]) if message else ""
    return f"https://wa.me/{phone}?text={encoded}"


def notify_application_submitted(
    company: str, position: str, recipient: str = ""
) -> str:
    """Notify via Telegram that an application was submitted"""
    company_esc = html.escape(company)
    position_esc = html.escape(position)
    recipient_esc = html.escape(recipient) if recipient else ""
    msg = f"✅ Application Submitted!\n🏢 {company_esc}\n💼 {position_esc}"
    if recipient_esc:
        msg += f"\n📧 {recipient_esc}"
    msg += f"\n\n📱 WhatsApp: {get_whatsapp_contact_url()}"
    _send_telegram(msg)
    return msg


def notify_campaign_started(name: str, total: int) -> str:
    """Notify campaign start"""
    name_esc = html.escape(name)
    msg = f"🚀 Campaign Started: {name_esc}\n📊 Total targets: {total}\n\n📱 WhatsApp: {get_whatsapp_contact_url()}"
    _send_telegram(msg)
    return msg


def notify_interview_scheduled(company: str, position: str, date: str = "") -> str:
    """Notify interview scheduled"""
    company_esc = html.escape(company)
    position_esc = html.escape(position)
    date_esc = html.escape(date) if date else ""
    msg = f"🎯 Interview Scheduled!\n🏢 {company_esc}\n💼 {position_esc}"
    if date_esc:
        msg += f"\n📅 {date_esc}"
    msg += f"\n\n📱 WhatsApp: {get_whatsapp_contact_url()}"
    _send_telegram(msg)
    return msg


def notify_error(source: str, error: str) -> str:
    """Notify error"""
    source_esc = html.escape(source)
    error_esc = html.escape(error[:200])
    msg = f"❌ Error in {source_esc}\n⚠️ {error_esc}\n\n📱 WhatsApp: {get_whatsapp_contact_url()}"
    _send_telegram(msg)
    return msg


def _send_telegram(message: str) -> bool:
    """Internal: send Telegram message (non-blocking if async loop is running)"""

    def _do_send():
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML",
            }
            r = _requests.post(url, json=payload, timeout=15)
            if r.status_code != 200:
                logger.error(f"Telegram API error ({r.status_code}): {r.text}")
                return False
            return True
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _do_send)
        return True
    except RuntimeError:
        return _do_send()


def send_wa_link(phone: str, message: str) -> str:
    return generate_wa_me_link(phone, message)


def notify_via_telegram(message: str) -> bool:
    return _send_telegram(message)


def notify_application(company: str, position: str, status: str = "sent") -> bool:
    notify_application_submitted(company, position)
    return True


def notify_lead_converted(company: str, lead_email: str, status: str, notes: str = "") -> str:
    """Send an instant lead conversion notification via Telegram + WhatsApp deep link."""
    company_esc = html.escape(company)
    email_esc = html.escape(lead_email)
    status_esc = html.escape(status)
    notes_esc = html.escape(notes[:200]) if notes else "Lead interacted with campaign."

    wa_link = generate_wa_me_link(message=f"Follow up with lead: {lead_email} from {company}")
    msg = (
        f"🔥 *INSTANT LEAD ALERT!*\n"
        f"🏢 *Company:* {company_esc}\n"
        f"📧 *Contact:* {email_esc}\n"
        f"📌 *Status:* {status_esc}\n"
        f"📝 *Details:* {notes_esc}\n\n"
        f"📱 [Instant WhatsApp Follow-up]({wa_link})"
    )
    _send_telegram(msg)
    return msg


def notify_recruiter_opened_cv(company: str, candidate_name: str, location: str = "GCC") -> str:
    """Send an instant alert to candidate when a recruiter opens their CV / application."""
    company_esc = html.escape(company)
    cand_esc = html.escape(candidate_name)
    loc_esc = html.escape(location)

    msg = (
        f"👀 <b>RECRUITER VIEWED YOUR CV!</b>\n"
        f"🏢 <b>Company:</b> {company_esc} ({loc_esc})\n"
        f"👤 <b>Candidate:</b> {cand_esc}\n"
        f"⏱ <b>Timestamp:</b> Just now\n\n"
        f"💡 Tip: Prepare for potential phone/email outreach!"
    )
    _send_telegram(msg)
    return msg


def generate_whatsapp_checkout_link(
    package_id: str,
    package_name: str,
    price_usd: float,
    customer_phone: str = None,
    sales_phone: str = None,
    payment_method: str = "Whish Money / USDT / Card"
) -> str:
    """Generate 1-click WhatsApp order link for MENA/Lebanon users with pre-filled cart info."""
    message = (
        f"Hello JobHunt Pro! I want to order:\n"
        f"📦 Package: {package_name} (${price_usd})\n"
        f"💳 Payment Method: {payment_method}\n"
        f"Please send payment instructions and activate my access."
    )
    return generate_wa_me_link(phone=sales_phone, message=message)


if __name__ == "__main__":
    logger.debug(f"Contact URL: {get_whatsapp_contact_url()}")
    logger.debug(f"Link: {generate_wa_me_link(message='Hi JobHunt Pro Team!')}")
    notify_application_submitted("Test Corp", "Network Engineer")


