from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import time

router = APIRouter(prefix="/api/live-interview-coach", tags=["Live Speech Interview Coach"])

class SpeechChunkRequest(BaseModel):
    session_id: str
    audio_transcript_chunk: str
    speaking_rate_wpm: Optional[int] = 135
    emotion_tone: Optional[str] = "Confident"

@router.post("/process-chunk")
async def process_speech_chunk(req: SpeechChunkRequest):
    words = req.audio_transcript_chunk.split()
    filler_words = {"um", "uh", "like", "you know", "basically", "actually"}
    detected_fillers = [w.lower() for w in words if w.lower() in filler_words]
    
    clarity_score = max(50, 100 - (len(detected_fillers) * 8))
    
    live_suggestion = "أداء ممتاز وتدفق ممتاز!"
    if req.speaking_rate_wpm > 160:
        live_suggestion = "تبطئة رتم الحديث قليلاً لزيادة الوضوح والهدوء."
    elif len(detected_fillers) > 2:
        live_suggestion = "تقليل كلمات الحشو (Um/Like) واستخدام الوقفات الذكية."

    return {
        "status": "success",
        "session_id": req.session_id,
        "metrics": {
            "wpm": req.speaking_rate_wpm,
            "clarity_score": clarity_score,
            "emotion_tone": req.emotion_tone,
            "fillers_count": len(detected_fillers)
        },
        "live_coaching_card": {
            "tip": live_suggestion,
            "star_method_stage": "ACTION",
            "confidence_meter_pct": clarity_score
        }
    }

@router.get("/session-summary/{session_id}")
async def get_session_summary(session_id: str):
    return {
        "status": "success",
        "session_id": session_id,
        "overall_rating": "EXCELLENT",
        "composite_score": 92,
        "key_strengths": [
            "قوة الحجة التقنية وصياغة الإجابات وفق منهجية STAR",
            "نبرة واثقة وهادئة طوال المقابلة"
        ],
        "improvement_areas": [
            "زيادة التركيز على الأرقام والنتائج المحققة (Measurable Business Impact)"
        ]
    }
