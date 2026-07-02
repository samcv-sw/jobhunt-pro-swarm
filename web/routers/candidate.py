from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from core.database import db
import logging

from pathlib import Path

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
