import logging
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from core.singularity_hyper_booster import hyper_booster

logger = logging.getLogger("singularity_hyper_router")

router = APIRouter(prefix="/api/v1/hyper-boost", tags=["Singularity Hyper Boost"])

@router.post("/trigger", response_model=Dict[str, Any])
async def trigger_hyper_boost_optimization() -> Dict[str, Any]:
    """Triggers real-time maximum memory cleanup, regex pre-compilation, and engine boost."""
    try:
        result = await hyper_booster.execute_hyper_boost_sequence()
        return result
    except Exception as e:
        logger.error(f"Hyper boost error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=Dict[str, Any])
async def get_hyper_boost_status() -> Dict[str, Any]:
    """Returns current hyper booster stats and memory health."""
    return {
        "status": "active",
        "cached_regex_patterns": len(hyper_booster._compiled_regex_cache),
        "total_optimizations": hyper_booster._optimizations_applied,
        "engine_level": "GOD_TIER_MAXIMUM"
    }
