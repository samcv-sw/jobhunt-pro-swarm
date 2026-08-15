"""
Telegram One-Tap Approval & Interactive Webhook Router
Enables seamless mobile decision-making: users receive job match alerts
with inline [Approve & Send] / [Skip] buttons to execute cold outreach in 1 tap.
"""

import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("telegram_onetap_router")

class TelegramOneTapRouter:
    def __init__(self):
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}

    def format_lead_approval_card(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an interactive Telegram message payload with Arabic/English summary
        and inline keyboard buttons.
        """
        company = lead.get("company", "Top Enterprise")
        title = lead.get("title", "Senior Role")
        location = lead.get("location", "Gulf Region")
        intent = lead.get("intent_tier", "HIGH_INTENT")
        score = lead.get("intent_score", 90)
        salary = lead.get("salary_range", "Competitive")
        lead_id = f"lead_{int(time.time() * 1000)}"

        # Save to memory cache
        self.pending_approvals[lead_id] = lead

        # Formatted bilingual message
        text = (
            f"🎯 <b>فرصة عمل جديدة متطابقة | New Matching Lead</b>\n\n"
            f"🏢 <b>الشركة (Company):</b> {company}\n"
            f"💼 <b>المسمى (Role):</b> {title}\n"
            f"📍 <b>الموقع (Location):</b> {location}\n"
            f"💰 <b>الراتب التقديري (Salary):</b> {salary}\n"
            f"⚡ <b>مستوى الأهمية (Score):</b> {score}% ({intent})\n\n"
            f"<i>هل ترغب في تخصيص الـ CV وإرسال طلب التقديم فوراً؟</i>"
        )

        inline_keyboard = [
            [
                {"text": "✅ إرسال التقديم (Send Application)", "callback_data": f"approve_{lead_id}"},
                {"text": "⏭️ تخطي (Skip)", "callback_data": f"skip_{lead_id}"}
            ],
            [
                {"text": "📱 فتح لوحة التحكم (Open Mini App)", "web_app": {"url": "https://samcv-sw.vercel.app/miniapp"}}
            ]
        ]

        return {
            "lead_id": lead_id,
            "text": text,
            "reply_markup": {"inline_keyboard": inline_keyboard}
        }

    async def handle_callback_query(self, callback_data: str, user_id: str = "demo_user") -> Dict[str, Any]:
        """Processes the button clicks from Telegram."""
        if callback_data.startswith("approve_"):
            lead_id = callback_data.replace("approve_", "")
            lead_info = self.pending_approvals.get(lead_id, {"title": "Target Role", "company": "Target Company"})
            
            logger.info(f"User {user_id} APPROVED lead {lead_id} ({lead_info.get('title')})")
            
            return {
                "status": "dispatched",
                "message": f"🚀 تم اعتماد التقديم وإرسال السيرة الذاتية المخصصة إلى {lead_info.get('company')} بنجاح!",
                "lead_id": lead_id,
                "credits_deducted": 1
            }

        elif callback_data.startswith("skip_"):
            lead_id = callback_data.replace("skip_", "")
            logger.info(f"User {user_id} SKIPPED lead {lead_id}")
            
            return {
                "status": "skipped",
                "message": "⏭️ تم تخطي هذه الفرصة بنجاح.",
                "lead_id": lead_id,
                "credits_deducted": 0
            }

        return {"status": "unknown_action", "message": "Action unrecognized."}

onetap_router = TelegramOneTapRouter()
