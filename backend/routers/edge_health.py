"""
JobHunt Pro SaaS — Multi-Region Cloud Edge Health & Failover Router
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body
from core.cloud_edge_failover import CloudEdgeFailoverManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/edge", tags=["Multi-Region Cloud Edge"])
failover_manager = CloudEdgeFailoverManager()

@router.get("/status")
async def get_edge_cluster_status():
    """Returns real-time status of multi-region edge nodes and active cluster routing."""
    return failover_manager.get_cluster_status()

@router.post("/failover")
async def trigger_edge_failover(payload: Dict[str, Any] = Body(...)):
    """Triggers zero-downtime multi-region cluster failover."""
    target_region = payload.get("target_region")
    reason = payload.get("reason", "Manual trigger via admin dashboard")

    if not target_region:
        raise HTTPException(status_code=400, detail="Missing required 'target_region' parameter")

    try:
        res = failover_manager.trigger_manual_failover(target_region=target_region, reason=reason)
        return res
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))
