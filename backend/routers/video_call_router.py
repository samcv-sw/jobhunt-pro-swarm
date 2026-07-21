"""
FastAPI Router for Real-Time Live Video Call AI Copilot
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from core.video_call_copilot import video_copilot

router = APIRouter(prefix="/api/v1/video-call-copilot", tags=["Video Call AI Copilot"])

class StartSessionRequest(BaseModel):
    user_id: str
    target_role: Optional[str] = "Senior Software Engineer"

class AudioTranscriptChunk(BaseModel):
    session_id: str
    text: str
    speaker: Optional[str] = "interviewer"

@router.post("/session/start")
def start_session(req: StartSessionRequest):
    """Start a live video call copilot session."""
    session = video_copilot.start_session(user_id=req.user_id, target_role=req.target_role)
    return {"status": "success", "session": session}

@router.post("/transcript")
def process_transcript(req: AudioTranscriptChunk):
    """Process live transcript chunk and generate HUD teleprompter cards."""
    res = video_copilot.process_audio_transcript(
        session_id=req.session_id,
        text=req.text,
        speaker=req.speaker
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return {"status": "success", "data": res}

@router.get("/hud/{session_id}")
def get_hud_state(session_id: str):
    """Retrieve HUD telemetry state for teleprompter stream."""
    res = video_copilot.get_hud_state(session_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return {"status": "success", "hud": res}
