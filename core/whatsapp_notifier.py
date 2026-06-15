"""
WhatsApp Notifier for JobHunt Pro
Supports: wa.me links, Telegram notifications, campaign tracking
"""
import logging
import urllib.parse
import requests as _requests
import asyncio
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, CANDIDATE_PHONE, CANDIDATE_NAME

logger = logging.getLogger(__name__)

CANDIDATE_PHONE_STR = "+96171019053"

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

def notify_application_submitted(company: str, position: str, recipient: str = "") -> str:
    """Notify via Telegram that an application was submitted"""
    msg = f"✅ Application Submitted!\n🏢 {company}\n💼 {position}"
    if recipient:
        msg += f"\n📧 {recipient}"
    msg += f"\n\n📱 WhatsApp: {get_whatsapp_contact_url()}"
    _send_telegram(msg)
    return msg

def notify_campaign_started(name: str, total: int) -> str:
    """Notify campaign start"""
    msg = f"🚀 Campaign Started: {name}\n📊 Total targets: {total}\n\n📱 WhatsApp: {get_whatsapp_contact_url()}"
    _send_telegram(msg)
    return msg

def notify_interview_scheduled(company: str, position: str, date: str = "") -> str:
    """Notify interview scheduled"""
    msg = f"🎯 Interview Scheduled!\n🏢 {company}\n💼 {position}"
    if date:
        msg += f"\n📅 {date}"
    msg += f"\n\n📱 WhatsApp: {get_whatsapp_contact_url()}"
    _send_telegram(msg)
    return msg

def notify_error(source: str, error: str) -> str:
    """Notify error"""
    msg = f"❌ Error in {source}\n⚠️ {error[:200]}\n\n📱 WhatsApp: {get_whatsapp_contact_url()}"
    _send_telegram(msg)
    return msg

def _send_telegram(message: str) -> bool:
    """Internal: send Telegram message"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        _requests.post(url, json=payload, timeout=15)
        return True
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False

def send_wa_link(phone: str, message: str) -> str:
    return generate_wa_me_link(phone, message)

def notify_via_telegram(message: str) -> bool:
    return _send_telegram(message)

def notify_application(company: str, position: str, status: str = "sent") -> bool:
    notify_application_submitted(company, position)
    return True

if __name__ == "__main__":
    print(f"Contact URL: {get_whatsapp_contact_url()}")
    print(f"Link: {generate_wa_me_link(message='Hi Sam!')}")
    notify_application_submitted("Test Corp", "Network Engineer")
