"""
Stealth Harvester Matrix Router
Provides REST endpoints to generate Google Dorks, execute Boolean searches, and extract hiring signals.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from core.stealth_dorks_matrix_v2 import stealth_dorks_matrix

router = APIRouter(prefix="/api/stealth-harvester", tags=["Stealth Harvester Matrix"])

class DorkRequest(BaseModel):
    role: str = Field(..., example="Senior Full Stack Engineer")
    location: Optional[str] = Field("dubai", example="dubai")
    platform: Optional[str] = Field(None, example="greenhouse.io")

class BooleanRequest(BaseModel):
    role: str = Field(..., example="Chief Technology Officer")
    department: str = Field("Engineering", example="Engineering")
    location: str = Field("Dubai", example="Dubai")

class SignalParseRequest(BaseModel):
    raw_snippet: str = Field(..., example="Urgently looking for Senior Backend Lead in Riyadh. Salary 35,000 SAR - 45,000 SAR.")

@router.get("/status")
def get_harvester_status() -> Dict[str, Any]:
    """Get operational status and supported GCC & Global hubs."""
    return {
        "status": "active",
        "engine": "Stealth Dorks Matrix V2",
        "supported_hubs": list(stealth_dorks_matrix.TARGET_HUBS.keys()),
        "supported_ats": stealth_dorks_matrix.ATS_PLATFORMS,
        "mode": "Zero-Cost Autonomous Harvester"
    }

@router.post("/generate-dork")
def generate_ats_dork(req: DorkRequest) -> Dict[str, Any]:
    """Generate targeted ATS direct link dork query."""
    return stealth_dorks_matrix.build_ats_dork(
        role=req.role,
        location=req.location,
        platform=req.platform
    )

@router.post("/generate-boolean")
def generate_boolean_search(req: BooleanRequest) -> Dict[str, Any]:
    """Generate hiring manager boolean search query."""
    return stealth_dorks_matrix.build_hiring_manager_boolean(
        role=req.role,
        department=req.department,
        location=req.location
    )

@router.get("/matrix")
def get_full_matrix(role: str = Query("Software Engineer"), hub: str = Query("dubai")) -> Dict[str, Any]:
    """Generate full 6-vector search matrix."""
    matrix = stealth_dorks_matrix.build_stealth_matrix(role=role, hub=hub)
    return {
        "role": role,
        "hub": hub,
        "total_vectors": len(matrix),
        "matrix": matrix
    }

@router.post("/parse-signal")
def parse_snippet_signal(req: SignalParseRequest) -> Dict[str, Any]:
    """Extract urgency, remote status, and salary indications."""
    return stealth_dorks_matrix.parse_job_signal(req.raw_snippet)
