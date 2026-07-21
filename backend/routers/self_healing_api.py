"""
JobHunt Pro - Phase 7 Component 2: Self-Healing API Router
"""
from fastapi import APIRouter
from typing import Dict, Any
from core.self_healing import self_healing_engine

router = APIRouter(prefix="/api/v2/self-healing", tags=["Self Healing"])

@router.get("/telemetry")
def get_telemetry() -> Dict[str, Any]:
    return self_healing_engine.get_telemetry()

@router.post("/simulate-error")
def simulate_and_heal() -> Dict[str, Any]:
    try:
        # Simulate transient error
        raise ValueError("Simulated system transient anomaly in async queue")
    except Exception as e:
        event = self_healing_engine.intercept_and_heal(e, context_info="Simulation Test Endpoint")
        return {
            "success": True,
            "message": "Anomaly intercepted and auto-healed silently.",
            "heal_event": event
        }
