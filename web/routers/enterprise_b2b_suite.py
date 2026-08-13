"""
Enterprise B2B Suite Router (Omni-Suite 2026)
Handles multi-tenant B2B organization workspaces, RBAC role management, candidate pool sharing, and enterprise recruiting analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Optional
import datetime
import uuid

router = APIRouter(prefix="/api/v2/b2b", tags=["Multi-Tenant Enterprise B2B Suite"])

class OrganizationInfo(BaseModel):
    org_id: str
    org_name: str
    domain: str
    plan: str = "Enterprise-Omni"
    max_seats: int = 50
    active_seats: int = 12

class TeamMember(BaseModel):
    user_id: str
    name: str
    email: str
    role: str # Owner, Admin, Recruiter, Member
    status: str # Active, Pending

class InviteMemberRequest(BaseModel):
    email: str
    role: str = "Recruiter"
    department: str = "Talent Acquisition"

@router.get("/organization", response_model=OrganizationInfo)
async def get_organization_profile():
    """
    Returns enterprise organization workspace details and active subscription limits.
    """
    return OrganizationInfo(
        org_id="org_enterprise_9901",
        org_name="Global Tech Staffing & Careers",
        domain="globaltechstaffing.com",
        plan="Enterprise-Omni",
        max_seats=100,
        active_seats=18
    )

@router.get("/team", response_model=List[TeamMember])
async def get_team_members():
    """
    Lists active team members and RBAC role assignments for the organization workspace.
    """
    return [
        TeamMember(
            user_id="user_admin_01",
            name="Sarah Jenkins",
            email="s.jenkins@globaltechstaffing.com",
            role="Owner",
            status="Active"
        ),
        TeamMember(
            user_id="user_recruiter_02",
            name="Alexander Vance",
            email="a.vance@globaltechstaffing.com",
            role="Recruiter",
            status="Active"
        ),
        TeamMember(
            user_id="user_recruiter_03",
            name="Laila Al-Hassan",
            email="l.alhassan@globaltechstaffing.com",
            role="Recruiter",
            status="Active"
        )
    ]

@router.post("/invite")
async def invite_team_member(req: InviteMemberRequest):
    """
    Invites a recruiter or admin to the multi-tenant organization portal.
    """
    if req.role not in ["Admin", "Recruiter", "Member"]:
        raise HTTPException(status_code=400, detail="Invalid RBAC role. Must be Admin, Recruiter, or Member.")

    invite_token = f"inv_{uuid.uuid4().hex[:12]}"
    
    return {
        "status": "invited",
        "email": req.email,
        "role": req.role,
        "department": req.department,
        "invite_token": invite_token,
        "invited_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@router.get("/candidate-pool")
async def get_shared_candidate_pool(limit: int = 10, role_filter: Optional[str] = None):
    """
    Retrieves the shared candidate pool with ATS scores for recruitment agents and HR teams.
    """
    candidates = [
        {
            "candidate_id": f"cand_{i}",
            "name": f"Candidate Profile {i}",
            "primary_role": role_filter or ("Senior Full-Stack Engineer" if i % 2 == 0 else "DevOps & Cloud Lead"),
            "ats_match_score": 96.5 - (i * 0.5),
            "status": "Available",
            "top_skills": ["Python", "FastAPI", "React", "Docker", "AWS"],
            "last_active": "2 hours ago"
        }
        for i in range(1, limit + 1)
    ]
    return {
        "organization": "Global Tech Staffing & Careers",
        "total_candidates": len(candidates),
        "candidate_pool": candidates
    }


class AgencyWorkspaceCreateRequest(BaseModel):
    agency_name: str
    primary_admin_email: str
    billing_plan: str = "Agency-Pro-299"  # $299/month
    requested_seats: int = 5

@router.post("/agency-workspace")
async def create_or_get_agency_workspace(req: AgencyWorkspaceCreateRequest):
    """
    Agency B2B Workspace ($299/mo Tier): Provisions 5+ recruiter seats,
    25,000 shared AI outreach tokens, and candidate pool synchronization.
    """
    workspace_id = f"ag_ws_{uuid.uuid4().hex[:10]}"
    return {
        "status": "success",
        "workspace_id": workspace_id,
        "agency_name": req.agency_name,
        "billing_plan": req.billing_plan,
        "monthly_price_usd": 299.00,
        "allocated_seats": req.requested_seats,
        "pooled_ai_credits": 25000,
        "admin_email": req.primary_admin_email,
        "features": [
            "Multi-Seat Recruiter Invites",
            "Pooled AI SDR Tokens",
            "Shared Gulf Candidate Talent Pool",
            "Live Deliverability Shield & DNS Monitor",
            "Dedicated Account Support"
        ],
        "message": f"Agency workspace '{req.agency_name}' successfully provisioned with {req.requested_seats} seats!"
    }


class AgencyBrandingRequest(BaseModel):
    agency_name: str
    logo_url: str
    custom_domain: Optional[str] = "outreach.agency.com"
    primary_color: Optional[str] = "#3b82f6"
    custom_footer_text: Optional[str] = "Powered by Agency B2B Swarm"

_agency_branding_store = {
    "agency_name": "Apex SDR Agency",
    "logo_url": "/static/images/agency-logo-default.png",
    "custom_domain": "outreach.apexagency.com",
    "primary_color": "#00f2fe",
    "custom_footer_text": "© 2026 Apex SDR Agency. All Rights Reserved."
}

@router.get("/agency-branding")
async def get_agency_branding():
    """Returns current white-label agency branding settings."""
    return {"status": "success", "branding": _agency_branding_store}

@router.post("/agency-branding")
async def update_agency_branding(req: AgencyBrandingRequest):
    """Updates white-label agency branding settings (Logo, Colors, Domain)."""
    _agency_branding_store.update({
        "agency_name": req.agency_name,
        "logo_url": req.logo_url,
        "custom_domain": req.custom_domain or "outreach.agency.com",
        "primary_color": req.primary_color or "#3b82f6",
        "custom_footer_text": req.custom_footer_text or f"© 2026 {req.agency_name}"
    })
    return {
        "status": "success",
        "message": f"White-label branding for '{req.agency_name}' saved successfully!",
        "branding": _agency_branding_store
    }


