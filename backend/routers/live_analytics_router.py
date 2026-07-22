"""
FastAPI Router for Real-Time Autonomous Conversion Analytics Dashboard Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.live_analytics_engine import LiveAnalyticsEngine, get_analytics_engine_status

router = APIRouter(prefix="/api/v2/live-analytics", tags=["Live Conversion Analytics"])

@router.get("/status")
def status_endpoint():
    return get_analytics_engine_status()

@router.get("/metrics/{user_id}")
def metrics_endpoint(user_id: str = "default_user"):
    engine = LiveAnalyticsEngine()
    return engine.compute_conversion_metrics(user_id)
