"""
Intent Signal Detector & Job Score Analyzer
Extracts high-intent signals (urgent hiring, fast turnaround, executive budget)
from job descriptions, companies, and recruiter postings.
"""

import re
from typing import Dict, Any, List

URGENT_KEYWORDS = [
    "urgent", "urgently", "immediate", "immediately", "asap",
    "fast-track", "hiring now", "join immediately", "فوري", "مطلوب فورا", "مستعجل"
]

DECISION_MAKER_TITLES = [
    "founder", "co-founder", "ceo", "cto", "cpo", "vp of engineering",
    "head of talent", "talent acquisition", "hr manager", "recruiter",
    "مدير التوظيف", "الموارد البشرية"
]

class IntentDetector:
    @staticmethod
    def calculate_intent_score(job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates an intent score (0-100) based on urgency, recruiter authority,
        recency, and compensation clarity.
        """
        title = str(job_data.get("title", "")).lower()
        description = str(job_data.get("description", "")).lower()
        contact_name = str(job_data.get("contact_name", "")).lower()
        contact_title = str(job_data.get("contact_title", "")).lower()
        source = str(job_data.get("source", "")).lower()

        score = 50  # Baseline score
        signals = []

        # Check for urgency keywords in title or description
        for kw in URGENT_KEYWORDS:
            if kw in title or kw in description:
                score += 20
                signals.append(f"urgency_keyword:{kw}")
                break

        # Check for direct Decision Maker involvement
        for dmt in DECISION_MAKER_TITLES:
            if dmt in contact_title or dmt in contact_name:
                score += 15
                signals.append(f"decision_maker:{dmt}")
                break

        # Check for salary/compensation transparency
        if any(term in description for term in ["$", "aed", "sar", "kwd", "usd", "salary", "راتب", "مكافأة"]):
            score += 10
            signals.append("salary_transparency")

        # Cap score between 0 and 100
        final_score = min(100, max(10, score))
        
        tier = "HIGH_INTENT" if final_score >= 80 else ("MEDIUM_INTENT" if final_score >= 60 else "STANDARD")

        return {
            "intent_score": final_score,
            "intent_tier": tier,
            "signals": signals,
            "is_priority_lead": final_score >= 75
        }

    @staticmethod
    def classify_reply_intent(subject: str, body: str, language: str = "en") -> Dict[str, Any]:
        """
        Autonomous NLP Classifier for inbound recruiter responses.
        Categorizes replies into actionable business states:
        - INTERVIEW_INVITE: Urgent high-value opportunity
        - SALARY_INQUIRY: Compensation alignment phase
        - FORWARDED_TO_TEAM: Internal circulation
        - POLITE_REJECTION: Archive lead gracefully
        - AUTO_REPLY_BOUNCE: Out of office / Vacation responder
        """
        combined = f"{subject} {body}".lower()
        
        # 1. Interview Invite Detection
        interview_kw = [
            "interview", "schedule a call", "zoom", "google meet", "teams meeting", "phone screen",
            "availability", "free for a call", "speak with", "chat this week", "meet you",
            "مقابلة", "تحديد موعد", "مكالمة هاتفية", "لقاء تعريفي", "اجتماع", "شاغر مناسب"
        ]
        if any(kw in combined for kw in interview_kw):
            return {
                "intent": "INTERVIEW_INVITE",
                "urgency": "CRITICAL",
                "sentiment": "POSITIVE",
                "recommended_action": "SEND_CALENDAR_LINK",
                "suggested_reply": "Thank you for reaching out! I would be delighted to connect. I am available at your convenience. Looking forward to our conversation.",
                "suggested_reply_ar": "شكراً جزيلاً لتواصلكم الكريم. يسعدني ويشرفني عقد اللقاء في الموعد الذي يناسبكم. بانتظار تأكيد التفاصيل."
            }

        # 2. Salary / Rate Inquiry
        salary_kw = [
            "salary expectation", "expected salary", "current ctc", "rate", "compensation",
            "notice period", "budget", "الراتب المتوقع", "فترة الإشعار", "توقعات الراتب"
        ]
        if any(kw in combined for kw in salary_kw):
            return {
                "intent": "SALARY_INQUIRY",
                "urgency": "HIGH",
                "sentiment": "POSITIVE",
                "recommended_action": "CONFIRM_COMPENSATION_RANGE",
                "suggested_reply": "Thank you for checking! My compensation expectations align with standard market rates for senior roles, and I am flexible based on the complete package and growth scope.",
                "suggested_reply_ar": "شكراً لاستفساركم. توقعاتي المالية متوافقة مع متوسطات السوق للأدوار المتقدمة، مع مرونة تامة وفقاً لمزايا الدور والمسار المهني."
            }

        # 3. Forwarded to Team
        forward_kw = [
            "forwarded your resume", "passed to hiring manager", "sharing with the team",
            "shared with the lead", "under review with engineering", "أحيلت السيرة", "تم التحويل للإدارة"
        ]
        if any(kw in combined for kw in forward_kw):
            return {
                "intent": "FORWARDED_TO_TEAM",
                "urgency": "MEDIUM",
                "sentiment": "NEUTRAL_POSITIVE",
                "recommended_action": "SCHEDULE_AUTO_FOLLOWUP_3DAYS",
                "suggested_reply": "Thank you for forwarding my profile to the team! I look forward to hearing their feedback.",
                "suggested_reply_ar": "شكراً جزيلاً لتحويل ملفي إلى الفريق المعني. كلي تطلع للتواصل معهم قريباً."
            }

        # 4. Out of Office / Vacation Responder
        ooo_kw = [
            "out of office", "auto-reply", "automated response", "away on leave",
            "vacation responder", "i am currently out", "إجازة سنوية", "رد آلي"
        ]
        if any(kw in combined for kw in ooo_kw):
            return {
                "intent": "AUTO_REPLY_BOUNCE",
                "urgency": "LOW",
                "sentiment": "NEUTRAL",
                "recommended_action": "RETRY_AFTER_RETURN_DATE",
                "suggested_reply": None,
                "suggested_reply_ar": None
            }

        # 5. Polite Rejection
        reject_kw = [
            "unfortunately", "other candidates", "not moving forward", "keep on file",
            "decided to pursue other", "future opportunities", "نعتذر", "شاغر مغلق", "تمنياتنا بالتوفيق"
        ]
        if any(kw in combined for kw in reject_kw):
            return {
                "intent": "POLITE_REJECTION",
                "urgency": "LOW",
                "sentiment": "NEGATIVE_POLITE",
                "recommended_action": "ARCHIVE_WITH_COOLDOWN",
                "suggested_reply": "Thank you for letting me know. I wish the team all the best and would love to stay connected for future opportunities.",
                "suggested_reply_ar": "شكراً جزيلاً لإحاطتي علماً. أتمنى لكم ولفريقكم دوام التوفيق والنجاح، ويسعدني البقاء على تواصل للفرص المستقبلية."
            }

        return {
            "intent": "GENERAL_INQUIRY",
            "urgency": "MEDIUM",
            "sentiment": "NEUTRAL",
            "recommended_action": "MANUAL_OR_AI_CUSTOM_REVIEW",
            "suggested_reply": "Thank you for your response! Please let me know if you need any additional information or portfolio samples.",
            "suggested_reply_ar": "شكراً جزيلاً لردكم. أرجو إعلامي في حال كنتم بحاجة لأي تفاصيل إضافية أو نماذج من أعمالي السابقة."
        }

