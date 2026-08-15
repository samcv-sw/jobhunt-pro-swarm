"""
B2B White-Label Multi-Tenant Router
JobHunt Pro SaaS - REST endpoints for custom-branded portal provisioning & resolving.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional

from core.whitelabel_multi_tenant import whitelabel_engine

router = APIRouter(prefix="/api/v2/whitelabel", tags=["B2B White-Label & Multi-Tenant"])


class TenantRegistrationRequest(BaseModel):
    org_name: str = Field(..., description="Organization or Agency Name")
    admin_email: str = Field(..., description="Admin Email")
    desired_subdomain: str = Field(..., description="Subdomain prefix")
    primary_color: Optional[str] = Field("#00f0ff", description="Brand HEX Color")
    seats_quota: Optional[int] = Field(250, ge=10, le=10000)


@router.get("/resolve/{slug}")
def resolve_tenant(slug: str):
    """Resolves white-label branding, logo, and theme tokens by tenant slug."""
    return whitelabel_engine.get_tenant_config(slug)


@router.post("/register")
def register_tenant(req: TenantRegistrationRequest):
    """Provisions a new custom-branded agency or university portal."""
    return whitelabel_engine.register_new_tenant(
        org_name=req.org_name,
        admin_email=req.admin_email,
        desired_subdomain=req.desired_subdomain,
        primary_color=req.primary_color or "#00f0ff",
        seats_quota=req.seats_quota or 250
    )
