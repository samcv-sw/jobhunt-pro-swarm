"""
core/sentiment_auto_reply.py
Automated Sentiment & Intent Classifier with Auto-Reply & Booking Generator
Analyzes incoming recruiter and hiring manager replies, classifies intent,
and generates hyper-tailored responses with automatic calendar link insertion.
"""

import re
from typing import Dict, Any, Optional


class SentimentAutoReplyEngine:
    """
    Classifies recruiter reply intent and generates objection-handling responses.
    """

    INTENT_KEYWORDS = {
        "interested": [
            "interested", "sounds good", "let's talk", "schedule", "call", "interview",
            "send your cv", "send your resume", "share your profile", "مهتم", "تفضل", "أرسل السيرة", "مقابلة"
        ],
        "objection_experience": [
            "years of experience", "looking for more senior", "require more experience", "خبرة أكثر"
        ],
        "objection_budget": [
            "budget", "rate is high", "salary range", "ميزانية", "الراتب"
        ],
        "not_interested": [
            "not interested", "not hiring", "no open positions", "unsubscribe", "remove me", "غير مهتم", "لا توجد شواغر"
        ],
        "out_of_office": [
            "out of office", "on leave", "vacation", "auto-reply", "إجازة", "رد تلقائي"
        ],
    }

    @classmethod
    def classify_intent(cls, message_text: str) -> Dict[str, Any]:
        """
        Classifies the sentiment and intent of an incoming reply.
        """
        clean_text = message_text.lower().strip()

        for intent, keywords in cls.INTENT_KEYWORDS.items():
            for kw in keywords:
                if kw in clean_text:
                    sentiment = "positive" if intent == "interested" else ("neutral" if intent == "out_of_office" else "negative")
                    return {
                        "intent": intent,
                        "sentiment": sentiment,
                        "confidence": 0.95,
                        "detected_keyword": kw,
                    }

        return {
            "intent": "general_inquiry",
            "sentiment": "neutral",
            "confidence": 0.70,
            "detected_keyword": None,
        }

    @classmethod
    def generate_smart_reply(
        cls,
        incoming_message: str,
        candidate_name: str,
        booking_link: str = "https://cal.com/sam-dev",
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Generates the recommended response based on intent.
        """
        classification = cls.classify_intent(incoming_message)
        intent = classification["intent"]
        is_arabic = language.lower() in ["ar", "arabic"] or bool(re.search(r"[\u0600-\u06FF]", incoming_message))

        if intent == "interested":
            if is_arabic:
                reply_text = (
                    f"أهلاً وسهلاً،\n\n"
                    f"شكراً جزيلاً لاهتمامكم ووقتكم. يسعدني جداً تنسيق مكالمة سريعة.\n"
                    f"يمكنكم اختيار الموعد الأنسب لكم مباشرة عبر هذا الرابط:\n{booking_link}\n\n"
                    f"أتطلع للحديث معكم قريباً.\n\nتحياتي،\n{candidate_name}"
                )
            else:
                reply_text = (
                    f"Hi there,\n\n"
                    f"Thank you for getting back to me! I'd love to connect and discuss how I can contribute to your goals.\n"
                    f"You can easily pick a time that works best for you here: {booking_link}\n\n"
                    f"Looking forward to speaking with you.\n\nBest regards,\n{candidate_name}"
                )
            action = "schedule_meeting"

        elif intent == "objection_experience":
            if is_arabic:
                reply_text = (
                    f"شكراً لردكم الكريم.\n"
                    f"أتفهم تماماً نقطتكم بخصوص سنوات الخبرة، ولكن أود الإشارة إلى أن تركيزي كان دائماً على سرعة الإنجاز والنتائج العملية المؤثرة.\n"
                    f"يسعدني مشاركة مشاريع عملية تثبت ذلك.\n\nتحياتي،\n{candidate_name}"
                )
            else:
                reply_text = (
                    f"Thank you for the candid feedback.\n"
                    f"While total years of experience is important, my focus has consistently been on delivering high-impact, scalable results rapidly.\n"
                    f"I would be glad to share live project metrics demonstrating this.\n\nBest regards,\n{candidate_name}"
                )
            action = "handle_objection"

        elif intent == "out_of_office":
            reply_text = ""
            action = "wait_and_retry"

        else:
            if is_arabic:
                reply_text = f"شكراً جزيلاً لوقتكم، وأتمنى لكم وللفريق دوام التوفيق والنجاح.\n\nتحياتي،\n{candidate_name}"
            else:
                reply_text = f"Thank you for your time and response. Wishing you and the team continued success!\n\nBest,\n{candidate_name}"
            action = "archive_or_close"

        return {
            "intent": intent,
            "sentiment": classification["sentiment"],
            "suggested_reply": reply_text,
            "action_recommended": action,
            "booking_link_included": (intent == "interested"),
        }


# Global Engine Instance
global_sentiment_engine = SentimentAutoReplyEngine()
