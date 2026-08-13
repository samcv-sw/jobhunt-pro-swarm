"""
AI Reply Sentiment Engine & SDR Inbox Classifier
Categorizes prospect responses: Interested, Objection, Unsubscribe, Wrong Person.
"""

import re
from typing import Dict, Any

class ReplySentimentService:
    def __init__(self):
        self.interested_keywords = ["interested", "call", "demo", "meeting", "talk", "schedule", "pricing", "send details", "let's connect", "sure"]
        self.objection_keywords = ["too expensive", "budget", "not right now", "next quarter", "busy", "already use", "competitor"]
        self.unsubscribe_keywords = ["unsubscribe", "remove", "stop", "dont email", "don't email", "take me off", "spam"]
        self.referral_keywords = ["wrong person", "reach out to", "contact my colleague", "talk to", "refer to"]

    def classify_reply(self, reply_text: str) -> Dict[str, Any]:
        """
        Classifies incoming reply text and generates smart next-action tag.
        """
        if not reply_text:
            return {"category": "Unknown", "confidence": 0.0, "action": "manual_review"}

        text_lower = reply_text.lower()

        # Check unsubscribe first (highest priority for compliance)
        for kw in self.unsubscribe_keywords:
            if kw in text_lower:
                return {
                    "category": "Unsubscribe",
                    "sentiment": "Negative",
                    "confidence": 0.95,
                    "action": "auto_opt_out",
                    "suggested_reply": None
                }

        # Check referral / wrong person
        for kw in self.referral_keywords:
            if kw in text_lower:
                return {
                    "category": "Referral / Wrong Person",
                    "sentiment": "Neutral",
                    "confidence": 0.88,
                    "action": "update_contact",
                    "suggested_reply": "Thank you for pointing me in the right direction! I will reach out to your colleague."
                }

        # Check interested
        for kw in self.interested_keywords:
            if kw in text_lower:
                return {
                    "category": "Interested / High Intent",
                    "sentiment": "Positive",
                    "confidence": 0.90,
                    "action": "send_calendar_link",
                    "suggested_reply": "Great to connect! Here is a link to pick a time that works best for you: [Calendar Link]"
                }

        # Check objection
        for kw in self.objection_keywords:
            if kw in text_lower:
                return {
                    "category": "Objection / Bad Timing",
                    "sentiment": "Neutral/Negative",
                    "confidence": 0.82,
                    "action": "handle_objection",
                    "suggested_reply": "Understood! Would it make sense to circle back in 3 months when timing might be better?"
                }

        # Default fallback
        return {
            "category": "General Inquiry",
            "sentiment": "Neutral",
            "confidence": 0.60,
            "action": "manual_review",
            "suggested_reply": "Thank you for your reply! How can I best assist you?"
        }

reply_sentiment_service = ReplySentimentService()
