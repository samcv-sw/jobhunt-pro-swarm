"""
ZATCA E-Invoice Router
JobHunt Pro SaaS - Endpoints for generating Saudi Tax Invoices & TLV QR Codes.
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from core.zatca_einvoice_engine import zatca_einvoice_engine

router = APIRouter(prefix="/api/v2/invoices/zatca", tags=["ZATCA Saudi E-Invoicing"])


class InvoiceGenerationRequest(BaseModel):
    customer_name: str = Field("Client Name", description="Customer Name")
    customer_email: str = Field("client@example.com", description="Customer Email")
    item_description: str = Field("JobHunt Pro VIP Lifetime Career Pass", description="Purchased package")
    net_amount_sar: float = Field(199.0, gt=0.0, description="Amount in SAR before VAT")
    payment_method: Optional[str] = Field("Mada / Apple Pay", description="Payment gateway")
    reference_tx_id: Optional[str] = Field(None, description="Transaction ID")


@router.post("/generate")
def create_zatca_tax_invoice(req: InvoiceGenerationRequest):
    """Generates a certified Saudi ZATCA compliant e-invoice with TLV QR Code."""
    return zatca_einvoice_engine.generate_tax_invoice(
        customer_name=req.customer_name,
        customer_email=req.customer_email,
        item_description=req.item_description,
        net_amount_sar=req.net_amount_sar,
        payment_method=req.payment_method or "Mada / Apple Pay",
        reference_tx_id=req.reference_tx_id
    )
