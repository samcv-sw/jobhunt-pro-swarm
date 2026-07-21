"""
tenants.py — Multi-Tenant Enterprise Agency White-Labeling Router.
Allows agencies to customize brand identity, domains, fonts, and subscription pricing for JobHunt Pro.
"""

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

router = APIRouter(tags=["Multi-Tenant White-Labeling"])

class TenantCreateRequest(BaseModel):
    agency_name: str = Field(..., description="Recruitment Agency / Corporate Name")
    custom_domain: str = Field(..., description="White-labeled domain e.g., portal.agency.com")
    primary_color: str = Field(default="#0D9488", description="Primary brand accent color")
    font_family: str = Field(default="Cairo", description="Typography e.g., Cairo, Tajawal, IBM Plex Arabic")
    logo_url: Optional[str] = Field(default="https://jobhuntpro.io/static/tenant_default_logo.png")
    monthly_plan_price: float = Field(default=99.0, ge=10.0)

# Memory store for active enterprise tenants
TENANTS_STORE: Dict[str, Dict[str, Any]] = {
    "default": {
        "tenant_id": "tenant_default",
        "agency_name": "JobHunt Pro Global",
        "custom_domain": "jobhuntpro.io",
        "primary_color": "#2563EB",
        "font_family": "Cairo",
        "logo_url": "/static/img/logo.png",
        "monthly_plan_price": 49.0,
        "is_active": True
    }
}

from services.tenant_service import tenant_service

@router.post("/api/tenants/create")
async def create_white_label_tenant(payload: TenantCreateRequest):
    """Register a new white-labeled enterprise agency portal."""
    clean_domain = payload.custom_domain.lower().replace("www.", "")
    tenant_data = tenant_service.register_tenant(
        agency_name=payload.agency_name,
        domain=payload.custom_domain,
        primary_color=payload.primary_color,
        font_family=payload.font_family,
        logo_url=payload.logo_url or ""
    )
    TENANTS_STORE[clean_domain] = tenant_data
    
    return {
        "status": "success",
        "message": f"Enterprise White-Label Tenant [{payload.agency_name}] initialized successfully.",
        "tenant": tenant_data,
        "cname_setup": {
            "record_type": "CNAME",
            "host": payload.custom_domain,
            "target": "cname.jobhuntpro.io"
        }
    }

@router.get("/api/tenants/config")
async def get_tenant_configuration(domain: str = Query(default="jobhuntpro.io")):
    """Lookup white-label tenant styling & settings by incoming request domain."""
    clean_domain = domain.lower().replace("www.", "")
    tenant = TENANTS_STORE.get(clean_domain) or tenant_service._tenants.get(clean_domain) or TENANTS_STORE["default"]
    
    return {
        "status": "success",
        "tenant": tenant,
        "css_variables": {
            "--primary-color": tenant.get("primary_color", "#2563EB"),
            "--font-family": f"'{tenant.get('font_family', 'Cairo')}', sans-serif",
            "--direction": "rtl"
        }
    }

@router.get("/api/tenants/list")
async def list_enterprise_tenants():
    """List all registered agency tenants."""
    unique_tenants = list({t["tenant_id"]: t for t in TENANTS_STORE.values()}.values())
    return {
        "status": "success",
        "count": len(unique_tenants),
        "tenants": unique_tenants
    }
