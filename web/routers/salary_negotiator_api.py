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
    currency: Optional[str] = "USD"
    offered_bonus: Optional[float] = 0.0
    offered_equity: Optional[float] = 0.0
    competing_offer: Optional[bool] = False
    skills_summary: Optional[str] = ""
    target_percentage: Optional[float] = None
    lang: Optional[str] = "ar"

@router.post("/oracle")
async def calculate_salary_oracle(payload: OracleRequest):
    """
    Data-backed global salary calculation, TC breakdown, multi-tone scripts, and localized PPP.
    """
    from core.salary_negotiation_oracle import salary_oracle
    return salary_oracle.calculate_compensation_oracle(
        role=payload.role,
        initial_offer=payload.initial_offer,
        region=payload.region,
        years_experience=payload.years_experience,
        style=payload.style or "balanced",
        currency=payload.currency or "USD",
        offered_bonus=payload.offered_bonus or 0.0,
        offered_equity=payload.offered_equity or 0.0,
        competing_offer=payload.competing_offer or False,
        skills_summary=payload.skills_summary or "",
        target_percentage=payload.target_percentage,
        lang=payload.lang or "ar"
    )


@router.get("/hiring-velocity")
async def get_hiring_velocity(
    company: str = Query("Google", description="Target company name"),
    role: str = Query("Software Engineer", description="Target job role")
):
    """Predicts hiring velocity, response time, and application ROI."""
    from core.predictive_job_ml import predictive_ml_engine
    return {"status": "success", "analytics": predictive_ml_engine.predict_hiring_velocity_and_roi(company, role)}


class RebuttalRequest(BaseModel):
    role: str = "Senior Engineer"
    target_salary: float = 6500.0
    currency: str = "USD"
    lang: str = "ar"


@router.post("/rebuttal")
async def get_objection_rebuttals(payload: RebuttalRequest):
    """Returns counter-rebuttal scripts for 5 major recruiter objection scenarios."""
    from core.salary_negotiation_oracle import salary_oracle
    return {
        "status": "success",
        "rebuttals": salary_oracle.get_all_objection_rebuttals(
            role=payload.role,
            target_salary=payload.target_salary,
            currency=payload.currency,
            lang=payload.lang
        )
    }



