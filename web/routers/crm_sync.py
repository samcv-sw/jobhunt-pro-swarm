"""
Web Router for Enterprise CRM Integrations & Webhook Dispatching
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from core.crm_service import crm_service

router = APIRouter(prefix="/crm", tags=["CRM Integrations"])
templates = Jinja2Templates(directory="web/templates")

class CRMExportRequest(BaseModel):
    provider: str = Field(..., description="hubspot | pipedrive | webhook")
    api_key: Optional[str] = None
    webhook_url: Optional[str] = None
    secret: Optional[str] = None
    domain: Optional[str] = None
    lead: Dict[str, Any]

@router.get("/integrations", response_class=HTMLResponse)
async def get_crm_integrations_page(request: Request):
    """
    Renders CRM Integrations Dashboard with RTL/LTR support.
    """
    return templates.TemplateResponse("crm_integrations.html", {"request": request, "title": "Enterprise CRM Integrations"})

@router.post("/export")
async def export_lead_to_crm(req: CRMExportRequest):
    """
    Exports lead to selected CRM provider or dispatches a webhook.
    """
    provider = req.provider.lower()
    if provider == "hubspot":
        res = crm_service.export_to_hubspot(req.api_key or "", req.lead)
    elif provider == "pipedrive":
        res = crm_service.export_to_pipedrive(req.api_key or "", req.domain or "", req.lead)
    elif provider == "webhook":
        res = crm_service.dispatch_webhook(req.webhook_url or "", req.secret or "", "lead.converted", req.lead)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported CRM provider: {provider}")

    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "CRM Export failed"))
    return res
