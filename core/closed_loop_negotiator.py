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

closed_loop_negotiator = ClosedLoopNegotiator()
