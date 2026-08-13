"""
Web Router for AI SDR Reply Intelligence & Copilot
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from core.reply_sentiment import reply_sentiment_service

router = APIRouter(prefix="/reply-copilot", tags=["AI Reply Intelligence"])
templates = Jinja2Templates(directory="web/templates")

class ClassifyReplyRequest(BaseModel):
    reply_text: str

@router.get("/inbox", response_class=HTMLResponse)
async def get_reply_copilot_page(request: Request):
    """
    Renders AI Reply Copilot Inbox UI.
    """
    return templates.TemplateResponse("reply_copilot.html", {"request": request, "title": "AI SDR Reply Copilot"})

@router.post("/classify")
async def classify_prospect_reply(req: ClassifyReplyRequest):
    """
    Analyzes prospect reply and returns sentiment, category, and AI draft reply.
    """
    res = reply_sentiment_service.classify_reply(req.reply_text)
    return res
