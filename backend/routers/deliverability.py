"""
Deliverability & Domain Health Router for JobHunt Pro.
"""

from fastapi import APIRouter, Query, HTTPException
from core.domain_health import check_domain_dns

router = APIRouter(prefix="/api/v1/deliverability", tags=["Deliverability"])

@router.get("/check-domain")
async def audit_domain(domain: str = Query(..., description="Domain name to audit (e.g. company.com)")):
    """Audit DNS records and deliverability status for a domain."""
    if not domain:
        raise HTTPException(status_code=400, detail="Domain parameter is required.")
    return check_domain_dns(domain)

@router.get("/health")
async def deliverability_health():
    """Returns general deliverability shield status."""
    return {
        "status": "active",
        "mx_verification_shield": True,
        "cooldown_deduplication_window_days": 365,
        "synthetic_email_prevention": True
    }
