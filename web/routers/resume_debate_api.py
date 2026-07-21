"""
Resume Debate Swarm API Router
Exposes 3-Agent Council CV debate & ATS score optimization endpoints.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.resume_debate_swarm import resume_debate_swarm

router = APIRouter(prefix="/api/resume-debate", tags=["Resume Debate Swarm"])


class DebateRequest(BaseModel):
    resume_text: str
    job_description: str
    target_role: Optional[str] = "Senior Engineer"


@router.post("/run")
async def run_resume_debate(payload: DebateRequest):
    """
    Triggers 3-agent debate (Skeptic, ATS Specialist, Hiring Manager) to evaluate and refine CV.
    """
    if not payload.resume_text.strip() or not payload.job_description.strip():
        raise HTTPException(status_code=400, detail="Resume text and Job Description cannot be empty.")

    results = resume_debate_swarm.run_debate(
        resume_text=payload.resume_text,
        job_description=payload.job_description
    )
    return results
