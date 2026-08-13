"""
Web Router for GCC Multi-Currency Invoicing & Payments
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional
from core.gcc_billing import gcc_billing_service

router = APIRouter(prefix="/gcc-billing", tags=["GCC Multi-Currency Billing"])
templates = Jinja2Templates(directory="web/templates")

class GenerateInvoiceRequest(BaseModel):
    client_name: str
    client_vat_id: Optional[str] = "N/A"
    amount_usd: float = Field(..., gt=0)
    currency: Optional[str] = "AED"

@router.post("/generate-invoice")
async def generate_invoice(req: GenerateInvoiceRequest):
    """
    Generates a dual-language (Arabic/English) B2B tax invoice.
    """
    invoice = gcc_billing_service.generate_tax_invoice(
        client_name=req.client_name,
        client_vat_id=req.client_vat_id or "N/A",
        amount_usd=req.amount_usd,
        currency=req.currency or "AED"
    )
    return invoice

@router.get("/invoice-preview", response_class=HTMLResponse)
async def preview_invoice_template(request: Request, client_name: str = "GCC Enterprise Client", amount_usd: float = 149.0, currency: str = "AED"):
    """
    Renders dual Arabic/English invoice template.
    """
    invoice_data = gcc_billing_service.generate_tax_invoice(client_name, "TRN-9988776655", amount_usd, currency)
    return templates.TemplateResponse("invoice_template.html", {"request": request, "invoice": invoice_data})
