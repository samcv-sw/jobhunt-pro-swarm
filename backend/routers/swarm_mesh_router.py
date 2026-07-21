"""P2P AI Swarm Mesh API Router

Exposes endpoints for peer discovery, gossip heartbeat synchronization,
and P2P task delegation across distributed mesh nodes.
"""

from typing import Any, Dict
from fastapi import APIRouter
from pydantic import BaseModel

from core.p2p_swarm_mesh import p2p_swarm_mesh

router = APIRouter(prefix="/api/v3/mesh", tags=["P2P Swarm Mesh Network"])


class DelegateTaskRequest(BaseModel):
    task_type: str = "ai_resume_matching"
    payload: Dict[str, Any] = {}


@router.get("/peers")
async def get_mesh_peers():
    """Returns active peer nodes in the decentralized P2P swarm mesh network."""
    return p2p_swarm_mesh.discover_peers()


@router.post("/gossip-ping")
async def send_gossip_ping():
    """Broadcasts gossip protocol heartbeat state across mesh peers."""
    return p2p_swarm_mesh.broadcast_gossip_heartbeat()


@router.post("/delegate")
async def delegate_task(req: DelegateTaskRequest):
    """Delegates workload to the optimal P2P mesh node with automatic failover."""
    return p2p_swarm_mesh.delegate_p2p_task(req.task_type, req.payload)
