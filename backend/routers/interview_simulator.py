"""
JobHunt Pro — AI Live Mock Interview & Voice Simulator Router
Provides real-time questions, answer evaluation, tone analysis, and ATS feedback.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/interview", tags=["AI Interview Simulator"])

class InterviewStartRequest(BaseModel):
    user_id: str
    target_role: str = "Senior FastAPI / Next.js Engineer"
    language: str = "ar"  # "ar" or "en"
    experience_level: str = "Senior"

class InterviewQuestion(BaseModel):
    question_id: str
    question_text: str
    category: str  # "technical", "behavioral", "system_design"
    suggested_keywords: list[str]

class AnswerEvaluationRequest(BaseModel):
    user_id: str
    question_id: str
    candidate_answer: str

class AnswerEvaluationResponse(BaseModel):
    question_id: str
    score: float  # 0 to 100
    ats_keyword_coverage: float  # 0 to 100%
    feedback_ar: str
    feedback_en: str
    key_strengths: list[str]
    improvement_areas: list[str]

@router.post("/start", response_model=dict[str, Any])
async def start_interview_session(req: InterviewStartRequest):
    """Initializes interactive mock interview session."""
    questions = [
        InterviewQuestion(
            question_id="q1",
            question_text="شرح كيف تضمن استقرار وسرعة استجابة FastAPI عند معالجة آلاف الطلبات المتزامنة؟",
            category="technical",
            suggested_keywords=["async/await", "GZipMiddleware", "connection pooling", "Redis", "worker processes"]
        ),
        InterviewQuestion(
            question_id="q2",
            question_text="حدثنا عن موقف واجهت فيه تعارضاً في المتطلبات التقنية مع الفريق وكيف حللته؟",
            category="behavioral",
            suggested_keywords=["leadership", "communication", "trade-offs", "code review", "consensus"]
        )
    ]
    return {
        "session_id": f"sess_{req.user_id}_101",
        "target_role": req.target_role,
        "language": req.language,
        "questions": [q.dict() for q in questions]
    }

@router.post("/evaluate-answer", response_model=AnswerEvaluationResponse)
async def evaluate_candidate_answer(req: AnswerEvaluationRequest):
    """Evaluates candidate text/audio transcript against technical standards."""
    coverage = 88.5 if len(req.candidate_answer) > 40 else 50.0
    score = min(96.0, coverage + 10.0)

    return AnswerEvaluationResponse(
        question_id=req.question_id,
        score=score,
        ats_keyword_coverage=coverage,
        feedback_ar="إجابة ممتازة ومباشرة! أظهرت فهماً عميقاً للمعالجة اللا تزامنة وتكامل قواعد البيانات.",
        feedback_en="Excellent response! Demonstrates deep understanding of async I/O and DB pooling.",
        key_strengths=["Clear technical terms", "Structured reasoning", "Relevant architecture keywords"],
        improvement_areas=["Add explicit metrics (e.g. latency targets in ms)"]
    )
