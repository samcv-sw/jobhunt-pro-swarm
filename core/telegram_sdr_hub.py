"""
core/telegram_sdr_hub.py
=========================
Autonomous Telegram SDR & Real-Time Intelligence Telemetry Hub.
Dispatches live application delivery notifications, daily lead digests,
and interactive AI mock interview simulation directly to candidate Telegram chats.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("TelegramSdrHub")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class TelegramSdrHub:
    """
    Manages direct Telegram webhook alerts, telemetry dispatches, and SDR interactions.
    """

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    async def send_message(self, text: str, parse_mode: str = "HTML", target_chat_id: Optional[str] = None) -> bool:
        """Sends an HTML formatted message to the user's Telegram."""
        cid = target_chat_id or self.chat_id
        if not self.bot_token or not cid:
            logger.debug("[TelegramHub] Missing bot_token or chat_id. Notification skipped.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=8.0)
                return resp.status_code == 200
        except Exception as e:
            logger.debug(f"[TelegramHub] Send message error: {e}")
            return False

    async def notify_application_dispatched(
        self, candidate_name: str, company: str, role: str, provider: str
    ) -> bool:
        """Alerts the candidate when an outreach email is successfully sent."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        msg = (
            f"🚀 <b>Job Application Dispatched!</b>\n\n"
            f"👤 <b>Candidate:</b> {candidate_name}\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"💼 <b>Role:</b> {role}\n"
            f"🛡️ <b>Deliverability Engine:</b> {provider} (MX Verified)\n"
            f"🕒 <b>Time:</b> {timestamp}\n\n"
            f"✨ <i>JobHunt Pro 24/7 Autonomous SDR</i>"
        )
        return await self.send_message(msg)

    async def notify_daily_lead_digest(self, leads_count: int, top_companies: List[str]) -> bool:
        """Sends a daily summary of newly harvested leads."""
        companies_text = ", ".join(top_companies[:5]) if top_companies else "Gulf Tech Startups"
        msg = (
            f"📊 <b>Daily 24/7 Swarm Digest</b>\n\n"
            f"🎯 <b>New Verified Leads:</b> {leads_count}\n"
            f"🏢 <b>Featured Companies:</b> {companies_text}\n"
            f"⚡ <b>Cloud Status:</b> 100% Operational (0$ Cost)\n\n"
            f"🔗 <a href='https://jobhuntpro.io/dashboard'>Open Dashboard</a>"
        )
        return await self.send_message(msg)

    async def send_interactive_message(
        self,
        text: str,
        reply_markup: Optional[Dict[str, Any]] = None,
        target_chat_id: Optional[str] = None
    ) -> bool:
        """Sends an HTML formatted message with custom inline action buttons."""
        cid = target_chat_id or self.chat_id
        if not self.bot_token or not cid:
            logger.debug("[TelegramHub] Missing bot_token or chat_id. Interactive notification skipped.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload: Dict[str, Any] = {
            "chat_id": cid,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=8.0)
                return resp.status_code == 200
        except Exception as e:
            logger.debug(f"[TelegramHub] Send interactive message error: {e}")
            return False

    async def notify_inbound_reply_detected(
        self,
        company: str,
        sender_email: str,
        intent_data: Dict[str, Any],
        lead_id: Optional[str] = None
    ) -> bool:
        """
        Sends an instant high-priority Telegram alert when a company replies to outreach,
        complete with 1-click interactive response options.
        """
        intent = intent_data.get("intent", "GENERAL_INQUIRY")
        urgency = intent_data.get("urgency", "MEDIUM")
        suggested = intent_data.get("suggested_reply", "Looking forward to speaking.")
        lid = lead_id or "default"

        icon = "🔥" if intent == "INTERVIEW_INVITE" else ("💰" if intent == "SALARY_INQUIRY" else "📩")
        
        msg = (
            f"{icon} <b>Inbound Recruiter Response Received!</b>\n\n"
            f"🏢 <b>Company:</b> {company}\n"
            f"👤 <b>Sender:</b> {sender_email}\n"
            f"🎯 <b>Intent Detected:</b> <code>{intent}</code> (Urgency: {urgency})\n\n"
            f"💡 <b>AI Suggested 1-Click Reply:</b>\n"
            f"<i>\"{suggested}\"</i>\n\n"
            f"⚡ <i>Choose an action below to dispatch instantly from Telegram:</i>"
        )

        inline_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Send AI Reply", "callback_data": f"reply_approve:{lid}"},
                    {"text": "📅 Send Calendar Link", "callback_data": f"reply_calendar:{lid}"}
                ],
                [
                    {"text": "⏸️ Snooze 24h", "callback_data": f"reply_snooze:{lid}"},
                    {"text": "📁 Archive Lead", "callback_data": f"reply_archive:{lid}"}
                ]
            ]
        }

        return await self.send_interactive_message(msg, reply_markup=inline_keyboard)

    @staticmethod
    def generate_mock_interview_question(role: str, category: str = "technical") -> Dict[str, str]:
        """
        Generates interactive interview questions for candidate practice.
        """
        questions = {
            "technical": [
                f"How would you design a high-throughput, low-latency API architecture for a {role} role?",
                f"Can you explain a complex bug or performance bottleneck you resolved in production as a {role}?",
                "How do you handle database failover and caching when building microservices?",
            ],
            "behavioral": [
                f"Tell me about a time you had a technical disagreement with a team member and how you resolved it.",
                f"Describe a project where you had to quickly adapt to changing business requirements as a {role}.",
                "How do you prioritize competing deadlines when managing critical production systems?",
            ],
        }
        selected_category = category if category in questions else "behavioral"
        import random
        question = random.choice(questions[selected_category])
        return {
            "role": role,
            "category": selected_category,
            "question": question,
            "tips": "Use the STAR method (Situation, Task, Action, Result) for the best evaluation score.",
        }

    def verify_telegram_webapp_data(
        self,
        init_data: str,
        bot_token: Optional[str] = None,
        max_age_seconds: int = 86400
    ) -> Dict[str, Any]:
        """
        Cryptographically validates Telegram WebApp/Mini App initData using HMAC-SHA256.
        Standard implementation according to official Telegram Bot API specification:
        1. Parse key-value pairs from init_data.
        2. Extract and remove 'hash'.
        3. Sort remaining key-value pairs lexicographically (key=value joined by \n).
        4. Compute secret_key = HMAC_SHA256("WebAppData", bot_token).
        5. Compute signature = HMAC_SHA256(secret_key, data_check_string).hexdigest().
        6. Validate constant-time equality between signature and received hash.
        7. Check auth_date TTL to prevent replay attacks.
        """
        token = bot_token or self.bot_token
        if not token or not init_data:
            return {"is_valid": False, "error": "Missing bot token or init_data string"}

        try:
            parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
            received_hash = parsed.pop("hash", None)
            if not received_hash:
                return {"is_valid": False, "error": "Missing hash parameter in init_data"}

            # Build data_check_string
            data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

            # Step 1: secret_key = HMAC-SHA256(b"WebAppData", bot_token)
            secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()

            # Step 2: calculated_hash = HMAC-SHA256(secret_key, data_check_string)
            calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

            if not hmac.compare_digest(calculated_hash, received_hash):
                return {
                    "is_valid": False,
                    "error": "Invalid HMAC-SHA256 signature",
                    "calculated_hash": calculated_hash
                }

            # Check timestamp expiration
            auth_date = int(parsed.get("auth_date", 0))
            if auth_date > 0 and max_age_seconds > 0:
                now = int(datetime.now(timezone.utc).timestamp())
                if (now - auth_date) > max_age_seconds:
                    return {
                        "is_valid": False,
                        "error": "init_data expired (replay attack protection)",
                        "auth_date": auth_date,
                        "age_seconds": now - auth_date
                    }

            # Parse user JSON
            user_data = {}
            if "user" in parsed:
                try:
                    user_data = json.loads(parsed["user"])
                except Exception:
                    user_data = {"raw": parsed["user"]}

            return {
                "is_valid": True,
                "user": user_data,
                "auth_date": auth_date,
                "query_id": parsed.get("query_id"),
                "params": parsed
            }
        except Exception as e:
            logger.error(f"[TelegramHub] HMAC verification exception: {e}")
            return {"is_valid": False, "error": str(e)}

    @classmethod
    def generate_signed_init_data(
        cls,
        user_dict: Dict[str, Any],
        bot_token: str,
        auth_date: Optional[int] = None,
        query_id: Optional[str] = None
    ) -> str:
        """
        Helper method to generate valid signed initData for Mini App testing / simulation.
        """
        now = auth_date or int(datetime.now(timezone.utc).timestamp())
        qid = query_id or f"AAH_{uuid_hex[:6]}" if "uuid_hex" in locals() else f"AAH_TEST_{now}"
        
        params = {
            "auth_date": str(now),
            "query_id": qid,
            "user": json.dumps(user_dict, separators=(",", ":"))
        }
        
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
        calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        
        params["hash"] = calc_hash
        return urllib.parse.urlencode(params)


# Global singleton
telegram_sdr = TelegramSdrHub()

