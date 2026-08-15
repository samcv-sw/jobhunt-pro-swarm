"""
backend/routers/growth_master_suite.py - Master Growth & 24/7 Cloud Autonomy API Suite
Exposes REST endpoints for Anti-Spam Scanner, Email Pattern Finder, Vector Matching, and Swarm Orchestration.
"""

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Body

from services.company_email_pattern_engine import company_email_pattern_engine
from services.email_spam_scanner_service import email_spam_scanner_service
from services.master_growth_swarm_orchestrator import master_growth_swarm_orchestrator
from services.edge_vector_matcher_v3 import edge_vector_matcher_v3

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/growth-master", tags=["Growth Master Suite"])


@router.post("/scan-spam")
async def scan_email_spam(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Scan subject and body copy for spam trigger words and calculate inbox placement score.
    """
    subject = payload.get("subject", "")
    body = payload.get("body", "")
    if not subject and not body:
        raise HTTPException(status_code=400, detail="Subject or body is required for spam scan")
    
    return email_spam_scanner_service.scan_content(subject, body)


@router.post("/discover-email-pattern")
async def discover_email_pattern(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Discover candidate email patterns for decision makers at a specific company domain.
    """
    first_name = payload.get("first_name", "Hiring")
    last_name = payload.get("last_name", "Manager")
    domain = payload.get("domain", "")

    if not domain:
        raise HTTPException(status_code=400, detail="Company domain is required")

    return company_email_pattern_engine.generate_candidate_emails(
        first_name=first_name,
        last_name=last_name,
        company_domain=domain,
        verify_mx=payload.get("verify_mx", True)
    )


@router.post("/match-resume-vector")
async def match_resume_vector(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Perform sub-5ms vector matching of resume skills against target job embeddings.
    """
    skills = payload.get("skills", ["python", "ai", "fastapi"])
    top_k = payload.get("top_k", 5)
    return edge_vector_matcher_v3.match_resume_vector(resume_keywords=skills, top_k=top_k)


@router.post("/run-swarm-pipeline")
async def run_swarm_pipeline(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Run end-to-end autonomous swarm pipeline on lead data.
    """
    lead_data = payload.get("lead", {})
    if not lead_data:
        raise HTTPException(status_code=400, detail="Lead data is required")
    
    candidate = payload.get("candidate")
    dispatch_alert = payload.get("dispatch_alert", False)

    return master_growth_swarm_orchestrator.process_lead_end_to_end(
        lead_data=lead_data,
        candidate_profile=candidate,
        dispatch_alerts=dispatch_alert
    )
