"""
GCC Dialect AI Interviewer Router
JobHunt Pro SaaS - Endpoints for Regional Hiring Personas & Behavioral Probing
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

from core.gcc_dialect_interviewer import gcc_dialect_interviewer

router = APIRouter(prefix="/api/v2/interview/gcc-personas", tags=["GCC Dialect Interviewer"])


@router.get("/list")
def list_personas():
    """Lists all available GCC corporate personas (Saudi Executive, Emirati Tech Lead, etc.)."""
    return gcc_dialect_interviewer.get_available_personas()


@router.get("/generate-round")
def get_interview_round(
    persona: str = Query("saudi_executive", description="Persona key"),
    role: str = Query("Enterprise Cloud Architect", description="Candidate target role"),
    round_num: int = Query(1, ge=1, le=10, description="Round number")
):
    """Generates authentic dialectal greeting, interview question, and evaluation framework."""
    return gcc_dialect_interviewer.generate_interview_round(
        persona_key=persona,
        candidate_role=role,
        round_number=round_num
    )
