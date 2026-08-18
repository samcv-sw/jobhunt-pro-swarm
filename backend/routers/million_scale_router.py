"""
backend/routers/million_scale_router.py - Hyperscale Architecture & Concurrency Router
======================================================================================
Provides live metrics, health status, and cache management for handling 1M+ users.
"""

import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Query, Response

from core.million_scale_engine import (
    get_million_scale_metrics,
    global_cache,
    global_ingestor,
    global_load_shedder,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hyperscale", tags=["Hyperscale Architecture"])

@router.get("/metrics")
async def get_hyperscale_metrics(response: Response) -> Dict[str, Any]:
    """Returns real-time concurrency metrics, memory cache hit ratios, and batch buffer state."""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["X-Hyperscale-Tier"] = "Million-User-Ready"
    return get_million_scale_metrics()

@router.post("/buffer/flush")
async def flush_hyperscale_buffer() -> Dict[str, Any]:
    """Force flush all buffered in-memory transactions into the database."""
    flushed = global_ingestor.flush()
    return {
        "status": "flushed",
        "flushed_count": flushed,
        "remaining": len(global_ingestor._queue)
    }

@router.get("/cache/stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get high-velocity L1 in-memory cache performance statistics."""
    return global_cache.stats()

@router.get("/load/status")
async def get_load_status() -> Dict[str, Any]:
    """Get current active concurrency capacity and headroom percentage."""
    return global_load_shedder.stats()
