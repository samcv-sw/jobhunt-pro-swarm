"""
JobHunt Pro v3.5 - Real-Time Voice AI Interviewer Engine (v2)
Simulates realistic, low-latency voice interviews with multi-persona evaluators,
providing instant scoring, speech clarity feedback, and technical depth analysis.
"""

import time
import random
from typing import Dict, Any, List, Optional


class VoiceAIInterviewerEngine:
    PERSONAS = {
        "faang_tech_lead": {
            "name": "Alex Vance (Staff Engineer)",
            "focus": "System Design, Microservices, Data Structures, Concurrency",
            "tone": "Direct, Technical, Deep-Dive"
        },
        "hr_screener": {
            "name": "Sarah Miller (Senior Talent Acquisition)",
            "focus": "Cultural Fit, Communication, Career Trajectory, Motivation",
            "tone": "Warm, Professional, Observant"
        },
        "startup_cto": {
            "name": "David Chen (CTO)",
            "focus": "Product Velocity, Polyglot Architecture, Pragmatism, AI Integration",
            "tone": "Fast-Paced, Solution-Oriented"
        }
    }

    QUESTION_BANK = {
        "faang_tech_lead": [
            "How would you design a rate-limiter for a distributed API handling 100k requests per second?",
            "Explain how you prevent race conditions in asynchronous database updates without locking full tables.",
            "Walk me through how you optimize database index strategies for high-frequency write operations."
        ],
        "hr_screener": [
            "Tell me about a challenging project deadline you faced and how you prioritized deliverables.",
            "What drives your interest in this specific engineering role and team architecture?",
            "How do you handle technical disagreements with senior stakeholders?"
        ],
        "startup_cto": [
            "How do you decide between building a custom microservice vs using a managed serverless API?",
            "Describe how you deployed an AI model or automated pipeline to cut infrastructure costs.",
            "What is your approach to maintaining code quality while shipping features rapidly?"
        ]
    }

    def start_session(self, persona: str = "faang_tech_lead", candidate_name: str = "Candidate") -> Dict[str, Any]:
        persona_key = persona if persona in self.PERSONAS else "faang_tech_lead"
        persona_info = self.PERSONAS[persona_key]
        questions = self.QUESTION_BANK[persona_key]

        return {
            "session_id": f"voice-session-{int(time.time())}",
            "candidate_name": candidate_name,
            "interviewer": persona_info,
            "initial_question": questions[0],
            "total_questions": len(questions),
            "status": "active",
            "started_at": time.time()
        }

    def evaluate_response(
        self,
        session_id: str,
        question: str,
        transcript_text: str,
        audio_duration_sec: float = 30.0
    ) -> Dict[str, Any]:
        """
        Analyzes spoken candidate response transcript for technical depth,
        words-per-minute pacing, confidence score, and key area improvements.
        """
        words = transcript_text.split() if transcript_text else []
        word_count = len(words)
        wpm = round((word_count / (audio_duration_sec / 60.0)), 1) if audio_duration_sec > 0 else 0

        # Technical keyword analysis
        tech_keywords = {"architecture", "async", "latency", "pipeline", "distributed", "cache", "security", "testing", "scale", "db"}
        matches = [w.lower() for w in words if w.lower().strip(",.") in tech_keywords]
        tech_score = min(100, 50 + (len(matches) * 10))

        # Pacing analysis (Ideal: 120-160 WPM)
        if 110 <= wpm <= 170:
            pacing_status = "Optimal Pacing"
            pacing_score = 95
        elif wpm < 110:
            pacing_status = "Slightly Hesitant"
            pacing_score = 75
        else:
            pacing_status = "Rushed Pacing"
            pacing_score = 80

        confidence_score = round((tech_score * 0.6 + pacing_score * 0.4), 1)

        return {
            "session_id": session_id,
            "question": question,
            "transcript_summary": transcript_text[:120] + "..." if len(transcript_text) > 120 else transcript_text,
            "word_count": word_count,
            "words_per_minute": wpm,
            "pacing_status": pacing_status,
            "technical_depth_score": tech_score,
            "overall_confidence_score": confidence_score,
            "recommendation": "Strong response with solid technical terminology." if confidence_score >= 85 else "Good start. Add concrete architectural metrics to strengthen answer."
        }


voice_interviewer_engine = VoiceAIInterviewerEngine()
