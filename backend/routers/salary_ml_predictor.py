"""
JobHunt Pro SaaS — AI Salary & Offer Negotiation Predictor Router
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Body
from core.salary_predictor import SalaryNegotiationPredictor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/salary", tags=["AI Salary Negotiation Predictor"])

@router.post("/predict")
async def predict_salary_negotiation_upside(payload: Dict[str, Any] = Body(...)):
    """Predicts counter-offer win probability, target compensation, and tactical playbook."""
    initial_offer_base = payload.get("initial_offer_base")
    if initial_offer_base is None or float(initial_offer_base) <= 0:
        raise HTTPException(status_code=400, detail="Valid 'initial_offer_base' greater than 0 is required")

    initial_offer_equity = float(payload.get("initial_offer_equity", 0.0))
    years_experience = float(payload.get("years_experience", 5.0))
    company_tier = str(payload.get("company_tier", "MID_MARKET"))
    location_tier = str(payload.get("location_tier", "DEFAULT"))
    has_competing_offers = bool(payload.get("has_competing_offers", False))
    competing_offer_base = float(payload.get("competing_offer_base", 0.0))
    role_seniority = str(payload.get("role_seniority", "SENIOR"))

    result = SalaryNegotiationPredictor.predict_offer_upside(
        initial_offer_base=float(initial_offer_base),
        initial_offer_equity=initial_offer_equity,
        years_experience=years_experience,
        company_tier=company_tier,
        location_tier=location_tier,
        has_competing_offers=has_competing_offers,
        competing_offer_base=competing_offer_base,
        role_seniority=role_seniority
    )

    return {
        "status": "success",
        "data": result
    }
