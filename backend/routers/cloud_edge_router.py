"""
FastAPI Router for Cloud Edge DB Sync & Telemetry.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from core.cloud_edge_db import CloudEdgeDBAdapter, get_cloud_edge_status

router = APIRouter(prefix="/api/cloud-edge", tags=["Cloud Edge DB"])

@router.get("/status")
def get_edge_status() -> Dict[str, Any]:
    """
    Returns live health telemetry of 24/7 Cloud Edge database nodes.
    """
    try:
        return get_cloud_edge_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
def trigger_cloud_sync() -> Dict[str, Any]:
    """
    Triggers an instant WAL checkpoint & Edge data sync event.
    """
    try:
        adapter = CloudEdgeDBAdapter()
        return adapter.execute_cloud_sync_checkpoint()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
