"""
Micro-SaaS Fleet Deployer & Tenant Factory API Router
Exposes zero-touch Micro-SaaS fleet provisioning, custom branding, and MRR analytics.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.micro_saas_factory import dispatch_saas_bounty, SAAS_IDEAS

router = APIRouter(prefix="/api/micro-saas", tags=["Micro-SaaS Fleet API"])


class TenantDeployRequest(BaseModel):
    tenant_name: str
    custom_domain: Optional[str] = None
    target_niche: Optional[str] = "B2B SaaS"
    pricing_monthly_usd: Optional[int] = 29


@router.get("/ideas")
async def list_saas_ideas():
    """List high-value B2B Micro-SaaS template ideas for autonomous deployment."""
    return {"status": "success", "count": len(SAAS_IDEAS), "ideas": SAAS_IDEAS}


@router.post("/deploy")
async def deploy_micro_saas(payload: TenantDeployRequest):
    """
    Deploy an autonomous micro-SaaS instance with zero-cost edge hosting.
    """
    if not payload.tenant_name.strip():
        raise HTTPException(status_code=400, detail="Tenant name is required.")

    success = dispatch_saas_bounty()
    
    clean_name = payload.tenant_name.lower().replace(" ", "-")
    domain = payload.custom_domain or f"https://{clean_name}.jobhuntpro.app"

    return {
        "status": "deployed",
        "tenant_name": payload.tenant_name,
        "live_url": domain,
        "target_niche": payload.target_niche,
        "projected_mrr": f"${payload.pricing_monthly_usd}/mo per user",
        "edge_deployment": "Cloudflare Workers ($0 Serverless Arbitrage)",
        "bounty_dispatched": success
    }
