"""
Enterprise B2B Suite Router (Omni-Suite 2026)
Handles multi-tenant B2B organization workspaces, RBAC role management, candidate pool sharing, and enterprise recruiting analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel, EmailStr
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
    email: EmailStr
    role: str # Owner, Admin, Recruiter, Member
    status: str # Active, Pending

class InviteMemberRequest(BaseModel):
    email: EmailStr
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
