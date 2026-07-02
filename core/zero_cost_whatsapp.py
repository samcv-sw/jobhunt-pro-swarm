"""
JobHunt Pro v13 - WhatsApp Cloud API Automation
Uses Meta's official WhatsApp Cloud API (1,000 free conversations/month).
Perfect for 24/7 headless cloud deployment.
"""

import logging
import httpx
import os

logger = logging.getLogger(__name__)


class ZeroCostWhatsAppAutomator:
    """
    Automates WhatsApp via Meta Cloud API via REST (No browser required).
    """

    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_id = os.getenv("WHATSAPP_PHONE_ID", "")

    async def send_whatsapp_message(
        self, phone_number: str, candidate_name: str, company: str, position: str
    ) -> dict:
        """
        Sends a free WhatsApp message using Meta's REST API.
        """
        if not self.access_token or not self.phone_id:
            logger.warning(
                "WhatsApp API credentials missing. Simulating Cloud API request."
            )
            return {"status": "simulated", "platform": "whatsapp_cloud_api"}

        message = f"Hi from {candidate_name}!\n\nI recently applied for the {position} role at {company} and wanted to follow up. Let me know if you have a moment to chat!"

        url = f"https://graph.facebook.com/v17.0/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        # Format phone number (Meta requires country code without + or 00)
        formatted_phone = (
            phone_number.replace("+", "").replace(" ", "").replace("-", "")
        )

        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "text",
            "text": {"body": message},
        }

        try:
            logger.info(
                f"Preparing to send Cloud WhatsApp message to {formatted_phone}..."
            )

            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=headers, json=payload)

                if resp.status_code in (200, 201):
                    logger.info(
                        f"Successfully sent WhatsApp message to {formatted_phone}"
                    )
                    return {"status": "success", "platform": "whatsapp_cloud_api"}
                else:
                    logger.error(f"WhatsApp Cloud API Error: {resp.text}")
                    return {"status": "error", "error": resp.text}

        except Exception as e:
            logger.error(f"WhatsApp Cloud automation failed: {e}")
            return {"status": "error", "error": str(e)}


whatsapp_automator = ZeroCostWhatsAppAutomator()
