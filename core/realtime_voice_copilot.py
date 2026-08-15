"""
JobHunt Pro — Realtime Voice & Persona Interview Copilot
Multi-persona AI mock interviewer featuring Gulf Executive, UAE Tech Director, and Global Talent Recruiter
personas with STAR framework evaluation and salary negotiation coaching.
"""

from typing import Dict, Any, List, Optional
import time
import re
import logging

logger = logging.getLogger(__name__)

INTERVIEW_PERSONAS = {
    "saudi_executive": {
        "id": "saudi_executive",
        "name": "Eng. Faisal Al-Otaibi",
        "title": "Vice President of Digital Transformation & Delivery (KSA)",
        "tone": "Authoritative, vision-focused, deeply invested in Vision 2030, local team mentoring, and execution resilience.",
        "common_questions": [
            "How do your previous technical and leadership contributions align with the strategic mandates of Saudi Vision 2030?",
            "Can you walk me through a situation where you led a complex stakeholder alignment across government or enterprise entities?",
            "How do you approach talent upskilling and knowledge transfer within high-growth engineering teams in Riyadh?"
        ]
    },
    "uae_tech_director": {
        "id": "uae_tech_director",
        "name": "Tariq Mansoor",
        "title": "Head of Engineering & AI Systems (Dubai / DIFC)",
        "tone": "Fast-paced, modern, pragmatic, focusing on architecture scalability, zero-downtime microservices, and AI adoption.",
        "common_questions": [
            "We process millions of transactions per day in Dubai. How do you design high-throughput systems that maintain sub-50ms latency?",
            "Tell me about a time an end-to-end deployment failed in production and how you orchestrated recovery and root-cause resolution.",
            "How do you balance shipping features rapidly under tight fintech deadlines with maintaining clean, maintainable architecture?"
        ]
    },
    "global_talent_partner": {
        "id": "global_talent_partner",
        "name": "Sarah Jenkins",
        "title": "Global Executive Talent Acquisition Partner",
        "tone": "Supportive, inquisitive, deeply analytical on behavioral STAR responses and cultural fit.",
        "common_questions": [
            "Give me a specific example of a time you resolved a major conflict of technical opinions within your team.",
            "What is your target total compensation expectation (Base + Housing + Bonus) for this position?",
            "Where do you see your technical trajectory evolving over the next 3 to 5 years?"
        ]
    }
}


class RealtimeVoiceCopilot:
    """Realtime Multi-Persona AI Interviewer & Assessment Engine."""

    def get_personas(self) -> List[Dict[str, Any]]:
        """Return available recruiter personas."""
        return list(INTERVIEW_PERSONAS.values())

    def start_persona_session(self, persona_id: str, candidate_role: str, experience_level: str = "Senior") -> Dict[str, Any]:
        """Start a personalized interview simulation with a selected persona."""
        persona = INTERVIEW_PERSONAS.get(persona_id, INTERVIEW_PERSONAS["saudi_executive"])
        initial_q = persona["common_questions"][0]

        session_id = f"copilot_{persona_id}_{int(time.time())}"

        return {
            "session_id": session_id,
            "persona": {
                "id": persona["id"],
                "name": persona["name"],
                "title": persona["title"],
                "tone": persona["tone"]
            },
            "candidate_role": candidate_role,
            "experience_level": experience_level,
            "opening_greeting": f"Marhaba / Welcome! I am {persona['name']}, {persona['title']}. We are evaluating leaders for our {candidate_role} opening.",
            "first_question": initial_q,
            "audio_stream_endpoint": f"/api/voice-interview/stream-audio?session={session_id}&q=0"
        }

    def evaluate_star_answer(self, candidate_answer: str, persona_id: str = "saudi_executive") -> Dict[str, Any]:
        """Evaluate a candidate's answer against the STAR framework and provide coaching."""
        text = candidate_answer.lower()
        words = candidate_answer.split()
        word_count = len(words)

        # Detect STAR components
        has_situation = any(k in text for k in [
            "when", "at my previous", "in my previous", "previous role", "in my role", "at my", "our team",
            "we were facing", "situation", "background", "context", "faced with", "company was"
        ])
        has_task = any(k in text for k in [
            "my objective", "my task", "the task", "goal", "responsible for", "needed to", "required to",
            "target was", "challenge was", "aimed to"
        ])
        has_action = any(k in text for k in [
            "i implemented", "i designed", "i built", "i led", "i architected", "i migrated", "we utilized",
            "i developed", "i refactored", "i optimized", "i created", "i spearheaded"
        ])
        has_result = any(k in text for k in [
            "resulting in", "achieved", "increased", "decreased", "saved", "%", "revenue", "improved",
            "delivered", "reduced", "boosted", "scaled", "successfully"
        ])

        star_score = (int(has_situation) + int(has_task) + int(has_action) + int(has_result)) * 25

        # Score calculation
        clarity_score = min(100, max(60, int(word_count * 0.8) + 40)) if word_count < 150 else 95
        overall_score = int((star_score * 0.7) + (clarity_score * 0.3))

        coaching_tips = []
        if not has_result:
            coaching_tips.append("Include specific quantifiable business metrics (e.g. 'reduced latency by 35%' or 'saved $50k').")
        if not has_action:
            coaching_tips.append("Specify what YOU personally did (use 'I designed / I orchestrated') rather than generic team actions.")
        if word_count < 35:
            coaching_tips.append("Elaborate with deeper technical context and challenges overcome.")

        if not coaching_tips:
            coaching_tips.append("Excellent structured delivery! Your STAR structure is clear and persuasive.")

        return {
            "overall_score": overall_score,
            "star_breakdown": {
                "situation_detected": has_situation,
                "task_detected": has_task,
                "action_detected": has_action,
                "result_detected": has_result,
                "star_completion_percentage": star_score
            },
            "word_count": word_count,
            "clarity_score": clarity_score,
            "coaching_feedback": coaching_tips,
            "persona_feedback": f"Response evaluated by {INTERVIEW_PERSONAS.get(persona_id, INTERVIEW_PERSONAS['saudi_executive'])['name']}."
        }


# Global singleton instance
realtime_voice_copilot = RealtimeVoiceCopilot()
