from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import time

router = APIRouter(prefix="/api/white-label", tags=["B2B White-Label Enterprise Portal"])

class TenantConfigRequest(BaseModel):
    agency_name: str
    custom_domain: str
    primary_color: Optional[str] = "#6366f1"
    logo_url: Optional[str] = ""
    monthly_pricing_usd: Optional[float] = 299.0

class CandidateBatchInviteRequest(BaseModel):
    tenant_id: str
    candidates: List[dict] = Field(description="List of candidates with name and email")

@router.post("/tenant/create")
async def create_tenant_config(req: TenantConfigRequest):
    tenant_id = f"tenant_{int(time.time())}"
    return {
        "status": "success",
        "tenant_id": tenant_id,
        "agency_name": req.agency_name,
        "custom_domain": req.custom_domain,
        "cname_target": "domains.jobhuntpro.io",
        "branding": {
            "primary_color": req.primary_color,
            "logo_url": req.logo_url
        },
        "monthly_pricing_usd": req.monthly_pricing_usd
    }

@router.get("/tenant/{tenant_id}")
async def get_tenant_details(tenant_id: str):
    return {
        "tenant_id": tenant_id,
        "agency_name": "Apex Talent Solutions",
        "custom_domain": "portal.apextalent.io",
        "active_clients": 48,
        "monthly_recurring_revenue": 14352.00,
        "status": "active"
    }

@router.post("/tenant/candidates/invite")
async def invite_candidates_batch(req: CandidateBatchInviteRequest):
    """
    Batch invite candidates to a white-labeled agency dashboard under tenant domain.
    """
    if not req.candidates:
        raise HTTPException(status_code=400, detail="Candidates list cannot be empty.")
    
    invited_list = []
    for c in req.candidates:
        invited_list.append({
            "name": c.get("name", "Candidate"),
            "email": c.get("email"),
            "invite_link": f"https://{req.tenant_id}.jobhuntpro.io/onboard?token=inv_{int(time.time())}",
            "status": "invited"
        })
    return {
        "status": "success",
        "tenant_id": req.tenant_id,
        "invited_count": len(invited_list),
        "invitations": invited_list
    }
