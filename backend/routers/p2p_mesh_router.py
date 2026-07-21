"""
FastAPI Router for Decentralized P2P Mesh Relay
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from core.p2p_mesh_relay import p2p_mesh

router = APIRouter(prefix="/api/v1/p2p-mesh", tags=["P2P Mesh Network"])

class PeerRegisterRequest(BaseModel):
    peer_id: Optional[str] = None
    ip_region: str = "global"
    capacity: int = 10

class SignalRequest(BaseModel):
    source_peer: str
    target_peer: str

class SignalAnswerRequest(BaseModel):
    channel_id: str
    sdp_answer: str

@router.post("/register")
def register_peer(req: PeerRegisterRequest):
    """Register a new node into the P2P Mesh Network."""
    peer = p2p_mesh.register_peer(peer_id=req.peer_id, ip_region=req.ip_region, capacity=req.capacity)
    return {"status": "success", "peer": peer}

@router.post("/heartbeat")
def peer_heartbeat(peer_id: str = Query(...)):
    """Heartbeat endpoint for active P2P mesh nodes."""
    success = p2p_mesh.heartbeat(peer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Peer node not found")
    return {"status": "success", "peer_id": peer_id}

@router.get("/optimal-peer")
def get_optimal_peer(region: str = "global"):
    """Fetch the optimal peer node ID for a target region."""
    peer_id = p2p_mesh.select_optimal_peer(target_region=region)
    return {"status": "success", "optimal_peer_id": peer_id}

@router.post("/signal/offer")
def create_signal(req: SignalRequest):
    """Initiate a WebRTC signal channel between peers."""
    channel = p2p_mesh.create_signal_channel(req.source_peer, req.target_peer)
    return {"status": "success", "channel": channel}

@router.post("/signal/answer")
def complete_signal(req: SignalAnswerRequest):
    """Complete a WebRTC signaling handshake."""
    success = p2p_mesh.complete_signal(req.channel_id, req.sdp_answer)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid channel ID or signaling state")
    return {"status": "success", "channel_id": req.channel_id}

@router.get("/stats")
def get_mesh_stats():
    """Retrieve P2P Mesh network status and metrics."""
    return {"status": "success", "stats": p2p_mesh.get_mesh_stats()}
