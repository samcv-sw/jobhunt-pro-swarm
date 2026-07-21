from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import time
from core.voice_interview_simulator import voice_interview_simulator

router = APIRouter(prefix="/api/voice-interview", tags=["Voice AI Interviewer"])

class AudioQuestionRequest(BaseModel):
    candidate_id: str
    role_target: str
    experience_level: Optional[str] = "Senior"

class TranscriptAnalysisRequest(BaseModel):
    session_id: str
    transcript: str
    duration_seconds: int

@router.post("/generate-session")
async def generate_voice_session(req: AudioQuestionRequest):
    return {
        "status": "success",
        "session_id": f"voice_sess_{int(time.time())}",
        "role_target": req.role_target,
        "initial_question": f"Hello! Welcome to your AI technical interview for the {req.role_target} role. Could you briefly introduce your background and key achievements?",
        "suggested_topics": ["Architecture", "Problem Solving", "Leadership", "System Design"],
        "audio_stream_url": "/api/voice-interview/stream-audio?id=init_01"
    }

@router.post("/analyze-transcript")
async def analyze_transcript(req: TranscriptAnalysisRequest):
    evaluation = voice_interview_simulator.evaluate_response(req.transcript, req.duration_seconds)
    
    return {
        "status": "completed",
        "session_id": req.session_id,
        "overall_score": evaluation["overall_score"],
        "metrics": {
            "fluency_wpm": evaluation["wpm"],
            "total_words": evaluation["total_words"],
            "filler_words_detected": evaluation["filler_count"],
            "star_framework": evaluation["star_framework"]
        },
        "feedback": evaluation["feedback"],
        "recommended_followups": [
            "Elaborate more on quantifiable business impacts achieved in past projects."
        ]
    }

class VoiceOutreachRequest(BaseModel):
    recruiter_name: str
    company_name: str
    candidate_name: str
    target_role: str
    phone_number: str

@router.post("/outreach-call")
async def initiate_voice_outreach_call(req: VoiceOutreachRequest):
    call_id = f"vapi_call_{int(time.time())}"
    script = (
        f"Hi {req.recruiter_name}, this is an automated message on behalf of {req.candidate_name}. "
        f"They are a top-tier {req.target_role} interested in opportunities at {req.company_name}. "
        f"We sent their verified portfolio to your inbox. Would you like to schedule a 10-minute call?"
    )
    return {
        "status": "initiated",
        "call_id": call_id,
        "phone_number": req.phone_number,
        "script_preview": script,
        "vapi_payload": {
            "model": "gpt-4o-realtime",
            "voice": "jennifer-professional",
            "first_message": f"Hello {req.recruiter_name}, calling regarding top tech talent for {req.company_name}."
        }
    }

