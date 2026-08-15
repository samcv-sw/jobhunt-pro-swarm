"""
GCC Compensation Radar Router
JobHunt Pro SaaS - REST endpoints for executive compensation, allowances, EOSB, and savings projections.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

from core.gcc_compensation_radar import gcc_compensation_radar

router = APIRouter(prefix="/api/v2/compensation/radar", tags=["GCC Compensation Radar"])


class CompensationCalculationRequest(BaseModel):
    basic_salary: float = Field(25000.0, gt=1000.0, description="Monthly basic salary")
    company_key: Optional[str] = Field("aramco", description="aramco, neom, emirates_tech, alrajhi")
    years_of_service: Optional[int] = Field(5, ge=1, le=40, description="Years of service")
    num_children: Optional[int] = Field(2, ge=0, le=10, description="Children count")
    estimated_monthly_expenses: Optional[float] = Field(12000.0, ge=0.0, description="Estimated living cost")


@router.post("/calculate")
def calculate_compensation_radar(req: CompensationCalculationRequest):
    """Calculates granular package breakdown, benefits, EOSB, and savings projection."""
    return gcc_compensation_radar.compute_full_package(
        basic_salary=req.basic_salary,
        company_key=req.company_key or "aramco",
        years_of_service=req.years_of_service or 5,
        num_children=req.num_children if req.num_children is not None else 2,
        estimated_monthly_expenses=req.estimated_monthly_expenses or 12000.0
    )
