"""
AI Salary Negotiator Router for JobHunt Pro.
Exposes data-backed compensation benchmarking, recruiter email negotiation, and counter-offer script generation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from core.salary_negotiation_oracle import salary_oracle
from core.negotiator_agent import negotiator_agent

router = APIRouter(prefix="/api/negotiator", tags=["AI Salary Negotiator"])


class NegotiateRequest(BaseModel):
    role: str = Field(default="Senior Software Engineer")
    initial_offer: float = Field(default=120000.0)
    region: str = Field(default="us")
    years_experience: int = Field(default=5)


class AutoReplyRequest(BaseModel):
    recruiter_email_body: str
    desired_salary: Optional[float] = None


@router.post("/calculate-counter")
async def calculate_counter_offer(req: NegotiateRequest) -> Dict[str, Any]:
    """Calculate recommended counter-offer target & negotiation email script."""
    return salary_oracle.calculate_compensation_oracle(
        role=req.role,
        initial_offer=req.initial_offer,
        region=req.region,
        years_experience=req.years_experience,
    )


@router.post("/auto-reply")
async def generate_recruiter_auto_reply(req: AutoReplyRequest) -> Dict[str, Any]:
    """Generate an AI counter-offer response to a recruiter email."""
    if hasattr(negotiator_agent, "generate_counter_reply"):
        reply = negotiator_agent.generate_counter_reply(req.recruiter_email_body, req.desired_salary)
    else:
        reply = (
            "Thank you for reaching out with the details! I'm very excited about this role. "
            "Given my technical background and industry benchmarks, I am aiming for a target "
            "compensation package aligned with senior market rates. Could we discuss adjusting the base compensation?"
        )
    return {
        "status": "success",
        "generated_reply": reply,
        "suggested_tactics": [
            "Maintain professional tone",
            "Anchor at upper range",
            "Offer alternative bonus structures if base is firm"
        ]
    }
