"""
JobHunt Pro — Gulf Compensation & Labor Law Oracle Router
API endpoints for GCC salary package breakdowns, EOSB gratuity under Saudi/UAE laws,
and personalized counter-offer letters.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.gulf_comp_oracle import gulf_comp_oracle

router = APIRouter(prefix="/api/v2/compensation", tags=["Gulf Compensation Oracle"])


class PackageCalculationRequest(BaseModel):
    monthly_gross: float = 35000.0
    country: str = "SA"
    years_of_service: Optional[float] = 4.5


class CounterOfferRequest(BaseModel):
    candidate_name: str = "Samir Haddad"
    company_name: str = "Saudi Sovereign Tech"
    role_title: str = "Principal Engineer"
    current_offer_monthly: float = 30000.0
    target_increase_percent: float = 20.0
    currency: str = "SAR"


@router.post("/calculate", response_model=Dict[str, Any])
def calculate_gcc_package_and_eosb(req: PackageCalculationRequest) -> Dict[str, Any]:
    """Calculate basic salary, housing allowance, transport allowance, and projected EOSB."""
    package = gulf_comp_oracle.calculate_gcc_package(
        total_monthly_gross=req.monthly_gross,
        country=req.country
    )

    eosb_data = None
    if req.years_of_service and req.years_of_service > 0:
        basic = package["breakdown"]["basic_salary"]
        eosb_data = gulf_comp_oracle.calculate_saudi_eosb(basic, req.years_of_service)

    return {
        "package_breakdown": package,
        "projected_eosb_gratuity": eosb_data
    }


@router.post("/negotiate-script", response_model=Dict[str, Any])
def generate_negotiation_counter_offer(req: CounterOfferRequest) -> Dict[str, Any]:
    """Generate high-persuasion counter-offer email letter to negotiate salary increase."""
    return gulf_comp_oracle.generate_counter_offer_script(
        candidate_name=req.candidate_name,
        company_name=req.company_name,
        role_title=req.role_title,
        current_offer_monthly=req.current_offer_monthly,
        target_increase_percent=req.target_increase_percent,
        currency=req.currency
    )
