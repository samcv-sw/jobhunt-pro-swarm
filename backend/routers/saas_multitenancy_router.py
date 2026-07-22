"""
FastAPI Router for Multi-Tenant Enterprise B2B SaaS Engine & Autonomous Billing.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from core.saas_multitenancy import SaaSMultiTenancyEngine, get_multitenancy_status

router = APIRouter(prefix="/api/v2/saas", tags=["Multi-Tenant B2B SaaS & Billing"])

class ProvisionRequest(BaseModel):
    org_name: str
    admin_email: str
    tier: Optional[str] = "professional"

class UsageDeductionRequest(BaseModel):
    tenant_id: str
    current_credits: int
    usage_cost: Optional[int] = 1

class CheckoutSessionRequest(BaseModel):
    tenant_id: str
    tier: str

@router.get("/status")
def status_endpoint():
    return get_multitenancy_status()

@router.post("/provision")
def provision_tenant_endpoint(req: ProvisionRequest):
    engine = SaaSMultiTenancyEngine()
    return engine.provision_tenant(req.org_name, req.admin_email, req.tier or "professional")

@router.post("/deduct-credits")
def deduct_credits_endpoint(req: UsageDeductionRequest):
    engine = SaaSMultiTenancyEngine()
    return engine.deduct_usage_credits(req.tenant_id, req.current_credits, req.usage_cost or 1)

@router.post("/create-checkout-session")
def create_checkout_endpoint(req: CheckoutSessionRequest):
    engine = SaaSMultiTenancyEngine()
    return engine.generate_stripe_invoice_session(req.tenant_id, req.tier)
