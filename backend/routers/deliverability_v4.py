"""
Deliverability V4 Router
Provides endpoints for psychographic spintax generation, Gaussian jitter calculation,
and domain DNS deliverability health audits.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from core.psychographic_jitter_engine import psychographic_jitter_engine

router = APIRouter(prefix="/api/deliverability-v4", tags=["Deliverability V4"])

class SpintaxRequest(BaseModel):
    tone: str = Field("executive", example="executive")
    name: str = Field("Ahmed", example="Ahmed")
    company: str = Field("Careem", example="Careem")
    sender_name: str = Field("Sami", example="Sami")

class DomainAuditRequest(BaseModel):
    domain: str = Field(..., example="jobhuntpro.io")

class UnsubscribeHeaderRequest(BaseModel):
    unsubscribe_url: str = Field(..., example="https://jobhuntpro.io/api/unsubscribe/token_123")
    mailto_address: str = Field(..., example="unsub@jobhuntpro.io")

@router.post("/generate-spintax")
def generate_spintax(req: SpintaxRequest) -> Dict[str, Any]:
    """Generate psychographic non-repeating outreach email."""
    return psychographic_jitter_engine.generate_personalized_copy(
        tone=req.tone,
        name=req.name,
        company=req.company,
        sender_name=req.sender_name
    )

@router.get("/calculate-jitter")
def get_gaussian_jitter(base_sec: float = Query(120.0), std_dev: float = Query(30.0)) -> Dict[str, Any]:
    """Calculate human-like Gaussian jitter send delay."""
    return psychographic_jitter_engine.calculate_gaussian_jitter(base_delay_sec=base_sec, std_dev=std_dev)

@router.post("/audit-domain")
def audit_domain(req: DomainAuditRequest) -> Dict[str, Any]:
    """Execute live DNS MX, SPF, DKIM, and Blacklist audit."""
    return psychographic_jitter_engine.audit_domain_deliverability(req.domain)

@router.post("/rfc8058-headers")
def get_rfc8058_headers(req: UnsubscribeHeaderRequest) -> Dict[str, str]:
    """Generate RFC 8058 one-click unsubscribe headers."""
    return psychographic_jitter_engine.inject_rfc_8058_headers(
        unsubscribe_url=req.unsubscribe_url,
        mailto_address=req.mailto_address
    )
