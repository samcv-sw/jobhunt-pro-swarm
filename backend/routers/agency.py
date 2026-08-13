"""
White-Label Agency Portal & Multi-Tenant Management Router for JobHunt Pro.
"""

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any

router = APIRouter(prefix="/api/v1/agency", tags=["Agency Portal"])

_agency_db = {}

@router.post("/configure-portal")
async def setup_agency_portal(payload: Dict[str, Any] = Body(...)):
    """Configures white-label agency branding and custom domain settings."""
    agency_id = payload.get("agency_id")
    if not agency_id:
        raise HTTPException(status_code=400, detail="Agency ID is required.")

    profile = {
        "agency_id": agency_id,
        "company_name": payload.get("company_name", "Growth Agency Pro"),
        "custom_domain": payload.get("custom_domain", "leads.growthagency.com"),
        "custom_logo_url": payload.get("custom_logo_url", "/static/agency_logo.png"),
        "primary_color": payload.get("primary_color", "#00f2fe"),
        "seats_allowed": payload.get("seats_allowed", 10),
        "active_clients": payload.get("active_clients", 3)
    }
    _agency_db[agency_id] = profile
    return {"status": "success", "profile": profile}

@router.get("/portal/{agency_id}")
async def get_agency_portal(agency_id: str):
    """Retrieves white-label agency portal profile."""
    if agency_id in _agency_db:
        return {"status": "success", "profile": _agency_db[agency_id]}
    
    # Fallback default agency profile
    return {
        "status": "success",
        "profile": {
            "agency_id": agency_id,
            "company_name": "Apex Enterprise Leads",
            "custom_domain": f"{agency_id}.jobhuntpro.io",
            "custom_logo_url": "/static/default_logo.png",
            "primary_color": "#00f2fe",
            "seats_allowed": 25,
            "active_clients": 8
        }
    }
