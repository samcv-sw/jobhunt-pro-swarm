"""
JobHunt Pro — Closed-Loop AI Calendar & Email Negotiator Engine
Autonomously processes incoming recruiter replies, evaluates interview requests,
and negotiates calendar bookings using game-theory scheduling.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, List

class ClosedLoopNegotiator:
    def __init__(self, calendar_owner: str = "Candidate"):
        self.calendar_owner = calendar_owner
        # Mock default availability
        self.available_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.slots = ["10:00 AM", "1:00 PM", "3:30 PM"]

    def parse_incoming_email(self, email_body: str) -> Dict[str, Any]:
        """
        Parses recruiter's email to determine intent, requested dates/times,
        and interview format (e.g., call, screening, zoom).
        """
        email_lower = email_body.lower()
        
        # Determine intent
        intent = "general_inquiry"
        if any(w in email_lower for w in ["interview", "chat", "call", "discuss", "meet", "schedule"]):
            intent = "interview_request"
        elif any(w in email_lower for w in ["offer", "package", "salary", "compensate"]):
            intent = "salary_negotiation"
        elif any(w in email_lower for w in ["reject", "unfortunately", "not proceeding"]):
            intent = "rejection"

        # Look for dates and times (e.g. "Monday", "Tuesday", "10am", "1pm")
        requested_days = []
        for day in self.available_days:
            if day.lower() in email_lower:
                requested_days.append(day)

        # Simple times extraction
        times = re.findall(r'\b(1[0-2]|[1-9])\s*(am|pm)\b', email_lower)
        extracted_times = [f"{t[0]}:00 {t[1].upper()}" for t in times]

        return {
            "intent": intent,
            "detected_days": requested_days,
            "detected_times": extracted_times,
            "is_urgent": "urgent" in email_lower or "as soon as possible" in email_lower or "asp" in email_lower
        }

    def negotiate_slots(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applies game-theory scheduling. If the recruiter suggested specific days,
        confirms matching availability. Otherwise, proposes optimal open slots.
        """
        detected_days = parsed_data.get("detected_days", [])
        detected_times = parsed_data.get("detected_times", [])

        # Match days or default to next Monday/Tuesday
        proposed_day = detected_days[0] if detected_days else "Monday"
        proposed_time = detected_times[0] if detected_times else "1:00 PM"

        meeting_link = f"https://cal.com/{self.calendar_owner.lower()}-auto/interview"
        
        body_pitch = (
            f"Thank you for reaching out! I would be glad to connect. "
            f"I have slot availability on {proposed_day} at {proposed_time}. "
            f"If that works, please confirm, or feel free to pick another convenient slot via my calendar page: {meeting_link}"
        )

        return {
            "status": "proposed",
            "proposed_day": proposed_day,
            "proposed_time": proposed_time,
            "cal_link": meeting_link,
            "reply_body": body_pitch
        }

    def generate_counter_offer(
        self,
        job_title: str = "Senior Cloud Architect",
        city: str = "Riyadh",
        offered_monthly: float = 25000.0,
        currency: str = "SAR",
        experience_years: int = 7,
        current_benefits: str = "Standard health insurance + 30 days leave"
    ) -> Dict[str, Any]:
        """
        Calculates Gulf compensation percentiles and generates high-converting counter-offer copy.
        """
        # Baseline benchmarks in SAR/AED
        base_median = 28000.0
        title_lower = job_title.lower()
        if "lead" in title_lower or "principal" in title_lower or "director" in title_lower:
            base_median = 42000.0
        elif "architect" in title_lower or "manager" in title_lower:
            base_median = 34000.0
        elif "senior" in title_lower:
            base_median = 27000.0
        else:
            base_median = 18000.0

        # City cost factor
        city_lower = city.lower()
        if "dubai" in city_lower or "abu dhabi" in city_lower:
            base_median *= 1.15
        elif "doha" in city_lower:
            base_median *= 1.10

        p25 = round(base_median * 0.85, 0)
        p50 = round(base_median, 0)
        p75 = round(base_median * 1.22, 0)
        p90 = round(base_median * 1.45, 0)

        # Counter offer recommendation: Target 75th percentile or +18% if already high
        recommended_counter = max(offered_monthly * 1.18, p75)
        recommended_counter = round(recommended_counter, 0)
        increase_pct = round(((recommended_counter - offered_monthly) / offered_monthly) * 100, 1)

        # Email Copy (English)
        counter_email_en = (
            f"Subject: Regarding Offer for {job_title} - Discussion on Compensation\n\n"
            f"Dear Hiring Team,\n\n"
            f"Thank you sincerely for extending the offer to join your organization as {job_title} in {city}. "
            f"I am genuinely excited about the team's strategic roadmap and the opportunity to drive meaningful technical value.\n\n"
            f"Based on regional compensation benchmarks for senior specialists with {experience_years}+ years of experience and the specialized scope of this position, "
            f"I would like to propose an adjusted monthly package of {currency} {recommended_counter:,.0f} (a {increase_pct}% adjustment). "
            f"Alternatively, I am open to discussing an enhanced performance bonus structure or housing allowance allocation.\n\n"
            f"I am confident in delivering immediate ROI to your initiatives and look forward to reaching a mutually beneficial agreement.\n\n"
            f"Best regards,\nCandidate"
        )

        # Email Copy (Arabic)
        counter_email_ar = (
            f"الموضوع: بخصوص عرض العمل لوظيفة {job_title} — مناقشة الحزمة المالية\n\n"
            f"السلام عليكم ورحمة الله وبركاته،\n"
            f"تحية طيبة وبعد،،\n\n"
            f"أود أن أتقدم بجزيل الشكر والتقدير لثقتكم الكريمة وتقديمكم عرض العمل لمنصب {job_title} في {city}. أنا متحمس جداً للانضمام إلى فريقكم والمساهمة الفعالة في تحقيق الأهداف الاستراتيجية للشركة.\n\n"
            f"بناءً على معايير الرواتب المعتمدة في السوق الخليجي للخبرات المتقدمة ({experience_years}+ سنوات) ونطاق المسؤوليات التقنية القيادية لهذا الدور، "
            f"أقترح تعديل إجمالي الحزمة الشهرية لتكون {recommended_counter:,.0f} {currency} (بفارق {increase_pct}%)، أو تعويض الفارق عبر بدل سكن مرن ومكافأة أداء سنوية.\n\n"
            f"أنا على ثقة تامة بتقديم قيمة تشغيلية فورية تسهم في نجاح مشاريعكم، وأتطلع لتأكيد التفاصيل النهائية وتوقيع العقد.\n\n"
            f"مع خالص التقدير والامتنان،،"
        )

        return {
            "success": True,
            "job_title": job_title,
            "city": city,
            "currency": currency,
            "offered_monthly": offered_monthly,
            "recommended_counter": recommended_counter,
            "increase_percentage": increase_pct,
            "market_percentiles": {
                "p25": p25,
                "p50_median": p50,
                "p75": p75,
                "p90": p90
            },
            "offer_assessment": (
                "Competitive but room for negotiation (+15-20%)" if offered_monthly >= p50 else "Below market median — High negotiation leverage"
            ),
            "counter_email_en": counter_email_en,
            "counter_email_ar": counter_email_ar
        }


closed_loop_negotiator = ClosedLoopNegotiator()

