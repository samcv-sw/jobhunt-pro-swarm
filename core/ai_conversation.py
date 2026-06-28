"""
AI-Powered Recruiter Conversation Engine
Inspired by BOSS直聘's AI conversation flow — auto-crafts personalized
messages and continues conversations with recruiters on autopilot.

Features:
  - AI-generated personalized greeting messages
  - Smart reply suggestions based on recruiter messages
  - Sentiment analysis of recruiter responses
  - Conversation quality tracking
  - Follow-up scheduling
  - Telegram command hook (/converse)
  - FastAPI integration helpers
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────

# Must be set via GROQ_API_KEY environment variable (no hardcoded fallback)
DEFAULT_GROQ_KEY = os.getenv("GROQ_API_KEY", "")
DEFAULT_MODEL = "mixtral-8x7b-32768"

# Positive sentiment keywords
POSITIVE_WORDS = {
    "great", "excellent", "interested", "impressive", "perfect",
    "good fit", "schedule", "interview", "proceed", "forward",
    "looking forward", "pleased", "happy", "wonderful", "amazing",
    "outstanding", "strong", "qualified", "potential", "next step",
    "call", "meeting", "discuss", "definitely", "absolutely",
    "yes", "sure", "let's", "congratulations", "offer",
}

# Negative sentiment keywords
NEGATIVE_WORDS = {
    "unfortunately", "not interested", "overqualified", "underqualified",
    "rejected", "no longer", "sorry", "cannot", "unable",
    "regret", "decline", "passed", "not a match", "not fit",
    "other candidates", "not the right", "decided to move forward with",
    "unfortunately, we", "not selected", "not proceed",
}

# Recruitment stages for conversation flow
RECRUITMENT_STAGES = [
    "initial_contact",      # First message sent
    "screening",            # Basic qualification questions
    "technical_discussion", # Deep tech/role conversation
    "interview_scheduling",  # Setting up interview
    "interview_scheduled",  # Confirmed interview
    "follow_up",            # Post-interview follow-up
    "offer_negotiation",    # Salary/offer stage
    "offer_accepted",       # Hired
    "rejected",             # Not moving forward
]


# ═══════════════════════════════════════════════════════════════════════════════
#  AIConversationEngine
# ═══════════════════════════════════════════════════════════════════════════════

class AIConversationEngine:
    """
    AI-powered recruiter messaging engine.

    Handles:
      - Auto-generated personalized greetings
      - Smart reply suggestions based on recruiter's message
      - Sentiment analysis of recruiter responses
      - Conversation history and quality tracking
      - Follow-up timing recommendations

    Usage:
        engine = AIConversationEngine(groq_key="your_key")
        greeting = engine.generate_greeting(
            recruiter_name="John",
            company="Google",
            position="Network Engineer",
            candidate_name="Sam Salameh",
            candidate_skills=["Cisco", "Fortinet", "AWS"]
        )
    """

    def __init__(self, groq_key: str = ""):
        self.groq_key = groq_key or os.getenv("GROQ_API_KEY", "") or DEFAULT_GROQ_KEY
        self.model = DEFAULT_MODEL

        # Per-recruiter conversation history
        # { recruiter_id: [ { role, content, timestamp, sentiment? }, ... ] }
        self.conversation_history: Dict[str, List[Dict]] = defaultdict(list)

        # Track conversation stage per recruiter
        self.conversation_stages: Dict[str, str] = {}
        self.conversation_started: Dict[str, datetime] = {}
        self.last_message_at: Dict[str, datetime] = {}

    # ── Greeting Generation ─────────────────────────────────────────────────

    def generate_greeting(
        self,
        recruiter_name: str,
        company: str,
        position: str,
        candidate_name: str = "Sam Salameh",
        candidate_skills: Optional[List[str]] = None,
        job_url: str = "",
        years_of_experience: Optional[int] = None,
    ) -> str:
        """
        Generate a personalized greeting message for a recruiter.

        Falls back to template if AI is unavailable.
        """
        skills = candidate_skills or []
        skills_str = ", ".join(skills[:3]) if skills else "relevant experience"
        skills_all = ", ".join(skills[:5]) if skills else "relevant experience"
        exp_years = years_of_experience if years_of_experience is not None else 5

        if self.groq_key:
            ai_msg = self._ai_generate_greeting(
                recruiter_name, company, position,
                candidate_name, skills,
            )
            if ai_msg:
                return ai_msg

        # Default high-quality template (multiple variants)
        templates = [
            f"Hello {recruiter_name}, I came across the {position} opening at {company} "
            f"and I'm very interested. With my background in {skills_str} and {exp_years}+ years "
            f"of hands-on experience, I believe I'd be a great fit. I've submitted my application "
            f"and would love to connect further. Looking forward to hearing from you!",

            f"Hi {recruiter_name}, I'm excited about the {position} role at {company}. "
            f"My expertise in {skills_str} and proven track record in this space align well "
            f"with what you're looking for. I'd appreciate the opportunity to discuss how "
            f"I can contribute to the team. Thanks!",

            f"Dear {recruiter_name}, I'm {candidate_name}, a Network Engineer specialized "
            f"in {skills_str}. The {position} position at {company} caught my attention "
            f"because it matches my career trajectory. I've applied via the portal and would "
            f"love to chat about how my skills can benefit your organization.",
        ]

        import random
        return random.choice(templates)

    def _ai_generate_greeting(
        self,
        recruiter_name: str,
        company: str,
        position: str,
        candidate_name: str,
        candidate_skills: List[str],
    ) -> Optional[str]:
        """Use AI to generate a highly personalized greeting message."""
        skills_str = ", ".join(candidate_skills[:5]) if candidate_skills else "networking"
        prompt = (
            f"Generate a professional, personalized LinkedIn message (max 300 characters) "
            f"from {candidate_name} to {recruiter_name} at {company} "
            f"for the {position} role. "
            f"Skills: {skills_str}. "
            f"Make it specific, not generic. Sound enthusiastic but professional. "
            f"Return ONLY the message text, no quotes, no prefix."
        )

        try:
            import httpx
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 200,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                msg = resp.json()["choices"][0]["message"]["content"].strip()
                # Clean quotes if present
                msg = msg.strip('"\'')
                return msg
            else:
                logger.warning(
                    f"[AI-Greeting] API returned {resp.status_code}"
                )
        except Exception as e:
            logger.warning(f"[AI-Greeting] AI failed, using template: {e}")

        return None

    # ── Reply Suggestions ───────────────────────────────────────────────────

    def suggest_reply(
        self,
        recruiter_message: str,
        context: Optional[Dict] = None,
        recruiter_id: str = "",
    ) -> Dict:
        """
        AI suggests a reply to a recruiter's message.

        Returns a dict with:
            - reply: Suggested reply text
            - sentiment: Detected sentiment of recruiter message
            - suggested_action: What the candidate should do next
            - confidence: Confidence score (0-1)
        """
        context = context or {}

        # First, analyze sentiment
        sentiment = self.analyze_sentiment(recruiter_message)

        prompt = f"""Recruiter message: "{recruiter_message}"

Candidate profile: {json.dumps(context, indent=2) if context else "Network Engineer with Cisco, Fortinet, MikroTik experience"}

Sentiment of recruiter message: {sentiment['sentiment']}

Suggest a professional reply (max 150 words) that:
1. Directly addresses the recruiter's question or comment
2. Reinforces the candidate's strengths relevant to the conversation
3. Moves the conversation forward (toward interview or next step)

Return ONLY the reply text, no explanations or prefixes."""

        default_reply = (
            "Thank you for your message. I'm very interested in this opportunity "
            "and would love to discuss how my background aligns with your needs. "
            "Could we schedule a brief call to explore next steps?"
        )

        try:
            import httpx
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5,
                    "max_tokens": 300,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"].strip()
            else:
                logger.warning(f"[AI-Reply] API returned {resp.status_code}")
                reply = default_reply
        except Exception as e:
            logger.warning(f"[AI-Reply] Error: {e}")
            reply = default_reply

        # Determine suggested action
        if sentiment["sentiment"] == "positive":
            suggested_action = "schedule_interview"
        elif sentiment["sentiment"] == "neutral":
            suggested_action = "send_follow_up"
        else:
            suggested_action = "move_to_other_leads"

        # If recruiter asks a direct question, always reply
        if "?" in recruiter_message:
            suggested_action = "answer_question"

        return {
            "reply": reply,
            "sentiment": sentiment["sentiment"],
            "sentiment_score": sentiment["score"],
            "suggested_action": suggested_action,
            "confidence": sentiment.get("confidence", 0.5),
        }

    # ── Follow-up Suggestion ───────────────────────────────────────────────

    def suggest_follow_up(
        self,
        recruiter_id: str,
        days_since_last: int = 3,
    ) -> Optional[Dict]:
        """
        Suggest a follow-up message if enough time has passed since last contact.
        Returns None if follow-up isn't needed yet.
        """
        history = self.conversation_history.get(recruiter_id, [])
        if len(history) < 2:
            return None

        last_msg = history[-1]
        last_role = last_msg.get("role", "")
        last_content = last_msg.get("content", "")

        # Don't follow up if they already replied recently
        if last_role == "recruiter" and days_since_last < 3:
            return None

        # Generate follow-up based on last message
        prompt = f"""Write a polite follow-up message (max 100 words) for a job application.
Last message from the conversation was: "{last_content[:200]}"
It's been {days_since_last} days.
The message should be professional, not pushy, and express continued interest.
Return ONLY the message text."""

        try:
            import httpx
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.6,
                    "max_tokens": 200,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                msg = resp.json()["choices"][0]["message"]["content"].strip()
                return {
                    "follow_up": msg,
                    "days_since_last": days_since_last,
                    "conversation_length": len(history),
                }
        except Exception as e:
            logger.warning(f"[AI-FollowUp] Error: {e}")

        return None

    # ── Sentiment Analysis ─────────────────────────────────────────────────

    def analyze_sentiment(self, message: str) -> Dict:
        """
        Analyze recruiter message sentiment using keyword matching.
        Returns sentiment label, score, and suggested action.

        Also tries AI-powered analysis for more nuanced results.
        """
        msg_lower = message.lower()

        # Keyword-based analysis (fast, always available)
        positive_count = sum(
            1 for w in POSITIVE_WORDS if w in msg_lower
        )
        negative_count = sum(
            1 for w in NEGATIVE_WORDS if w in msg_lower
        )

        net = positive_count - negative_count
        total = positive_count + negative_count

        if total == 0:
            sentiment = "neutral"
            confidence = 0.3
        elif net > 0:
            sentiment = "positive"
            confidence = min(0.5 + (net / total) * 0.5, 1.0)
        elif net < 0:
            sentiment = "negative"
            confidence = min(0.5 + (abs(net) / total) * 0.5, 1.0)
        else:
            sentiment = "neutral"
            confidence = 0.5

        # AI-powered sentiment (more nuanced)
        if self.groq_key and len(message) > 20:
            ai_sentiment = self._ai_analyze_sentiment(message)
            if ai_sentiment:
                # Prefer AI analysis when available
                return ai_sentiment

        return {
            "sentiment": sentiment,
            "score": net,
            "confidence": round(confidence, 2),
            "keyword_counts": {
                "positive": positive_count,
                "negative": negative_count,
            },
            "should_follow_up": sentiment != "negative",
            "suggested_action": (
                "schedule_interview" if sentiment == "positive"
                else "send_follow_up" if sentiment == "neutral"
                else "move_to_other_leads"
            ),
        }

    def _ai_analyze_sentiment(self, message: str) -> Optional[Dict]:
        """Use AI for deeper sentiment analysis."""
        prompt = (
            f"Analyze the sentiment of this recruiter message. "
            f"Return JSON: {{\"sentiment\": \"positive|negative|neutral|interested|not_interested\", "
            f"\"score\": <integer -5 to 5>, \"confidence\": <0.0-1.0>, "
            f"\"should_follow_up\": <bool>, \"suggested_action\": \"<action>\"}}\n\n"
            f"Message: \"{message[:500]}\""
        )

        try:
            import httpx
            resp = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 200,
                },
                timeout=10,
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        except Exception as e:
            logger.debug(f"[AI-Sentiment] AI failed: {e}")

        return None

    # ── Conversation Management ────────────────────────────────────────────

    def track_message(
        self,
        recruiter_id: str,
        role: str,  # "candidate" or "recruiter"
        content: str,
        sentiment: Optional[Dict] = None,
    ) -> None:
        """Record a message in the conversation history."""
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        }
        if sentiment:
            entry["sentiment"] = sentiment

        self.conversation_history[recruiter_id].append(entry)
        self.last_message_at[recruiter_id] = datetime.now()

        # Set initial stage
        if recruiter_id not in self.conversation_stages:
            self.conversation_stages[recruiter_id] = "initial_contact"
            self.conversation_started[recruiter_id] = datetime.now()

    def get_conversation_summary(self, recruiter_id: str) -> Dict:
        """Get a summary of the conversation with a recruiter."""
        history = self.conversation_history.get(recruiter_id, [])
        if not history:
            return {"status": "no_conversation"}

        stage = self.conversation_stages.get(recruiter_id, "unknown")
        started = self.conversation_started.get(recruiter_id)
        last_msg = self.last_message_at.get(recruiter_id)

        # Calculate average sentiment
        sentiments = [
            m.get("sentiment", {}).get("score", 0)
            for m in history
            if m.get("sentiment")
        ]
        avg_sentiment = round(
            sum(sentiments) / max(len(sentiments), 1), 2
        ) if sentiments else 0

        # Determine last action needed
        last_role = history[-1]["role"] if history else "candidate"
        needs_reply = last_role == "recruiter"
        days_idle = (
            (datetime.now() - last_msg).days
            if last_msg else 0
        ) if last_msg else 0

        return {
            "recruiter_id": recruiter_id,
            "stage": stage,
            "message_count": len(history),
            "avg_sentiment": avg_sentiment,
            "needs_reply": needs_reply,
            "days_since_last_message": days_idle,
            "started_at": started.isoformat() if started else None,
            "last_message_at": last_msg.isoformat() if last_msg else None,
        }

    def update_stage(
        self, recruiter_id: str, new_stage: str
    ) -> bool:
        """Advance the conversation stage."""
        if new_stage in RECRUITMENT_STAGES:
            self.conversation_stages[recruiter_id] = new_stage
            return True
        logger.warning(
            f"[Conv-Stage] Unknown stage '{new_stage}'. "
            f"Valid: {RECRUITMENT_STAGES}"
        )
        return False

    def get_conversation_history(
        self, recruiter_id: str, limit: int = 20
    ) -> List[Dict]:
        """Get recent conversation history with a recruiter."""
        history = self.conversation_history.get(recruiter_id, [])
        return history[-limit:]

    def batch_conversation_status(self) -> Dict:
        """Get status snapshot of all active conversations."""
        status = {}
        for rid in self.conversation_history:
            status[rid] = self.get_conversation_summary(rid)
        return status

    # ── Export / Serialization ─────────────────────────────────────────────

    def export_conversations(self) -> Dict:
        """Export all conversations for persistence."""
        return {
            "history": dict(self.conversation_history),
            "stages": dict(self.conversation_stages),
            "started": {
                k: v.isoformat()
                for k, v in self.conversation_started.items()
            },
            "last_messages": {
                k: v.isoformat()
                for k, v in self.last_message_at.items()
            },
        }

    def import_conversations(self, data: Dict) -> None:
        """Import previously exported conversations."""
        self.conversation_history = defaultdict(
            list, data.get("history", {})
        )
        self.conversation_stages = data.get("stages", {})
        self.conversation_started = {
            k: datetime.fromisoformat(v)
            for k, v in data.get("started", {}).items()
        }
        self.last_message_at = {
            k: datetime.fromisoformat(v)
            for k, v in data.get("last_messages", {}).items()
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  Telegram Bot Command Hook
# ═══════════════════════════════════════════════════════════════════════════════

# Global engine instance (singleton pattern for Telegram bot)
_conversation_engine: Optional[AIConversationEngine] = None


def get_engine(groq_key: str = "") -> AIConversationEngine:
    """Get or create the global conversation engine."""
    global _conversation_engine
    if _conversation_engine is None:
        _conversation_engine = AIConversationEngine(groq_key=groq_key)
    return _conversation_engine


def format_conversation_for_telegram(
    recruiter_id: str,
    action: str = "status",
    message: str = "",
    engine: Optional[AIConversationEngine] = None,
) -> str:
    """
    Format conversation output for Telegram.

    Actions:
      - "status": Show all active conversations
      - "greeting": Generate a greeting for a recruiter
      - "reply": Suggest a reply to a recruiter message
    """
    eng = engine or get_engine()

    if action == "status":
        status = eng.batch_conversation_status()
        if not status:
            return "<b>💬 Conversations</b>\n\nNo active conversations yet."

        lines = ["<b>💬 Active Conversations</b>\n"]
        for rid, info in sorted(
            status.items(),
            key=lambda x: x[1].get("days_since_last_message", 999),
        ):
            emoji = "🟢" if info.get("needs_reply") else "⚪"
            lines.append(
                f"{emoji} <b>{rid}</b>\n"
                f"   Stage: {info.get('stage', 'unknown')}\n"
                f"   Messages: {info.get('message_count', 0)}\n"
                f"   Last: {info.get('days_since_last_message', 0)}d ago\n"
                f"   Sentiment: {info.get('avg_sentiment', 0)}"
            )
        return "\n".join(lines)

    elif action == "greeting":
        # Generate greeting — expects recruiter_id in format "name/company/role"
        parts = recruiter_id.split("/")
        if len(parts) < 2:
            return (
                "<b>❌ Greeting Error</b>\n\n"
                "Usage: /converse greeting <name>/<company>/<role>"
            )
        name = parts[0]
        company = parts[1]
        role = parts[2] if len(parts) > 2 else "position"

        greeting = eng.generate_greeting(
            recruiter_name=name,
            company=company,
            position=role,
            candidate_name="Sam Salameh",
            candidate_skills=[
                "Cisco", "Fortinet", "MikroTik", "Ubiquiti",
                "Python", "Linux", "AWS", "Cloud",
            ],
        )
        lines = [
            "<b>✉️ AI-Generated Greeting</b>\n",
            f"To: {name} at {company}\n",
            f"Role: {role}\n",
            f"───\n{greeting}\n───",
        ]
        eng.track_message(f"{name}@{company}", "candidate", greeting)
        return "\n".join(lines)

    elif action == "reply":
        if not message:
            return (
                "<b>❌ Reply Error</b>\n\n"
                "Usage: /converse reply <recruiter_message>"
            )
        suggestion = eng.suggest_reply(
            recruiter_message=message,
            context={
                "name": "Sam Salameh",
                "title": "Senior Network Engineer",
                "skills": ["Cisco", "Fortinet", "MikroTik", "AWS"],
            },
        )
        emoji_map = {
            "positive": "🟢",
            "negative": "🔴",
            "neutral": "🟡",
        }
        sent_emoji = emoji_map.get(suggestion["sentiment"], "⚪")
        lines = [
            "<b>🤖 AI Reply Suggestion</b>\n",
            f"{sent_emoji} Sentiment: {suggestion['sentiment'].upper()}\n"
            f"   Score: {suggestion['sentiment_score']}\n",
            f"<b>Suggested Reply:</b>\n{suggestion['reply']}\n",
            f"<b>Next Action:</b> {suggestion['suggested_action']}\n",
            f"<b>Confidence:</b> {suggestion['confidence']:.0%}",
        ]
        return "\n".join(lines)

    return f"<b>❌ Unknown action:</b> {action}"


# ═══════════════════════════════════════════════════════════════════════════════
#  Batch Greeting Generator (for mass outreach)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_batch_greetings(
    recruiters: List[Dict],
    candidate_name: str = "Sam Salameh",
    candidate_skills: Optional[List[str]] = None,
    engine: Optional[AIConversationEngine] = None,
) -> List[Dict]:
    """
    Generate greetings for multiple recruiters in batch.

    Args:
        recruiters: List of dicts with keys ['name', 'company', 'position']
        candidate_name: Name of the candidate
        candidate_skills: List of candidate's skills
        engine: Existing engine instance (or creates new)

    Returns:
        List of dicts with original keys + 'greeting'
    """
    eng = engine or AIConversationEngine()
    skills = candidate_skills or [
        "Cisco", "Fortinet", "MikroTik", "Ubiquiti",
        "Python", "Linux", "AWS",
    ]

    results = []
    for recruiter in recruiters:
        greeting = eng.generate_greeting(
            recruiter_name=recruiter.get("name", "Hiring Manager"),
            company=recruiter.get("company", "Company"),
            position=recruiter.get("position", "Position"),
            candidate_name=candidate_name,
            candidate_skills=skills,
        )
        entry = {**recruiter, "greeting": greeting}
        results.append(entry)

        # Track conversation
        rid = f"{recruiter.get('name', 'unknown')}@{recruiter.get('company', 'unknown')}"
        eng.track_message(rid, "candidate", greeting)

    return results


# ═══════════════════════════════════════════════════════════════════════════════
#  FastAPI / Flask Integration Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def api_generate_greeting(
    recruiter_name: str,
    company: str,
    position: str,
    candidate_name: str = "Sam Salameh",
    candidate_skills: Optional[List[str]] = None,
    groq_key: str = "",
) -> Dict:
    """API-friendly wrapper for greeting generation."""
    eng = AIConversationEngine(groq_key=groq_key)
    greeting = eng.generate_greeting(
        recruiter_name=recruiter_name,
        company=company,
        position=position,
        candidate_name=candidate_name,
        candidate_skills=candidate_skills,
    )
    return {
        "greeting": greeting,
        "recruiter_name": recruiter_name,
        "company": company,
        "position": position,
        "generated_at": datetime.now().isoformat(),
    }


def api_suggest_reply(
    recruiter_message: str,
    context: Optional[Dict] = None,
    groq_key: str = "",
) -> Dict:
    """API-friendly wrapper for reply suggestion."""
    eng = AIConversationEngine(groq_key=groq_key)
    suggestion = eng.suggest_reply(
        recruiter_message=recruiter_message,
        context=context or {},
    )
    return suggestion


# ═══════════════════════════════════════════════════════════════════════════════
#  Quick Test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("═" * 50)
    print("AI Conversation Engine — Quick Test")
    print("═" * 50)

    eng = AIConversationEngine()

    # Test greeting
    greeting = eng.generate_greeting(
        recruiter_name="Sarah",
        company="Google",
        position="Senior Network Engineer",
        candidate_skills=["Cisco", "Fortinet", "AWS", "Python"],
    )
    print(f"\n📨 Greeting:\n{greeting}\n")

    # Track it
    eng.track_message("Sarah@Google", "candidate", greeting)

    # Test sentiment analysis
    for msg in [
        "Great profile! Would you be available for a call this week?",
        "Unfortunately, we've decided to move forward with other candidates.",
        "Thank you for your application. We'll review and get back to you.",
    ]:
        sentiment = eng.analyze_sentiment(msg)
        reply = eng.suggest_reply(msg)
        print(f"\n📩 Recruiter: {msg}")
        print(f"📊 Sentiment: {sentiment['sentiment']} (score: {sentiment['score']})")
        print(f"💬 Suggested: {reply['reply'][:80]}...")
        print(f"➡️ Action: {reply['suggested_action']}")

    # Test conversation summary
    eng.track_message("Sarah@Google", "recruiter", "Let's schedule an interview")
    summary = eng.get_conversation_summary("Sarah@Google")
    print(f"\n📋 Conversation Summary:\n{json.dumps(summary, indent=2)}")
