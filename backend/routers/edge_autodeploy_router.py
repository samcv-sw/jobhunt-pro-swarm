"""
FastAPI Router for Autonomous Multi-Cloud Edge Deployment Orchestrator.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from deploy.edge_autodeploy import MultiCloudEdgeOrchestrator, get_orchestrator_status

router = APIRouter(prefix="/api/v2/edge-deploy", tags=["Multi-Cloud Edge Deployment"])

class DeployTriggerRequest(BaseModel):
    app_version: Optional[str] = "v3.0.0-galactic"

@router.get("/status")
def status_endpoint():
    return get_orchestrator_status()

@router.post("/trigger-deploy")
def trigger_deploy_endpoint(req: DeployTriggerRequest):
    orchestrator = MultiCloudEdgeOrchestrator()
    return orchestrator.execute_multi_cloud_deploy(req.app_version or "v3.0.0-galactic")
