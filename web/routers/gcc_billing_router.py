"""
Web Router for GCC Multi-Currency Invoicing, GCC Checkout Sessions & BNPL Payment Gateways
(Mada, Apple Pay, KNET, Tamara, Tabby with localized SAR/AED pricing)
"""

from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from core.gcc_billing import gcc_billing_service
from core.gcc_unified_checkout import gcc_unified_checkout, COUNTRY_PPP_CONFIG, BASE_PRICING

router = APIRouter(tags=["GCC Multi-Currency Billing & Checkout"])
templates = Jinja2Templates(directory="web/templates")

class GenerateInvoiceRequest(BaseModel):
    client_name: str
    client_vat_id: Optional[str] = "N/A"
    amount_usd: float = Field(..., gt=0)
    currency: Optional[str] = "AED"

@router.post("/gcc-billing/generate-invoice")
async def generate_invoice(req: GenerateInvoiceRequest):
    """Generates a dual-language (Arabic/English) B2B tax invoice."""
    invoice = gcc_billing_service.generate_tax_invoice(
        client_name=req.client_name,
        client_vat_id=req.client_vat_id or "N/A",
        amount_usd=req.amount_usd,
        currency=req.currency or "AED"
    )
    return invoice

@router.get("/gcc-billing/invoice-preview", response_class=HTMLResponse)
async def preview_invoice_template(
    request: Request,
    client_name: str = "GCC Enterprise Client",
    amount_usd: float = 149.0,
    currency: str = "AED"
):
    """Renders dual Arabic/English invoice template."""
    invoice_data = gcc_billing_service.generate_tax_invoice(client_name, "TRN-9988776655", amount_usd, currency)
    return templates.TemplateResponse("invoice_template.html", {"request": request, "invoice": invoice_data})


class CurrencyConvertRequest(BaseModel):
    amount_usd: float = Field(..., gt=0, description="Amount in USD")
    target_currency: str = Field(default="SAR", description="Target GCC currency: SAR, AED, KWD, QAR, BHD, OMR, USD")


@router.post("/gcc-billing/convert-pricing")
def convert_gcc_pricing(req: CurrencyConvertRequest):
    """Converts standard SaaS USD pricing into localized GCC currency with VAT calculation."""
    pricing = gcc_billing_service.convert_price(req.amount_usd, req.target_currency)
    return {
        "status": "success",
        "pricing": pricing
    }


@router.get("/gcc-billing/supported-currencies")
def get_supported_currencies():
    """Returns available GCC currencies, symbols, exchange rates, and VAT regulations."""
    return {
        "status": "success",
        "rates": gcc_billing_service.RATES_TO_USD,
        "symbols": gcc_billing_service.CURRENCY_SYMBOLS,
        "vat_rates": gcc_billing_service.COUNTRY_VAT_RATES
    }


# ── GCC Unified Checkout & BNPL Endpoints ────────────────────────────────────

class GCCCheckoutSessionRequest(BaseModel):
    plan_id: str = Field(default="pro", description="Pricing tier: starter, pro, enterprise_god, etc.")
    country_code: str = Field(default="SA", description="GCC ISO 2-letter country code: SA, AE, KW, QA, BH, OM")
    payment_method: str = Field(default="mada", description="Payment method: mada, apple_pay, knet, tamara, tabby, tap, moyasar")
    user_email: Optional[str] = Field(default="customer@jobhuntpro.io", description="User email for receipt and session link")


@router.post("/api/v2/checkout/gcc-session")
async def create_gcc_checkout_session(req: GCCCheckoutSessionRequest):
    """
    Creates localized GCC checkout session supporting Mada, KNET, Apple Pay,
    Tamara (4 installments), Tabby (4 split payments), and Tap Payments.
    """
    try:
        session = gcc_unified_checkout.generate_gcc_checkout_session(
            plan_id=req.plan_id,
            country_code=req.country_code,
            payment_method=req.payment_method,
            user_email=req.user_email or "customer@jobhuntpro.io"
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/v2/checkout/gcc-webhook")
async def handle_gcc_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_tap_signature: Optional[str] = Header(None, alias="X-Tap-Signature")
):
    """
    Handles GCC payment gateway webhooks (Tap, Moyasar, Tamara, Tabby)
    with HMAC-SHA256 signature verification and atomic wallet crediting.
    """
    body_bytes = await request.body()
    sig = x_signature or x_tap_signature or ""
    
    res = gcc_unified_checkout.process_gcc_webhook(
        raw_payload=body_bytes,
        signature_header=sig
    )

    if not res.get("success"):
        return JSONResponse(status_code=400, content=res)

    try:
        from core.telegram_alerts import alert_payment_received
        alert_payment_received(
            amount=float(res.get("amount_local", 0.0)),
            currency=str(res.get("currency", "SAR")),
            plan="GCC Localized Checkout",
            customer_email="",
            payment_method=f"GCC Gateway ({res.get('currency', 'SAR')})",
            transaction_id=str(res.get("session_id", "")),
        )
    except Exception as alert_err:
        logger.debug(f"[handle_gcc_webhook] Payment alert skipped: {alert_err}")

    return res


@router.get("/api/v2/checkout/gcc-methods")
def get_gcc_payment_methods(country_code: str = "SA"):
    """Returns supported payment methods, localized currency, and BNPL parameters for a country."""
    c_code = country_code.upper()
    country_info = COUNTRY_PPP_CONFIG.get(c_code, COUNTRY_PPP_CONFIG["SA"])
    sample_pricing = gcc_unified_checkout.calculate_localized_pricing("pro", c_code)

    return {
        "status": "success",
        "country_code": c_code,
        "country_name": country_info["country"],
        "currency": country_info["currency"],
        "exchange_rate_to_usd": country_info["rate_to_usd"],
        "vat_rate_percent": int(country_info.get("vat_rate", 0.0) * 100),
        "supported_methods": country_info["methods"],
        "bnpl_available": "tamara" in country_info["methods"] or "tabby" in country_info["methods"],
        "sample_pro_pricing": sample_pricing
    }
