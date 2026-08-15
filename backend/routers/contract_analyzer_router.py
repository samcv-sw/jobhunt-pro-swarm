"""
Contract Analyzer Router
JobHunt Pro SaaS - REST endpoints for reviewing employment contracts and offer letters against GCC labor law.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from core.gcc_contract_analyzer import gcc_contract_analyzer

router = APIRouter(prefix="/api/v2/contracts/analyzer", tags=["GCC Contract Analyzer"])


class ContractAnalysisRequest(BaseModel):
    contract_text: str = Field(..., min_length=20, description="Employment contract or offer letter text")
    jurisdiction: Optional[str] = Field("saudi_arabia", description="saudi_arabia or uae")
    basic_salary: Optional[float] = Field(None, description="Optional monthly basic salary")


@router.post("/review")
def review_employment_contract(req: ContractAnalysisRequest):
    """Reviews employment contract text against statutory labor laws and flags risks."""
    return gcc_contract_analyzer.analyze_contract(
        contract_text=req.contract_text,
        jurisdiction=req.jurisdiction or "saudi_arabia",
        basic_salary=req.basic_salary
    )
