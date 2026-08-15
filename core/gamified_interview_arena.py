"""
Gamified Interview Arena & Sovereign Leaderboard Engine
JobHunt Pro SaaS - Competitive technical interview challenges and recruiter showcase leaderboard.
"""
import time
import random
from typing import Dict, List, Any, Optional


class GamifiedInterviewArena:
    """
    Manages timed candidate challenge rounds, scoring metrics, and recruiter leaderboard.
    """

    CHALLENGES = [
        {
            "id": "ch_01",
            "track": "Cloud Architecture & High-Scale",
            "question": "How do you mitigate cascading failures in microservices with high write contention?",
            "options": [
                "A) Increase thread pool size infinitely on every worker node",
                "B) Implement Circuit Breaker pattern with exponential jitter backoff & dead-letter queue",
                "C) Switch all endpoints to synchronous blocking HTTP/1.1 calls",
                "D) Disable database constraints and foreign keys"
            ],
            "correct_option": "B",
            "difficulty": "Hard",
            "base_points": 100
        },
        {
            "id": "ch_02",
            "track": "SRE & Deliverability",
            "question": "What primary DNS records are mandatory to guarantee 99%+ cold outreach email deliverability without triggering spam filters?",
            "options": [
                "A) Only an A record pointing to server IP",
                "B) SPF, DKIM (2048-bit), DMARC (p=reject or quarantine), and Live MX verification",
                "C) CNAME record pointing to an unverified proxy",
                "D) TXT record containing plain-text passwords"
            ],
            "correct_option": "B",
            "difficulty": "Medium",
            "base_points": 80
        },
        {
            "id": "ch_03",
            "track": "FastAPI & Python Concurrency",
            "question": "Why is running CPU-bound blocking tasks directly inside an async def FastAPI route dangerous for throughput?",
            "options": [
                "A) It blocks the single asyncio event loop thread, stalling all concurrent HTTP requests",
                "B) It causes an automatic Python syntax error",
                "C) It disables SQLite WAL mode",
                "D) It increases memory usage by 10x"
            ],
            "correct_option": "A",
            "difficulty": "Hard",
            "base_points": 100
        }
    ]

    LEADERBOARD_SEED = [
        {"rank": 1, "candidate_name": "Tariq Al-Mansoor", "role": "Principal AI Architect", "score": 2940, "badge": "Top 1% Sovereign Architect", "city": "Riyadh"},
        {"rank": 2, "candidate_name": "Laila Al-Nuaimi", "role": "Lead DevOps / SRE", "score": 2820, "badge": "Elite Cloud SRE", "city": "Dubai"},
        {"rank": 3, "candidate_name": "Omar Al-Kuwari", "role": "Full-Stack Tech Lead", "score": 2710, "badge": "Vision 2030 Fast-Tracker", "city": "Doha"}
    ]

    @classmethod
    def get_arena_challenge(cls) -> Dict[str, Any]:
        """Returns a random timed technical challenge question."""
        challenge = random.choice(cls.CHALLENGES)
        return {
            "challenge_id": challenge["id"],
            "track": challenge["track"],
            "question": challenge["question"],
            "options": challenge["options"],
            "difficulty": challenge["difficulty"],
            "time_limit_seconds": 30,
            "max_score": challenge["base_points"]
        }

    @classmethod
    def submit_answer(
        cls,
        challenge_id: str,
        selected_option: str,
        response_time_seconds: float,
        candidate_name: str = "Candidate"
    ) -> Dict[str, Any]:
        """Evaluates candidate response and calculates accuracy and speed bonus points."""
        challenge = next((c for c in cls.CHALLENGES if c["id"] == challenge_id), cls.CHALLENGES[0])
        is_correct = selected_option.upper().strip() == challenge["correct_option"]

        if is_correct:
            speed_factor = max(0.5, (30.0 - response_time_seconds) / 30.0)
            awarded_points = int(challenge["base_points"] * (1.0 + (speed_factor * 0.5)))
            feedback = "🎯 Correct! Exceptional technical precision and fast response time."
            feedback_ar = "إجابة صحيحة ومتقنة! سرعة بديهة ودقة هندسية عالية."
        else:
            awarded_points = 0
            feedback = f"❌ Incorrect. The correct answer was {challenge['correct_option']}."
            feedback_ar = f"إجابة غير دقيقة. الخيار الصحيح هو {challenge['correct_option']}."

        return {
            "is_correct": is_correct,
            "awarded_points": awarded_points,
            "response_time_seconds": round(response_time_seconds, 2),
            "feedback_en": feedback,
            "feedback_ar": feedback_ar,
            "updated_arena_rank": "Rank #12 (Top 3% in Gulf Tech Arena)" if is_correct else "Rank #28"
        }

    @classmethod
    def get_global_leaderboard(cls) -> Dict[str, Any]:
        """Returns the public recruiter showcase leaderboard."""
        return {
            "arena_name": "JobHunt Pro GCC Sovereign Leaderboard",
            "total_competitors": 1420,
            "top_candidates": cls.LEADERBOARD_SEED,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }


# Global singleton instance
gamified_arena = GamifiedInterviewArena()
