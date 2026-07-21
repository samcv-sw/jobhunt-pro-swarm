"""WebRTC Video Avatar API Router

Exposes endpoints for interactive WebRTC AI video avatar session management,
SDP handshake negotiation, and lip-sync video frame generation.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from core.webrtc_video_avatar import webrtc_video_avatar

router = APIRouter(prefix="/api/v3/avatar", tags=["WebRTC Video Avatar"])


class CreateSessionRequest(BaseModel):
    avatar_style: str = "executive_interviewer"


class SDPOfferRequest(BaseModel):
    session_id: str = ""
    sdp_offer: str = "v=0\r\no=- 0 0 IN IP4 127.0.0.1\r\n"


class LipSyncRequest(BaseModel):
    session_id: str
    text_chunk: str = "Hello, I am your AI interview co-pilot."


@router.post("/session")
async def create_session(req: CreateSessionRequest):
    """Creates a new WebRTC Video Avatar session."""
    return webrtc_video_avatar.create_avatar_session(req.avatar_style)


@router.post("/webrtc-offer")
async def process_sdp_offer(req: SDPOfferRequest):
    """Processes WebRTC SDP offer and completes real-time media handshake."""
    return webrtc_video_avatar.handle_sdp_offer(req.session_id, req.sdp_offer)


@router.post("/lip-sync")
async def render_lip_sync(req: LipSyncRequest):
    """Calculates phoneme visemes for real-time lip-synced video avatar frames."""
    return webrtc_video_avatar.render_lip_sync_frame(req.session_id, req.text_chunk)
