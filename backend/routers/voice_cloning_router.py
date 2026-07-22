"""
FastAPI Router for Voice Cloning & Sub-50ms Latency Meeting Proxy.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.voice_cloning_proxy import VoiceCloningProxy, get_voice_proxy_status

router = APIRouter(prefix="/api/v2/voice-proxy", tags=["Voice Proxy & Meeting Shadowing"])

class AudioSynthesisRequest(BaseModel):
    text: str
    voice_profile_id: str

class VoiceProfileRequest(BaseModel):
    candidate_id: str
    sample_b64: str

@router.get("/status")
def status_endpoint():
    return get_voice_proxy_status()

@router.post("/clone-profile")
def clone_profile_endpoint(req: VoiceProfileRequest):
    proxy = VoiceCloningProxy()
    sample_bytes = req.sample_b64.encode("utf-8")
    return proxy.clone_voice_profile(sample_bytes, req.candidate_id)

@router.post("/synthesize-stream")
def synthesize_stream_endpoint(req: AudioSynthesisRequest):
    proxy = VoiceCloningProxy()
    return proxy.generate_realtime_audio_stream(req.text, req.voice_profile_id)
