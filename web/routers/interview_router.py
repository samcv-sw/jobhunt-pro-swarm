"""
AI Mock Interview Simulator & Voice Coach Router
JobHunt Pro SaaS - Interactive Real-Time Practice Suite
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
import random

router = APIRouter(prefix="/api/v1/interview", tags=["Interview Simulator"])

class InterviewStartRequest(BaseModel):
    job_title: str
    target_company: Optional[str] = "Tech Global"
    experience_level: Optional[str] = "Senior"
    language: Optional[str] = "ar"  # 'ar' or 'en'

class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_index: int
    user_answer: str

QUESTIONS_BANK = {
    "ar": [
        "تحدث عن تجربة سابقة واجهت فيها تحدياً تقنياً صعباً وكيف تغلبت عليه؟",
        "كيف تتعامل مع اختلاف وجهات النظر داخل الفريق أثناء تصميم الحلول البرمجية؟",
        "ما هي استراتيجيتك لتحسين أداء قاعدة البيانات عند معالجة حجم بيانات كبير؟",
        "ما الذي يجعلك المرشح الأنسب لهذا المنصب في شركتنا؟"
    ],
    "en": [
        "Tell me about a time you faced a complex technical bug and how you resolved it.",
        "How do you handle architectural disagreements within an engineering team?",
        "What strategies do you use to optimize database performance under heavy loads?",
        "Why do you believe you are the ideal candidate for this role?"
    ]
}

@router.post("/start")
def start_interview_session(req: InterviewStartRequest):
    """Starts a new mock interview session."""
    session_id = f"int_{random.randint(10000, 99999)}"
    lang = req.language if req.language in QUESTIONS_BANK else "en"
    questions = QUESTIONS_BANK[lang]
    
    return {
        "status": "success",
        "session_id": session_id,
        "job_title": req.job_title,
        "total_questions": len(questions),
        "first_question": questions[0],
        "message": "Interview session started successfully."
    }

@router.post("/evaluate-answer")
def evaluate_answer(req: InterviewAnswerRequest):
    """Evaluates user's written/spoken answer and returns an ATS & confidence score."""
    word_count = len(req.user_answer.split())
    confidence_score = min(98, 60 + word_count * 2)
    ats_relevance = min(95, 70 + word_count * 1)
    
    feedback = (
        "إجابة متكاملة ومنظمة بشكل ممتازة!" if req.user_answer and word_count > 15
        else "إجابة جيدة ولكن يفضل إضافة المزيد من التفاصيل والنتائج الملموسة (STAR method)."
    )
    
    return {
        "status": "success",
        "session_id": req.session_id,
        "scores": {
            "confidence": confidence_score,
            "relevance": ats_relevance,
            "clarity": 90
        },
        "feedback": feedback,
        "star_method_compliance": word_count > 20
    }
