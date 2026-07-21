"""
Real-Time Voice & Multi-Modal Mock Interview Engine
Processes audio transcripts, speech pace, filler words, and delivers instant audio feedback.
"""
from typing import Dict, Any, List
import re

class RealtimeVoiceInterviewEngine:
    """
    Evaluates real-time candidate audio transcripts and speech signals.
    """

    FILLER_WORDS = ["um", "uh", "like", "you know", "basically", "actually"]

    def analyze_audio_chunk_transcript(self, transcript: str, duration_seconds: float = 10.0) -> Dict[str, Any]:
        """
        Analyzes a segment of spoken transcript for pace, filler word density, and clarity.
        """
        words = re.findall(r'\b\w+\b', transcript.lower())
        word_count = len(words)
        
        # Pace calculation: Words Per Minute (WPM)
        wpm = (word_count / max(duration_seconds, 1.0)) * 60.0

        # Filler words count
        filler_count = sum(1 for w in words if w in self.FILLER_WORDS)
        filler_ratio = (filler_count / max(word_count, 1)) * 100.0

        # Clarity & Confidence scoring
        clarity_score = 100.0
        if wpm < 100 or wpm > 180:
            clarity_score -= 15.0
        if filler_ratio > 10.0:
            clarity_score -= 20.0
        elif filler_ratio > 5.0:
            clarity_score -= 10.0

        clarity_score = max(0.0, clarity_score)

        feedback = []
        if wpm < 100:
            feedback.append("Try speaking slightly faster to convey confidence.")
        elif wpm > 180:
            feedback.append("Slow down slightly to improve articulation.")
        
        if filler_count > 0:
            feedback.append(f"Detected {filler_count} filler word(s). Try pausing silently instead.")
        
        if not feedback:
            feedback.append("Excellent pace and clear delivery!")

        return {
            "transcript": transcript,
            "word_count": word_count,
            "wpm": round(wpm, 1),
            "filler_count": filler_count,
            "clarity_score": round(clarity_score, 1),
            "feedback": feedback
        }

    def generate_interview_question(self, role: str, difficulty: str = "medium") -> Dict[str, Any]:
        """
        Generates targeted situational and technical interview questions.
        """
        questions = {
            "software engineer": "Can you describe a challenging technical bug you encountered in production and how you diagnosed and resolved it?",
            "product manager": "How do you prioritize competing features when engineering resources are constrained?",
            "data scientist": "How do you handle missing or noisy data when building a predictive model?",
            "general": "Tell me about a time you had to deliver a complex project under tight deadlines."
        }
        
        role_key = role.lower()
        question_text = questions.get(role_key, questions["general"])
        
        return {
            "role": role,
            "difficulty": difficulty,
            "question": question_text,
            "eval_criteria": ["STAR Method", "Technical Depth", "Clear Communication"]
        }

voice_engine = RealtimeVoiceInterviewEngine()
