"""
FastAPI Router for Autopoietic Universal AI Agent Network & Self-Replication Fabric Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.autopoietic_universal_swarm import AutopoieticUniversalSwarm, get_universal_swarm_status

router = APIRouter(prefix="/api/v2/universal-swarm", tags=["Autopoietic Universal Swarm"])

class SpawnAgentRequest(BaseModel):
    agent_role: str
    target_cloud_provider: Optional[str] = "cloudflare_workers"

class SelfHealingRequest(BaseModel):
    anomaly_log: str

@router.get("/status")
def status_endpoint():
    return get_universal_swarm_status()

@router.post("/spawn-agent")
def spawn_agent_endpoint(req: SpawnAgentRequest):
    swarm = AutopoieticUniversalSwarm()
    return swarm.spawn_replicated_agent(req.agent_role, req.target_cloud_provider or "cloudflare_workers")

@router.post("/self-heal")
def self_heal_endpoint(req: SelfHealingRequest):
    swarm = AutopoieticUniversalSwarm()
    return swarm.execute_self_healing_mutation(req.anomaly_log)
