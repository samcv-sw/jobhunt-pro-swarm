from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from services.cold_outreach_service import cold_outreach_service, OutreachSequenceRequest

router = APIRouter(tags=["AI SDR Outreach Web"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/ai-sdr-outreach", response_class=HTMLResponse)
async def get_ai_sdr_outreach_page(request: Request):
    return templates.TemplateResponse(request, "ai_sdr_outreach.html", {"title": "AI SDR Recruiter Outreach | JobHunt Pro"})

@router.post("/api/outreach/generate-sequence")
async def generate_outreach_sequence(req: OutreachSequenceRequest):
    """Generate multi-step cold outreach sequence for recruiters."""
    result = cold_outreach_service.generate_sequence(req)
    return result

@router.get("/api/outreach/contacts/search")
async def search_recruiter_contacts(company: str = "TechCorp Global", role: str = "Engineering Lead"):
    """Search hiring manager and recruiter contact info."""
    contacts = cold_outreach_service.search_target_contacts(company, role)
    return {
        "status": "success",
        "company": company,
        "role": role,
        "contacts": contacts
    }

class SocialCampaignRequest(BaseModel):
    recruiter_name: str
    company: str
    target_role: str
    platform: Optional[str] = "linkedin"
    calendar_link: Optional[str] = "https://calendly.com/candidate/interview"

@router.post("/api/outreach/social-campaign")
async def generate_social_campaign(req: SocialCampaignRequest):
    """Generate multi-channel social cold outreach payload (LinkedIn, WhatsApp, Email)."""
    from core.autonomous_social_outreach import social_outreach
    return social_outreach.generate_outreach_campaign(
        recruiter_name=req.recruiter_name,
        company=req.company,
        target_role=req.target_role,
        platform=req.platform or "linkedin",
        calendar_link=req.calendar_link or "https://calendly.com/candidate/interview"
    )

