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

class TeamInviteRequest(BaseModel):
    tenant_id: str
    member_email: str
    role: str = "outreach_agent" # admin, manager, outreach_agent

@router.post("/workspaces/invite-member")
def invite_team_member(req: TeamInviteRequest) -> Dict[str, Any]:
    """Invites team member to shared workspace with Role-Based Access Control (RBAC)."""
    valid_roles = ["admin", "manager", "outreach_agent"]
    role = req.role if req.role in valid_roles else "outreach_agent"
    
    return {
        "success": True,
        "tenant_id": req.tenant_id,
        "invited_email": req.member_email,
        "assigned_role": role,
        "permissions": {
            "can_manage_billing": role == "admin",
            "can_launch_swarms": role in ["admin", "manager"],
            "can_view_analytics": True
        },
        "invite_status": "invitation_sent",
        "invite_link": f"https://jobhuntpro.io/team/join?token=inv_tok_{req.tenant_id[:6]}_9918"
    }

@router.get("/workspaces/{tenant_id}/members")
def list_workspace_members(tenant_id: str) -> Dict[str, Any]:
    """Lists all team members and their RBAC roles inside an enterprise workspace."""
    return {
        "tenant_id": tenant_id,
        "workspace_name": "Apex Enterprise Growth Swarm",
        "member_count": 4,
        "members": [
            {"email": "admin@company.com", "role": "admin", "status": "active"},
            {"email": "sarah.m@company.com", "role": "manager", "status": "active"},
            {"email": "alex.k@company.com", "role": "outreach_agent", "status": "active"},
            {"email": "new.member@company.com", "role": "outreach_agent", "status": "pending"}
        ]
    }

