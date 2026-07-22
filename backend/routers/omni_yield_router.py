"""
FastAPI Router for Autonomous Omni-Yield Financial Monetization Engine.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.omni_yield_monetization import OmniYieldMonetizationEngine, get_omni_yield_status

router = APIRouter(prefix="/api/v2/omni-yield", tags=["Autonomous Omni-Yield Financial Monetization"])

class MicroTxRequest(BaseModel):
    payer_id: str
    service_code: str
    amount_usd: float

@router.get("/status")
def status_endpoint():
    return get_omni_yield_status()

@router.post("/process-microtx")
def process_microtx_endpoint(req: MicroTxRequest):
    engine = OmniYieldMonetizationEngine()
    return engine.process_microtransaction(req.payer_id, req.service_code, req.amount_usd)

@router.get("/yield-split/{monthly_gross_usd}")
def yield_split_endpoint(monthly_gross_usd: float):
    engine = OmniYieldMonetizationEngine()
    return engine.calculate_enterprise_yield_split(monthly_gross_usd)
