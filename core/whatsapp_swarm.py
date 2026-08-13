"""
WhatsApp Business SDR Outreach Queue & Dispatcher for GCC/MENA Prospects.
"""

from typing import Dict, Any, List


def format_whatsapp_outreach_payload(phone_number: str, prospect_name: str, offer_text: str) -> Dict[str, Any]:
    """
    Formats WhatsApp Cloud API payload for personalized B2B outreach.
    """
    clean_phone = phone_number.replace("+", "").replace(" ", "").replace("-", "")
    
    body_text = f"Marhaba {prospect_name} 👋\n\n{offer_text}\n\nWould you be open for a quick 5-min chat this week?"

    return {
        "messaging_product": "whatsapp",
        "to": clean_phone,
        "type": "text",
        "text": {
            "body": body_text
        },
        "preview_url": True,
        "status": "queued_for_swarm"
    }
