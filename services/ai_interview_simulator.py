"""Autonomous AI Interview Simulator for JobHunt Pro.

Generates role-specific behavioral and technical interview questions,
evaluates responses against STAR metrics and technical keywords, and
returns real-time actionable candidate feedback.
"""

import random
from typing import Dict, List


class AIInterviewSimulator:
    """Mock interview question generator and automated evaluation engine."""

    QUESTION_BANK: Dict[str, List[Dict[str, str]]] = {
        "Software Engineer": [
            {
                "id": "se_1",
                "question": "Describe a time you diagnosed and fixed a critical performance bottleneck in a web production environment.",
                "type": "technical",
                "key_concepts": ["monitoring", "profiling", "database", "caching", "root cause"]
            },
            {
                "id": "se_2",
                "question": "How do you handle architectural disagreements with senior team members regarding microservices vs monoliths?",
                "type": "behavioral",
                "key_concepts": ["trade-offs", "communication", "data-driven", "compromise"]
            },
            {
                "id": "se_3",
                "question": "Explain how you ensure API security, parameter sanitization, and rate limiting in high-throughput endpoints.",
                "type": "technical",
                "key_concepts": ["jwt", "oauth", "rate limiting", "sanitization", "cors"]
            }
        ],
        "Product Manager": [
            {
                "id": "pm_1",
                "question": "How do you prioritize competing feature requests from high-value enterprise clients vs technical debt?",
                "type": "behavioral",
                "key_concepts": ["roadmap", "roi", "metrics", "stakeholder management"]
            },
            {
                "id": "pm_2",
                "question": "Walk me through how you launch an MVP, measure initial user retention, and iterate based on telemetry.",
                "type": "technical",
                "key_concepts": ["kpi", "analytics", "user feedback", "a/b testing"]
            }
        ],
        "General": [
            {
                "id": "gen_1",
                "question": "Tell me about a challenging project where specifications changed mid-flight and how you adapted.",
                "type": "behavioral",
                "key_concepts": ["flexibility", "agility", "communication", "delivery"]
            }
        ]
    }

    @classmethod
    def generate_interview_session(cls, job_title: str = "Software Engineer", num_questions: int = 3) -> List[Dict[str, str]]:
        """Generate a custom set of interview questions for a target role."""
        pool = cls.QUESTION_BANK.get(job_title, cls.QUESTION_BANK["Software Engineer"]) + cls.QUESTION_BANK["General"]
        selected = random.sample(pool, min(num_questions, len(pool)))
        return [
            {
                "id": q["id"],
                "question": q["question"],
                "type": q["type"]
            }
            for q in selected
        ]

    @classmethod
    def evaluate_response(cls, question_id: str, candidate_answer: str, key_concepts: List[str] | None = None) -> Dict:
        """Evaluate a candidate's answer based on length, keyword coverage, and STAR structure."""
        if not candidate_answer or len(candidate_answer.strip()) < 15:
            return {
                "score": 20.0,
                "feedback": "Response is too brief. Provide specific details using the STAR method (Situation, Task, Action, Result).",
                "concepts_covered": [],
                "star_structure_detected": False
            }

        answer_lower = candidate_answer.lower()

        # Lookup concepts from question bank if not provided
        concepts = key_concepts
        if not concepts:
            for category in cls.QUESTION_BANK.values():
                for q in category:
                    if q["id"] == question_id:
                        concepts = q["key_concepts"]
                        break
                if concepts:
                    break
        
        if not concepts:
            concepts = ["situation", "task", "action", "result", "performance", "database", "query", "caching", "solution", "team", "impact", "metric"]

        covered = [concept for concept in concepts if concept in answer_lower]
        concept_score = (len(covered) / max(len(concepts), 1)) * 40.0

        # Check STAR indicators
        star_words = ["situation", "task", "action", "result", "led to", "achieved", "solved", "implemented"]
        star_matches = [w for w in star_words if w in answer_lower]
        star_score = min(len(star_matches) * 10.0, 40.0)
        star_bonus = 10.0 if len(set(star_matches).intersection({"situation", "task", "action", "result"})) >= 3 else 0.0

        # Length score
        words = len(candidate_answer.split())
        length_score = min(words / 35.0 * 20.0, 20.0)

        total_score = round(min(concept_score + star_score + length_score + star_bonus, 100.0), 1)

        if total_score >= 80:
            feedback = "Excellent response! Clear structure, relevant technical depth, and quantifiable impact."
        elif total_score >= 50:
            feedback = "Good answer. Try to emphasize quantifiable results and specific technical choices more clearly."
        else:
            feedback = "Satisfactory start. Focus on detailing your personal action and measurable outcomes."

        return {
            "score": total_score,
            "feedback": feedback,
            "concepts_covered": covered,
            "star_structure_detected": len(star_matches) >= 2
        }
