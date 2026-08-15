"""
Multimodal Vision & Audio Interview Router
JobHunt Pro SaaS - Fast REST endpoints for WebRTC Canvas Vision & Speech Telemetry
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from core.multimodal_vision_interview import multimodal_vision_analyzer

router = APIRouter(prefix="/api/v2/vision", tags=["Multimodal Vision Interview"])


class FrameTelemetryRequest(BaseModel):
    face_detected: bool = True
    gaze_pitch: float = Field(0.0, description="Pitch angle in degrees")
    gaze_yaw: float = Field(0.0, description="Yaw angle in degrees")
    smile_intensity: float = Field(0.2, ge=0.0, le=1.0)
    head_tilt: float = Field(0.0, description="Tilt angle in degrees")
    shoulder_level_delta: float = Field(0.01, ge=0.0, le=1.0)
    lighting_lux: float = Field(120.0, ge=0.0)


class SpeechProsodyRequest(BaseModel):
    transcript_text: str = Field(..., min_length=1)
    duration_seconds: float = Field(..., gt=0.0)
    pitch_variance_hz: Optional[float] = 25.0


class FullSessionScorecardRequest(BaseModel):
    candidate_name: str = "Candidate"
    target_role: str = "Enterprise Architect"
    frame_telemetries: List[Dict[str, Any]] = []
    transcript_text: str = "I led the microservices migration and reduced latency by 45 percent."
    duration_seconds: float = 30.0


@router.get("/status")
def get_vision_engine_status():
    """Returns the operational status of the Multimodal Vision & Prosody engine."""
    return {
        "status": "operational",
        "vision_subsystem": "WebRTC Canvas Landmark Processor",
        "audio_subsystem": "Prosody & WPM Cadence Analyzer",
        "supported_languages": ["ar-GCC", "en-US", "en-GB"],
        "max_frame_rate_hz": 30
    }


@router.post("/frame-telemetry")
def analyze_frame(req: FrameTelemetryRequest):
    """Processes real-time frame telemetry and returns HUD overlay feedback."""
    return multimodal_vision_analyzer.analyze_frame_telemetry(
        face_detected=req.face_detected,
        gaze_pitch=req.gaze_pitch,
        gaze_yaw=req.gaze_yaw,
        smile_intensity=req.smile_intensity,
        head_tilt=req.head_tilt,
        shoulder_level_delta=req.shoulder_level_delta,
        lighting_lux=req.lighting_lux
    )


@router.post("/speech-eval")
def analyze_speech(req: SpeechProsodyRequest):
    """Evaluates cadence, pacing, and filler words from spoken transcript."""
    return multimodal_vision_analyzer.evaluate_speech_prosody(
        transcript_text=req.transcript_text,
        duration_seconds=req.duration_seconds,
        pitch_variance_hz=req.pitch_variance_hz or 25.0
    )


@router.post("/generate-scorecard")
def generate_scorecard(req: FullSessionScorecardRequest):
    """Generates an executive candidate interview scorecard with vision and vocal metrics."""
    speech_eval = multimodal_vision_analyzer.evaluate_speech_prosody(
        transcript_text=req.transcript_text,
        duration_seconds=req.duration_seconds
    )
    return multimodal_vision_analyzer.generate_full_session_scorecard(
        candidate_name=req.candidate_name,
        target_role=req.target_role,
        frame_telemetries=req.frame_telemetries,
        speech_eval=speech_eval
    )
