"""
FastAPI Router for Dynamic Revenue & Algorithmic Pricing Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.sovereign_revenue_engine import SovereignRevenueEngine, get_revenue_engine_status

router = APIRouter(prefix="/api/v2/revenue-engine", tags=["Dynamic Revenue & Algorithmic Pricing Engine"])

class PricingRequest(BaseModel):
    base_price_usd: float
    region: Optional[str] = "US"

@router.get("/status")
def status_endpoint():
    return get_revenue_engine_status()

@router.post("/calculate-pricing")
def calculate_pricing_endpoint(req: PricingRequest):
    engine = SovereignRevenueEngine()
    return engine.calculate_localized_pricing(req.base_price_usd, req.region or "US")

@router.post("/retention-offer/{user_id}")
def retention_offer_endpoint(user_id: str):
    engine = SovereignRevenueEngine()
    return engine.trigger_retention_discount(user_id)
