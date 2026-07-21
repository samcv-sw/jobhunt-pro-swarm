"""
Salary Negotiator API Router
Exposes salary benchmark lookup, negotiation advice, and counter-offer email drafting.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from core.salary_negotiator import salary_negotiator

router = APIRouter(prefix="/api/salary-negotiator", tags=["Salary Negotiator API"])


class NegotiationAdviceRequest(BaseModel):
    location: str = "dubai"
    level: str = "senior"
    offered_salary: Optional[int] = None
    company_name: Optional[str] = None


@router.get("/benchmark")
async def get_salary_benchmark(
    location: str = Query("dubai", description="Location name (dubai, lebanon, saudi_arabia, qatar, remote)"),
    level: str = Query("senior", description="Seniority level (junior, mid, senior, lead)")
):
    """Get salary benchmarks for specific location and level."""
    return salary_negotiator.get_range(location=location, level=level)


@router.get("/compare")
async def compare_all_locations(level: str = Query("senior")):
    """Compare salary ranges across all supported regions."""
    return salary_negotiator.compare_locations(level=level)


@router.post("/advice")
async def get_advice(payload: NegotiationAdviceRequest):
    """Get personalized negotiation strategy, counter-offer template, and tips."""
    advice = salary_negotiator.get_negotiation_advice(
        location=payload.location,
        offered=payload.offered_salary,
        level=payload.level
    )
    if payload.company_name and "response_template" in advice:
        advice["response_template"] = advice["response_template"].replace("this role", f"the role at {payload.company_name}")
    return advice

class OracleRequest(BaseModel):
    role: str = "Senior Engineer"
    initial_offer: float = 120000.0
    region: str = "us"
    years_experience: int = 5
    style: str = "balanced"

@router.post("/oracle")
async def calculate_salary_oracle(payload: OracleRequest):
    """
    Data-backed global salary calculation, benchmark calculation, and counter-offer script with localized PPP.
    """
    from core.salary_negotiation_oracle import salary_oracle
    return salary_oracle.calculate_compensation_oracle(
        role=payload.role,
        initial_offer=payload.initial_offer,
        region=payload.region,
        years_experience=payload.years_experience,
        style=payload.style
    )


@router.get("/hiring-velocity")
async def get_hiring_velocity(
    company: str = Query("Google", description="Target company name"),
    role: str = Query("Software Engineer", description="Target job role")
):
    """Predicts hiring velocity, response time, and application ROI."""
    from core.predictive_job_ml import predictive_ml_engine
    return {"status": "success", "analytics": predictive_ml_engine.predict_hiring_velocity_and_roi(company, role)}


