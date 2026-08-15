"""
JobHunt Pro — Multi-Domain Cold Email Reputation Sentinel Router
API endpoints for live domain health checks, DNS verification (SPF/DKIM/DMARC/MX),
and intelligent load-balanced dispatch domain rotation.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.multi_domain_sentinel import multi_domain_sentinel

router = APIRouter(prefix="/api/v2/sentinel", tags=["Domain Reputation Sentinel"])


class DomainVerifyRequest(BaseModel):
    domain: str


@router.get("/domains", response_model=List[Dict[str, Any]])
def get_managed_domains() -> List[Dict[str, Any]]:
    """Retrieve all managed cold email outreach domains and their health metrics."""
    return multi_domain_sentinel.get_all_domain_statuses()


@router.post("/verify", response_model=Dict[str, Any])
def verify_domain_dns(req: DomainVerifyRequest) -> Dict[str, Any]:
    """Perform live authoritative DNS check (SPF, DKIM, DMARC, MX) for a specific domain."""
    result = multi_domain_sentinel.verify_domain_dns(req.domain)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Domain verification failed"))
    return result


@router.post("/select-optimal", response_model=Dict[str, Any])
def select_optimal_domain() -> Dict[str, Any]:
    """Select the optimal dispatch domain based on warmup stage, reputation, and daily quotas."""
    return multi_domain_sentinel.select_optimal_dispatch_domain()
