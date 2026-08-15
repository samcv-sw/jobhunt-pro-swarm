"""
AI INTERVIEW SIMULATOR - Video Recording + Real-Time Analysis
Emotion detection, confidence scoring, speech analysis
Real-time feedback + coaching suggestions
"""

import asyncio
import base64
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class EmotionType(str, Enum):
    """Detected emotions"""
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    FOCUSED = "focused"
    UNCERTAIN = "uncertain"
    DEFENSIVE = "defensive"
    ENGAGED = "engaged"


class FeedbackCategory(str, Enum):
    """Feedback categories"""
    EYE_CONTACT = "eye_contact"
    POSTURE = "posture"
    SPEECH_PACE = "speech_pace"
    CLARITY = "clarity"
    ENTHUSIASM = "enthusiasm"
    TECHNICAL_ACCURACY = "technical_accuracy"
    STRUCTURE = "structure"
    CONFIDENCE = "confidence"


@dataclass
class EmotionFrame:
    """Single frame emotion detection"""
    timestamp: float
    dominant_emotion: EmotionType
    confidence: float
    emotions: Dict[str, float]  # all emotions with scores
    facial_features: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpeechAnalysis:
    """Speech metrics"""
    total_duration_sec: float
    words_spoken: int
    words_per_minute: float
    pause_count: int
    avg_pause_duration_sec: float
    clarity_score: float  # 0-1
    filler_words: List[str] = field(default_factory=list)
    filler_count: int = 0
    tone_variation: float = 0.0  # 0-1


@dataclass
class AnswerFeedback:
    """Feedback for single answer"""
    question_index: int
    question: str
    user_answer: str
    duration_sec: float
    emotion_progression: List[EmotionType] = field(default_factory=list)
    speech_analysis: Optional[SpeechAnalysis] = None
    emotion_average: EmotionType = EmotionType.CONFIDENT
    clarity_score: float = 0.0
    confidence_score: float = 0.0
    structure_score: float = 0.0
    technical_accuracy: float = 0.0
    feedback_points: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    coach_suggestions: List[str] = field(default_factory=list)


@dataclass
class InterviewSession:
    """Complete interview session"""
    session_id: str
    interview_type: str  # "behavioral", "technical", "mixed"
    job_title: str
    company: str
    questions: List[str] = field(default_factory=list)
    answers: List[AnswerFeedback] = field(default_factory=list)
    video_recordings: Dict[int, str] = field(default_factory=dict)  # base64 encoded
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    overall_score: float = 0.0
    overall_feedback: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class EmotionDetector:
    """Emotion detection from video/facial features"""
    
    @staticmethod
    async def analyze_video_frame(frame_data: bytes) -> EmotionFrame:
        """Analyze single video frame for emotions"""
        
        # In production: use OpenCV + emotion detection model
        # For demo: simulate emotion detection
        import random
        
        emotions_map = {
            "confident": random.uniform(0.3, 0.8),
            "nervous": random.uniform(0.1, 0.4),
            "focused": random.uniform(0.4, 0.9),
            "uncertain": random.uniform(0.0, 0.3),
            "engaged": random.uniform(0.4, 0.9),
        }
        
        # Normalize scores
        total = sum(emotions_map.values())
        emotions = {k: v/total for k, v in emotions_map.items()}
        
        dominant = max(emotions.items(), key=lambda x: x[1])
        
        return EmotionFrame(
            timestamp=datetime.now().timestamp(),
            dominant_emotion=EmotionType(dominant[0]),
            confidence=dominant[1],
            emotions=emotions,
            facial_features={
                "eye_contact": random.uniform(0.5, 1.0),
                "smile": random.uniform(0.0, 0.8),
                "head_position": "neutral"
            }
        )
    
    @staticmethod
    async def analyze_emotion_sequence(frames: List[EmotionFrame]) -> Dict[str, Any]:
        """Analyze emotion progression through interview"""
        
        if not frames:
            return {}
        
        emotions_sequence = [f.dominant_emotion for f in frames]
        emotion_scores = {e.value: 0 for e in EmotionType}
        
        for frame in frames:
            emotion_scores[frame.dominant_emotion.value] += frame.confidence
        
        return {
            "sequence": emotions_sequence,
            "dominant": max(emotion_scores.items(), key=lambda x: x[1])[0],
            "confidence_trend": [f.confidence for f in frames],
            "stability": self._calculate_emotion_stability(emotions_sequence)
        }
    
    @staticmethod
    def _calculate_emotion_stability(emotions: List[EmotionType]) -> float:
        """Calculate how stable emotions are (0-1)"""
        if len(emotions) < 2:
            return 1.0
        
        changes = sum(1 for i in range(len(emotions)-1) if emotions[i] != emotions[i+1])
        stability = 1.0 - (changes / len(emotions))
        return max(0.0, min(1.0, stability))


class SpeechAnalyzer:
    """Speech pattern analysis"""
    
    @staticmethod
    async def analyze_speech(transcript: str, audio_duration_sec: float) -> SpeechAnalysis:
        """Analyze speech patterns"""
        
        words = transcript.split()
        words_spoken = len(words)
        words_per_minute = (words_spoken / audio_duration_sec) * 60 if audio_duration_sec > 0 else 0
        
        # Detect filler words
        filler_words = ['um', 'uh', 'like', 'you know', 'basically', 'literally', 'honestly']
        fillers_found = []
        filler_count = 0
        
        for filler in filler_words:
            count = transcript.lower().count(filler)
            if count > 0:
                fillers_found.append(filler)
                filler_count += count
        
        # Estimate pause count and duration
        pause_count = transcript.count('...')
        avg_pause_duration = 1.0  # placeholder
        
        # Calculate clarity (fewer filler words = higher clarity)
        clarity_score = max(0.0, 1.0 - (filler_count / max(words_spoken, 1)))
        
        # Tone variation (simplified: based on punctuation)
        exclamation_marks = transcript.count('!')
        question_marks = transcript.count('?')
        tone_variation = min(1.0, (exclamation_marks + question_marks) / max(words_spoken / 10, 1))
        
        return SpeechAnalysis(
            total_duration_sec=audio_duration_sec,
            words_spoken=words_spoken,
            words_per_minute=words_per_minute,
            pause_count=pause_count,
            avg_pause_duration_sec=avg_pause_duration,
            clarity_score=clarity_score,
            filler_words=fillers_found,
            filler_count=filler_count,
            tone_variation=tone_variation
        )


class InterviewCoach:
    """AI coaching and feedback engine"""
    
    BEHAVIORAL_PATTERNS = {
        "STAR_method": "Structure answer with Situation, Task, Action, Result",
        "conciseness": "Keep answers to 2-3 minutes max",
        "confidence": "Maintain steady voice and posture",
        "engagement": "Make eye contact, nod occasionally",
        "specificity": "Use concrete examples instead of general statements"
    }
    
    TECHNICAL_PATTERNS = {
        "clarity": "Explain your approach before coding",
        "step_by_step": "Walk through solution step-by-step",
        "trade_offs": "Discuss time/space complexity trade-offs",
        "edge_cases": "Consider edge cases and error handling",
        "verification": "Test your solution with examples"
    }
    
    @staticmethod
    async def generate_feedback(
        answer: str,
        answer_duration: float,
        question: str,
        question_type: str,  # "behavioral" or "technical"
        emotion_data: List[EmotionFrame],
        speech_data: SpeechAnalysis
    ) -> AnswerFeedback:
        """Generate comprehensive feedback for answer"""
        
        feedback = AnswerFeedback(
            question_index=0,
            question=question,
            user_answer=answer,
            duration_sec=answer_duration
        )
        
        # Calculate scores
        feedback.clarity_score = speech_data.clarity_score
        feedback.confidence_score = sum(f.confidence for f in emotion_data) / len(emotion_data) if emotion_data else 0.5
        feedback.emotion_average = emotion_data[0].dominant_emotion if emotion_data else EmotionType.CONFIDENT
        
        # Structure analysis
        if "because" in answer.lower() and len(answer.split()) > 20:
            feedback.structure_score = 0.8
        else:
            feedback.structure_score = 0.5
        
        # Feedback points
        if speech_data.filler_count > 5:
            feedback.feedback_points.append(f"Reduce filler words: {speech_data.filler_count} detected")
        
        if speech_data.words_per_minute < 100:
            feedback.feedback_points.append("Speak a bit faster - you're under 100 WPM")
        elif speech_data.words_per_minute > 150:
            feedback.feedback_points.append("Slow down slightly - pacing at 150+ WPM")
        
        if len(answer.split()) < 50:
            feedback.feedback_points.append("Answer lacks depth - provide more detail")
        
        # Generate improvements
        if question_type == "behavioral":
            patterns = InterviewCoach.BEHAVIORAL_PATTERNS
            if not any(method in answer.lower() for method in ["situation", "task", "action", "result"]):
                feedback.improvements.append("Try using the STAR method: Situation, Task, Action, Result")
        else:
            patterns = InterviewCoach.TECHNICAL_PATTERNS
            if "complexity" not in answer.lower():
                feedback.improvements.append("Discuss time and space complexity of your solution")
        
        # Coach suggestions
        if feedback.confidence_score > 0.7:
            feedback.coach_suggestions.append("✓ Great confidence! Keep up that energy")
        else:
            feedback.coach_suggestions.append("Slow down and take a breath - you seem rushed")
        
        if feedback.clarity_score > 0.8:
            feedback.coach_suggestions.append("✓ Very clear articulation - excellent!")
        else:
            feedback.coach_suggestions.append("Focus on enunciating clearly - reduce filler words")
        
        return feedback


class AIInterviewSimulator:
    """Complete interview simulation engine"""
    
    def __init__(self):
        self.sessions: Dict[str, InterviewSession] = {}
        self.emotion_detector = EmotionDetector()
        self.speech_analyzer = SpeechAnalyzer()
        self.coach = InterviewCoach()
    
    async def start_interview_session(
        self,
        interview_type: str,
        job_title: str,
        company: str,
        questions: List[str]
    ) -> InterviewSession:
        """Start new interview session"""
        
        import uuid
        session_id = str(uuid.uuid4())
        
        session = InterviewSession(
            session_id=session_id,
            interview_type=interview_type,
            job_title=job_title,
            company=company,
            questions=questions,
            started_at=datetime.now()
        )
        
        self.sessions[session_id] = session
        return session
    
    async def process_answer(
        self,
        session_id: str,
        question_index: int,
        answer_text: str,
        video_data: Optional[bytes] = None,
        audio_duration_sec: float = 0.0
    ) -> AnswerFeedback:
        """Process and analyze answer"""
        
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Analyze speech
        speech_analysis = await self.speech_analyzer.analyze_speech(answer_text, audio_duration_sec)
        
        # Simulate emotion detection from video
        emotion_frames = []
        if video_data:
            # In production: extract frames from video
            for i in range(5):
                frame = await self.emotion_detector.analyze_video_frame(video_data)
                emotion_frames.append(frame)
        
        # Generate feedback
        feedback = await self.coach.generate_feedback(
            answer=answer_text,
            answer_duration=audio_duration_sec,
            question=session.questions[question_index],
            question_type=session.interview_type,
            emotion_data=emotion_frames,
            speech_data=speech_analysis
        )
        
        feedback.question_index = question_index
        feedback.speech_analysis = speech_analysis
        feedback.emotion_progression = [f.dominant_emotion for f in emotion_frames]
        
        session.answers.append(feedback)
        
        # Store video
        if video_data:
            session.video_recordings[question_index] = base64.b64encode(video_data).decode()
        
        return feedback
    
    async def complete_interview(self, session_id: str) -> InterviewSession:
        """Complete interview and generate overall report"""
        
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.completed_at = datetime.now()
        
        # Calculate overall score
        if session.answers:
            scores = [
                a.clarity_score for a in session.answers
                if a.clarity_score > 0
            ]
            session.overall_score = sum(scores) / len(scores) if scores else 0.0
        
        # Generate overall feedback
        session.overall_feedback.append("Great effort practicing!")
        
        if session.overall_score > 0.8:
            session.overall_feedback.append("Excellent performance - ready for real interviews!")
            session.recommendations.append("Practice with increasingly difficult questions")
        elif session.overall_score > 0.6:
            session.overall_feedback.append("Good performance - focus on weak areas")
            session.recommendations.append("Work on clarity and reduce filler words")
        else:
            session.overall_feedback.append("Keep practicing - you'll improve quickly")
            session.recommendations.append("Record yourself and review often")
        
        return session
    
    async def get_session_report(self, session_id: str) -> Dict[str, Any]:
        """Get detailed session report"""
        
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        return {
            "session_id": session.session_id,
            "job_title": session.job_title,
            "company": session.company,
            "interview_type": session.interview_type,
            "total_questions": len(session.questions),
            "questions_answered": len(session.answers),
            "overall_score": session.overall_score,
            "overall_feedback": session.overall_feedback,
            "recommendations": session.recommendations,
            "answers_detail": [
                {
                    "question": a.question,
                    "duration_sec": a.duration_sec,
                    "clarity_score": a.clarity_score,
                    "confidence_score": a.confidence_score,
                    "structure_score": a.structure_score,
                    "feedback": a.feedback_points,
                    "improvements": a.improvements,
                    "coach_suggestions": a.coach_suggestions
                }
                for a in session.answers
            ],
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None
        }


# Global instance
interview_simulator = AIInterviewSimulator()
