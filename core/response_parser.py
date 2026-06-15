"""
JobHunt Pro - Response Parser
Parse email responses and auto-reply with Calendly link for interview requests.
"""
import logging
import os
import re
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ResponseType(Enum):
    INTERVIEW = "interview"
    REJECTION = "rejection"
    FOLLOWUP = "followup"
    OFFER = "offer"
    QUESTION = "question"
    AUTO_REPLY = "auto_reply"
    SPAM = "spam"
    UNKNOWN = "unknown"


@dataclass
class ParseResult:
    response_type: ResponseType
    confidence: float
    keywords_found: list
    sentiment: str
    should_reply: bool
    reply_text: str
    calendar_link: str


CALENDLY_LINK = os.getenv("CALENDLY_LINK", "https://calendly.com/samsalameh.cv/30min")

CALENDLY_REPLY = """Dear Hiring Team,

Thank you for your response! I am delighted to hear about the opportunity to discuss my qualifications further.

I would be happy to schedule an interview at your convenience. Please feel free to book a time that works best for you using my calendar link:

{scheduling_link}

Alternatively, please let me know your preferred dates and times, and I will make myself available.

Looking forward to speaking with you.

Best regards,
Sam Salameh
Senior Network Engineer
samsalameh.cv@gmail.com
+961 71 019 053"""

FOLLOWUP_REPLY = """Dear Hiring Team,

Thank you for your response. I appreciate you getting back to me.

I remain very interested in this opportunity and am available to discuss my qualifications at your earliest convenience.

Please let me know if you need any additional information from my end.

Best regards,
Sam Salameh"""

INTERVIEW_KEYWORDS = [
    "interview", "schedule", "call", "meeting", "discuss",
    "available", "calendar", "book", "slot", "time",
    "phone screen", "phone call", "video call", "zoom",
    "teams", "google meet", "face to face", "in person",
    "next steps", "move forward", "proceed", "shortlisted",
    "selected", "impressed", "strong candidate"
]

REJECTION_KEYWORDS = [
    "unfortunately", "regret", "not selected", "not chosen",
    "position has been filled", "other candidates", "more qualified",
    "decided to move forward with", "not advancing",
    "will not be moving forward", "closing your application",
    "better fit", "not a match"
]

OFFER_KEYWORDS = [
    "offer", "congratulations", "pleased to offer",
    "salary", "compensation", "start date", "joining date",
    "welcome to the team", "accepted", "terms of employment"
]

FOLLOWUP_KEYWORDS = [
    "update", "status", "checking in", "following up",
    "still interested", "any update", "timeline"
]

AUTO_REPLY_KEYWORDS = [
    "out of office", "auto-reply", "automated",
    "on vacation", "away from office", "will respond shortly",
    "received your email", "thank you for your email"
]

SPAM_KEYWORDS = [
    "unsubscribe", "marketing", "promotion",
    "special offer", "limited time", "click here"
]


class ResponseParser:
    def __init__(self, calendly_link: str = CALENDLY_LINK):
        self.calendly_link = calendly_link
        self.interview_patterns = self._build_patterns(INTERVIEW_KEYWORDS)
        self.rejection_patterns = self._build_patterns(REJECTION_KEYWORDS)
        self.offer_patterns = self._build_patterns(OFFER_KEYWORDS)
        self.followup_patterns = self._build_patterns(FOLLOWUP_KEYWORDS)
        self.auto_reply_patterns = self._build_patterns(AUTO_REPLY_KEYWORDS)
        self.spam_patterns = self._build_patterns(SPAM_KEYWORDS)

    def _build_patterns(self, keywords: list) -> list:
        patterns = []
        for kw in keywords:
            patterns.append(re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE))
        return patterns

    def _count_matches(self, text: str, patterns: list) -> Tuple[int, list]:
        found = []
        for pattern in patterns:
            matches = pattern.findall(text)
            if matches:
                found.extend(matches)
        return len(found), found

    def parse(self, subject: str, body: str, from_email: str = "") -> ParseResult:
        text = f"{subject} {body}".lower()

        interview_count, interview_kw = self._count_matches(text, self.interview_patterns)
        rejection_count, rejection_kw = self._count_matches(text, self.rejection_patterns)
        offer_count, offer_kw = self._count_matches(text, self.offer_patterns)
        followup_count, followup_kw = self._count_matches(text, self.followup_patterns)
        auto_count, auto_kw = self._count_matches(text, self.auto_reply_patterns)
        spam_count, spam_kw = self._count_matches(text, self.spam_patterns)

        scores = {
            ResponseType.INTERVIEW: interview_count * 3,
            ResponseType.REJECTION: rejection_count * 4,
            ResponseType.OFFER: offer_count * 5,
            ResponseType.FOLLOWUP: followup_count * 2,
            ResponseType.AUTO_REPLY: auto_count * 3,
            ResponseType.SPAM: spam_count * 2,
        }

        max_type = max(scores, key=scores.get)
        max_score = scores[max_type]

        if max_score == 0:
            response_type = ResponseType.UNKNOWN
            confidence = 0.0
            keywords_found = []
        else:
            response_type = max_type
            confidence = min(max_score / 10, 1.0)
            all_kw = interview_kw + rejection_kw + offer_kw + followup_kw + auto_kw + spam_kw
            keywords_found = list(set(all_kw))

        if response_type == ResponseType.INTERVIEW:
            sentiment = "positive"
        elif response_type in (ResponseType.REJECTION, ResponseType.SPAM):
            sentiment = "negative"
        elif response_type == ResponseType.OFFER:
            sentiment = "very_positive"
        else:
            sentiment = "neutral"

        should_reply, reply_text = self._generate_reply(response_type, body, from_email)

        return ParseResult(
            response_type=response_type,
            confidence=confidence,
            keywords_found=keywords_found,
            sentiment=sentiment,
            should_reply=should_reply,
            reply_text=reply_text,
            calendar_link=self.calendly_link
        )

    def _generate_reply(self, response_type: ResponseType, body: str,
                        from_email: str) -> Tuple[bool, str]:
        if response_type == ResponseType.INTERVIEW:
            reply = CALENDLY_REPLY.format(scheduling_link=self.calendly_link)
            return True, reply

        elif response_type == ResponseType.REJECTION:
            return False, ""

        elif response_type == ResponseType.OFFER:
            reply = CALENDLY_REPLY.format(scheduling_link=self.calendly_link)
            return True, reply

        elif response_type == ResponseType.FOLLOWUP:
            return True, FOLLOWUP_REPLY

        elif response_type == ResponseType.AUTO_REPLY:
            return False, ""

        elif response_type == ResponseType.SPAM:
            return False, ""

        else:
            return False, ""

    def parse_batch(self, emails: list) -> Dict[str, int]:
        stats = {
            "total": len(emails),
            "interview": 0,
            "rejection": 0,
            "offer": 0,
            "followup": 0,
            "auto_reply": 0,
            "spam": 0,
            "unknown": 0,
            "should_reply": 0
        }

        for email in emails:
            subject = email.get("subject", "")
            body = email.get("body", "")
            from_email = email.get("from", "")

            result = self.parse(subject, body, from_email)

            stats[result.response_type.value] += 1
            if result.should_reply:
                stats["should_reply"] += 1

        return stats


class AntiGhostingFollowup:
    def __init__(self):
        self.followup_templates = [
            self._template_1,
            self._template_2,
            self._template_3,
        ]

    def _template_1(self, company: str, title: str, days: int) -> str:
        return f"""Dear {company} Hiring Team,

I hope this message finds you well. I am writing to follow up on my application for the {title} position, submitted {days} days ago.

I remain very interested in this opportunity and would appreciate any update on the status of my application.

Best regards,
Sam Salameh"""

    def _template_2(self, company: str, title: str, days: int) -> str:
        return f"""Dear Hiring Team,

I wanted to check in regarding my application for {title} at {company}.

With over 15 years of network engineering experience, I believe I could make a significant contribution to your team. I would welcome the chance to discuss my qualifications further.

Thank you for your time and consideration.

Best regards,
Sam Salameh"""

    def _template_3(self, company: str, title: str, days: int) -> str:
        return f"""Dear {company} Team,

I am reaching out to follow up on my {title} application from {days} days ago.

I understand you are likely reviewing many applications, but I wanted to reiterate my strong interest in joining your team. My experience with Cisco, MikroTik, and cloud infrastructure aligns well with this role.

Please let me know if you need any additional information.

Best regards,
Sam Salameh"""

    def get_followup(self, company: str, title: str, followup_number: int,
                     days_since_application: int) -> str:
        template_index = min(followup_number - 1, len(self.followup_templates) - 1)
        template = self.followup_templates[template_index]
        return template(company, title, days_since_application)

    def should_send_followup(self, days_since: int, followup_count: int,
                              last_response_type: str) -> bool:
        if last_response_type in ("interview", "offer", "rejection"):
            return False

        if followup_count >= 3:
            return False

        if followup_count == 0 and days_since >= 4:
            return True
        elif followup_count == 1 and days_since >= 7:
            return True
        elif followup_count == 2 and days_since >= 14:
            return True

        return False


parser = ResponseParser()
followup_engine = AntiGhostingFollowup()
