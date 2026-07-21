import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates

from core.database import db

logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/p/{candidate_id}")
async def view_candidate_profile(request: Request, candidate_id: str):
    """
    VIRAL HONEYPOT:
    The bot submits this URL to job applications instead of a raw PDF.
    When the HR manager opens it, they see the candidate's CV, but they ALSO
    see a banner advertising JobHunt Pro.
    """
    async with db.pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT name, email, phone FROM users WHERE user_id = $1", candidate_id
        )
        if not user:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # In a real scenario, we'd fetch their parsed CV JSON here.
        # For now, we mock the CV data.
        cv_data = {
            "name": user["name"],
            "title": "Senior Network Engineer",
            "experience": "15+ Years",
            "skills": ["Cisco", "Fortinet", "Python", "BGP", "OSPF", "Zero Trust"],
        }

    return templates.TemplateResponse(
        request, "candidate_profile.html", {"cv": cv_data}
    )


# ── Dynamic ATS, Mock Interview & Multi-Lang Endpoints ──────────

from pydantic import BaseModel
from typing import Optional
from core.ats_matcher import api_ats_score
from core.interview_prep import InterviewPrep

class ATSScoreRequest(BaseModel):
    resume_text: str
    job_description: str

class MockInterviewRequest(BaseModel):
    job_title: Optional[str] = ""
    job_description: Optional[str] = ""
    count: Optional[int] = 5

@router.post("/api/ats/score")
async def calculate_ats_score(payload: ATSScoreRequest):
    """Calculate 0-100% real-time ATS match score."""
    res = await api_ats_score(payload.resume_text, payload.job_description)
    return res

@router.post("/api/candidate/mock-interview")
async def generate_mock_interview(payload: MockInterviewRequest):
    """Generate tailored mock interview questions for candidate preparation."""
    questions = InterviewPrep.generate_custom_mock_interview(
        job_title=payload.job_title,
        job_description=payload.job_description,
        count=payload.count or 5
    )
    return {"questions": questions}
