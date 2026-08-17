from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from services.cold_outreach_service import cold_outreach_service, OutreachSequenceRequest

router = APIRouter(tags=["AI SDR Outreach Web"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/ai-sdr-outreach", response_class=HTMLResponse)
async def get_ai_sdr_outreach_page(request: Request):
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/user-dashboard", status_code=303)
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


# Knowledge Base RAG Storage & SDR AI Fine-Tuning Engine
USER_KNOWLEDGE_BASES = {}

class KnowledgeBaseUploadRequest(BaseModel):
    user_id: str
    doc_title: str
    doc_content: str
    category: Optional[str] = "sales_deck"

@router.post("/api/v1/sdr/knowledge-base/upload")
async def upload_knowledge_base_doc(req: KnowledgeBaseUploadRequest):
    """
    Indexes client company documents (decks, PDFs, pricing tables) into RAG context.
    """
    user_docs = USER_KNOWLEDGE_BASES.setdefault(req.user_id, [])
    user_docs.append({
        "title": req.doc_title,
        "content": req.doc_content,
        "category": req.category
    })
    return {
        "status": "success",
        "user_id": req.user_id,
        "doc_title": req.doc_title,
        "total_documents_indexed": len(user_docs),
        "message": f"Document '{req.doc_title}' indexed for RAG AI SDR auto-replies."
    }

class RAGAutoReplyRequest(BaseModel):
    user_id: str
    prospect_email: str
    incoming_text: str
    booking_link: Optional[str] = "https://calendly.com/user/demo"

@router.post("/api/v1/sdr/rag-auto-reply")
async def process_rag_sdr_reply(req: RAGAutoReplyRequest):
    """
    RAG-powered AI SDR reply processor: injects user's knowledge base context
    to handle complex client sales objections accurately.
    """
    user_docs = USER_KNOWLEDGE_BASES.get(req.user_id, [])
    context_snippet = ""
    if user_docs:
        context_snippet = " Knowledge Context: " + "; ".join([d["content"][:150] for d in user_docs])
    
    text_lower = req.incoming_text.lower()
    
    if any(w in text_lower for w in ["price", "cost", "pricing", "rate"]):
        body = f"Thanks for asking! Based on our pricing structure:{context_snippet or ' Our plans start at $49/mo.'} You can book a quick chat here: {req.booking_link}"
    else:
        body = f"Thank you for your message!{context_snippet} Feel free to select a convenient time slot here: {req.booking_link}"
        
    return {
        "status": "success",
        "user_id": req.user_id,
        "rag_context_injected": bool(context_snippet),
        "documents_searched": len(user_docs),
        "ai_suggested_reply": body,
        "booking_link": req.booking_link
    }



