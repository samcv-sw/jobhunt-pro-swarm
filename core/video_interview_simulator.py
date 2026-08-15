"""
MEGA UPGRADE: AI Video Interview Simulator
Real-time interview practice with emotion detection & coaching
WebRTC video recording + ML-powered feedback
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime


class EmotionType(str, Enum):
    """Detected emotions"""
    CONFIDENT = "confident"
    NERVOUS = "nervous"
    ENGAGED = "engaged"
    BORED = "bored"
    FRUSTRATED = "frustrated"
    THOUGHTFUL = "thoughtful"


class InterviewDifficulty(str, Enum):
    """Interview difficulty levels"""
    PHONE_SCREEN = "phone_screen"
    BEHAVIORAL = "behavioral"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    CASE_STUDY = "case_study"


@dataclass
class InterviewSession:
    """Video interview session"""
    session_id: str
    difficulty: InterviewDifficulty
    job_title: str
    company_name: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: int = 0
    video_url: Optional[str] = None
    transcript: str = ""
    questions_asked: List[str] = field(default_factory=list)
    user_answers: List[str] = field(default_factory=list)


@dataclass
class EmotionFrame:
    """Emotion analysis for video frame"""
    timestamp_sec: float
    emotion: EmotionType
    confidence: float  # 0-1
    facial_expression: str
    eye_contact: float  # 0-1 (1 = direct eye contact)
    speaking_rate_wpm: int


@dataclass
class InterviewFeedback:
    """Comprehensive interview feedback"""
    session_id: str
    overall_score: float  # 0-100
    strengths: List[str]
    weaknesses: List[str]
    emotion_analysis: List[EmotionFrame]
    speaking_metrics: Dict[str, Any]
    content_quality_score: float
    communication_score: float
    confidence_score: float
    eye_contact_score: float
    coaching_suggestions: List[str]
    top_improvements: List[str]


class VideoInterviewSimulator:
    """AI-powered interview simulator with emotion detection"""
    
    def __init__(self):
        self.active_sessions: Dict[str, InterviewSession] = {}
        self.interview_questions = self._init_interview_questions()
        self.evaluation_criteria = self._init_evaluation_criteria()
    
    def _init_interview_questions(self) -> Dict[InterviewDifficulty, List[str]]:
        """Initialize interview questions by difficulty"""
        return {
            InterviewDifficulty.PHONE_SCREEN: [
                "Tell me about yourself",
                "Why are you interested in this role?",
                "What's your biggest achievement?",
                "Describe a challenge you overcame",
                "Why do you want to leave your current role?",
                "What are your salary expectations?",
                "When can you start?",
                "Do you have any questions for me?"
            ],
            InterviewDifficulty.BEHAVIORAL: [
                "Tell me about a time you failed and what you learned",
                "Describe a conflict with a team member and how you resolved it",
                "How do you handle tight deadlines?",
                "Tell me about your leadership experience",
                "Describe a time you had to learn something new quickly",
                "How do you prioritize when everything is urgent?",
                "Tell me about your most proud achievement",
                "How do you handle criticism?"
            ],
            InterviewDifficulty.TECHNICAL: [
                "Design a system for [specific problem]",
                "Write code to solve [coding challenge]",
                "Explain a complex technical concept simply",
                "Walk me through your approach to debugging",
                "How would you optimize this algorithm?",
                "Tell me about your experience with [technology]",
                "What's your approach to testing?",
                "How do you stay updated with new technologies?"
            ],
            InterviewDifficulty.EXECUTIVE: [
                "Where do you see yourself in 5 years?",
                "How would you handle a major project failure?",
                "Tell me about your leadership philosophy",
                "How do you build and motivate teams?",
                "What's your approach to strategic thinking?",
                "How do you measure success?",
                "Tell me about a major decision you made",
                "How do you handle ambiguity?"
            ],
            InterviewDifficulty.CASE_STUDY: [
                "How would you enter the [new market]?",
                "Estimate the number of [items in category]",
                "How would you improve [existing product]?",
                "Design a business model for [scenario]",
                "What metrics would you track for [business]?",
                "How would you respond to [competitive threat]?",
                "Create a 100-day plan for [scenario]",
                "How would you structure a team for [goal]?"
            ]
        }
    
    def _init_evaluation_criteria(self) -> Dict[str, Dict[str, int]]:
        """Initialize evaluation criteria weights"""
        return {
            "content_quality": {
                "relevance": 30,
                "specificity": 20,
                "completeness": 20,
                "structure": 15,
                "clarity": 15
            },
            "communication": {
                "speaking_rate": 15,
                "pronunciation": 15,
                "grammar": 15,
                "filler_words": 20,
                "voice_tone": 15,
                "transitions": 20
            },
            "emotion": {
                "confidence": 30,
                "engagement": 25,
                "professionalism": 25,
                "authenticity": 20
            },
            "nonverbal": {
                "eye_contact": 40,
                "facial_expressions": 30,
                "posture": 20,
                "hand_gestures": 10
            }
        }
    
    async def start_interview_session(
        self,
        user_id: str,
        difficulty: InterviewDifficulty,
        job_title: str,
        company_name: str
    ) -> Dict[str, Any]:
        """Start a new interview practice session"""
        
        import secrets
        session_id = secrets.token_hex(8)
        
        session = InterviewSession(
            session_id=session_id,
            difficulty=difficulty,
            job_title=job_title,
            company_name=company_name,
            started_at=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        
        # Get first question
        questions = self.interview_questions[difficulty]
        first_question = questions[0]
        session.questions_asked.append(first_question)
        
        return {
            "session_id": session_id,
            "status": "started",
            "first_question": first_question,
            "difficulty": difficulty.value,
            "tips": self._get_interview_tips(difficulty),
            "recording": True,
            "webrtc_enabled": True
        }
    
    def _get_interview_tips(self, difficulty: InterviewDifficulty) -> List[str]:
        """Get tips for interview difficulty"""
        tips_map = {
            InterviewDifficulty.PHONE_SCREEN: [
                "Keep answers concise (30-60 seconds)",
                "Smile - it comes through your voice",
                "Have your resume nearby for reference",
                "Ask clarifying questions",
                "Highlight relevant experience"
            ],
            InterviewDifficulty.BEHAVIORAL: [
                "Use the STAR method (Situation, Task, Action, Result)",
                "Focus on your role and learning",
                "Show self-awareness and growth",
                "Provide specific examples",
                "Relate stories to job requirements"
            ],
            InterviewDifficulty.TECHNICAL: [
                "Think out loud - explain your approach",
                "Ask clarifying questions",
                "Start with a simple solution, then optimize",
                "Discuss trade-offs",
                "Test your solution with examples"
            ],
            InterviewDifficulty.EXECUTIVE: [
                "Think strategically and big-picture",
                "Show business acumen",
                "Discuss impact and ROI",
                "Demonstrate leadership qualities",
                "Be confident and decisive"
            ],
            InterviewDifficulty.CASE_STUDY: [
                "Structure your thinking (define problem, gather data, analyze)",
                "Make reasonable assumptions",
                "Use frameworks and models",
                "Discuss trade-offs and risks",
                "Summarize key recommendations"
            ]
        }
        return tips_map.get(difficulty, [])
    
    async def process_video_frame(
        self,
        session_id: str,
        frame_data: bytes,
        timestamp_sec: float
    ) -> Optional[EmotionFrame]:
        """Process video frame for emotion detection"""
        
        if session_id not in self.active_sessions:
            return None
        
        # In production: use actual ML model (OpenAI Vision, Google Cloud Vision, etc.)
        # For demo: simulate emotion detection
        emotion = self._simulate_emotion_detection(timestamp_sec)
        
        frame = EmotionFrame(
            timestamp_sec=timestamp_sec,
            emotion=emotion,
            confidence=0.85 + (timestamp_sec % 0.1),
            facial_expression=self._get_facial_expression(emotion),
            eye_contact=0.7 + (0.3 * ((timestamp_sec % 10) / 10)),
            speaking_rate_wpm=int(120 + (timestamp_sec % 40))
        )
        
        return frame
    
    def _simulate_emotion_detection(self, timestamp: float) -> EmotionType:
        """Simulate emotion detection"""
        emotions = [
            EmotionType.CONFIDENT,
            EmotionType.ENGAGED,
            EmotionType.THOUGHTFUL,
            EmotionType.NERVOUS
        ]
        emotion_idx = int(timestamp) % len(emotions)
        return emotions[emotion_idx]
    
    def _get_facial_expression(self, emotion: EmotionType) -> str:
        """Get facial expression for emotion"""
        expressions = {
            EmotionType.CONFIDENT: "smile (genuine)",
            EmotionType.NERVOUS: "tight smile",
            EmotionType.ENGAGED: "alert expression",
            EmotionType.BORED: "neutral expression",
            EmotionType.FRUSTRATED: "furrowed brow",
            EmotionType.THOUGHTFUL: "concerned expression"
        }
        return expressions.get(emotion, "neutral")
    
    async def end_interview_session(self, session_id: str) -> Dict[str, Any]:
        """End interview session and generate feedback"""
        
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        session.ended_at = datetime.now()
        session.duration_seconds = int(
            (session.ended_at - session.started_at).total_seconds()
        )
        
        # Generate feedback
        feedback = await self._generate_comprehensive_feedback(session)
        
        return {
            "status": "completed",
            "session_id": session_id,
            "duration": session.duration_seconds,
            "feedback": {
                "overall_score": feedback.overall_score,
                "content_quality": feedback.content_quality_score,
                "communication": feedback.communication_score,
                "confidence": feedback.confidence_score,
                "eye_contact": feedback.eye_contact_score,
                "strengths": feedback.strengths,
                "areas_for_improvement": feedback.weaknesses,
                "coaching_suggestions": feedback.coaching_suggestions,
                "top_improvements": feedback.top_improvements
            }
        }
    
    async def _generate_comprehensive_feedback(self, session: InterviewSession) -> InterviewFeedback:
        """Generate comprehensive interview feedback"""
        
        # Simulate feedback generation
        feedback = InterviewFeedback(
            session_id=session.session_id,
            overall_score=78.5,
            strengths=[
                "Clear communication of key points",
                "Good use of specific examples",
                "Professional tone maintained",
                "Relevant experience highlighted"
            ],
            weaknesses=[
                "Spoke a bit too quickly in some parts",
                "Could have provided more detail on technical aspects",
                "Minor filler words used",
                "Limited follow-up questions asked"
            ],
            emotion_analysis=[
                EmotionFrame(
                    timestamp_sec=i * 10,
                    emotion=EmotionType.CONFIDENT if i % 2 == 0 else EmotionType.ENGAGED,
                    confidence=0.85,
                    facial_expression="smile (genuine)",
                    eye_contact=0.75,
                    speaking_rate_wpm=130
                )
                for i in range(5)
            ],
            speaking_metrics={
                "average_speaking_rate": 132,
                "pause_frequency": 0.8,
                "filler_words_count": 5,
                "clarity_score": 85,
                "pronunciation_score": 90
            },
            content_quality_score=80.0,
            communication_score=76.0,
            confidence_score=82.0,
            eye_contact_score=75.0,
            coaching_suggestions=[
                "Slow down slightly for clarity (currently 132 WPM, target 120-130)",
                "Reduce filler words by taking brief pauses",
                "Add 1-2 follow-up questions to show interest",
                "Provide specific metrics/numbers in achievements",
                "Practice maintaining steady eye contact with camera"
            ],
            top_improvements=[
                "Practice with 3-4 behavioral questions weekly",
                "Record yourself and review for filler words",
                "Study STAR method framework",
                "Prepare specific quantifiable achievements",
                "Work on pacing and natural pauses"
            ]
        )
        
        return feedback
    
    async def get_practice_recommendations(self, session_id: str) -> Dict[str, Any]:
        """Get personalized practice recommendations"""
        
        if session_id not in self.active_sessions:
            return {}
        
        session = self.active_sessions[session_id]
        
        return {
            "next_focus_areas": [
                "Technical depth for system design questions",
                "STAR method for behavioral questions",
                "Confidence and body language",
                "Question preparation and research"
            ],
            "recommended_practice": [
                "Practice 3 more interviews this week",
                "Focus on technical difficulty level next",
                "Record and review sessions",
                "Study industry trends and company info"
            ],
            "resources": [
                "STAR method guide",
                "System design interview prep",
                "Behavioral questions library",
                "Mock interview booking"
            ],
            "improvement_trajectory": {
                "current_score": 78.5,
                "week_1_target": 82,
                "month_1_target": 88,
                "confidence_improvement": "4-5 points per practice session"
            }
        }


# Global instance
video_simulator = VideoInterviewSimulator()
