"""
core/outreach_sentiment_scheduler.py - AI Outreach Sentiment Analysis & Meeting Scheduler
=======================================================================================
- Analyzes incoming email replies from recruiters and hiring managers.
- Detects interview intent, portfolio requests, and scheduling opportunities.
- Prepares tailored executive follow-up responses and suggested calendar slots.
"""

import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

INTERVIEW_KEYWORDS = [
    "interview", "meet", "call", "schedule", "zoom", "teams", "chat",
    "available", "time", "tuesday", "wednesday", "thursday", "friday", "monday",
    "مقابلة", "مكالمة", "اجتماع", "موعد", "متاح"
]

PORTFOLIO_KEYWORDS = [
    "portfolio", "cv", "resume", "github", "sample", "work", "projects",
    "سيرة", "أعمال", "مشاريع"
]

REJECTION_KEYWORDS = [
    "not hiring", "not at this time", "kept on file", "future consideration",
    "unfortunately", "other candidates", "closed", "اعتذار", "نأسف"
]


def analyze_recruiter_sentiment(
    reply_body: str,
    sender_email: str = "",
    job_title: str = "Senior Engineer"
) -> Dict[str, Any]:
    """
    Classifies recruiter reply sentiment and drafts an executive reply strategy.
    """
    clean_text = reply_body.lower()
    
    # 1. Check for interview intent
    if any(kw in clean_text for kw in INTERVIEW_KEYWORDS) and not any(kw in clean_text for kw in REJECTION_KEYWORDS):
        category = "INTERVIEW_INVITATION"
        priority = "URGENT_HIGH"
        suggested_reply = (
            f"Thank you for the invitation! I would be delighted to speak with you regarding the {job_title} role. "
            f"I am available this week on Tuesday at 2:00 PM GST or Thursday at 11:00 AM GST. "
            f"Please let me know what works best for your team."
        )
    # 2. Check for portfolio / CV request
    elif any(kw in clean_text for kw in PORTFOLIO_KEYWORDS):
        category = "REQUEST_PORTFOLIO_INFO"
        priority = "HIGH"
        suggested_reply = (
            f"Thank you for reaching out! Please find attached my updated portfolio and technical project summaries "
            f"tailored to the {job_title} position. Looking forward to your thoughts."
        )
    # 3. Check for rejection
    elif any(kw in clean_text for kw in REJECTION_KEYWORDS):
        category = "POLITE_DECLINE"
        priority = "LOW"
        suggested_reply = (
            f"Thank you for letting me know. I appreciate your time and consideration, and I hope we can connect "
            f"on future opportunities as your team expands."
        )
    else:
        category = "GENERAL_INQUIRY"
        priority = "MEDIUM"
        suggested_reply = (
            f"Thank you for your response regarding the {job_title} opportunity. "
            f"I would be glad to provide any additional details you may need."
        )

    return {
        "status": "success",
        "category": category,
        "priority": priority,
        "sender_email": sender_email,
        "suggested_reply": suggested_reply,
        "detected_intent": category,
        "analyzed_at": time.time()
    }
