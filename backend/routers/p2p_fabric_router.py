"""
FastAPI Router for Quantum-Resistant P2P Mesh Fabric & Decoupled Compute Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.quantum_p2p_mesh_fabric import QuantumP2PMeshFabric, get_mesh_fabric_status

router = APIRouter(prefix="/api/v2/p2p-fabric", tags=["Quantum P2P Mesh Fabric"])

class PeerRegisterRequest(BaseModel):
    peer_b64_pubkey: str

class MeshInferenceRequest(BaseModel):
    prompt: str
    target_peers: Optional[int] = 3

@router.get("/status")
def status_endpoint():
    return get_mesh_fabric_status()

@router.post("/register-peer")
def register_peer_endpoint(req: PeerRegisterRequest):
    fabric = QuantumP2PMeshFabric()
    return fabric.register_peer_node(req.peer_b64_pubkey)

@router.post("/dispatch-task")
def dispatch_task_endpoint(req: MeshInferenceRequest):
    fabric = QuantumP2PMeshFabric()
    return fabric.dispatch_mesh_inference_task(req.prompt, req.target_peers or 3)
