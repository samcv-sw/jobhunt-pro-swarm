"""
JobHunt Pro — Programmatic SEO (pSEO) Job Farm Router
API endpoints providing dynamic localized job landing page content and Schema.org JobPosting structured data.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional

from core.pseo_job_farm import pseo_job_farm

router = APIRouter(prefix="/api/v2/pseo", tags=["Programmatic SEO Job Farm"])


@router.get("/page", response_model=Dict[str, Any])
def get_pseo_job_page(
    role: str = Query("software-engineer", description="Role slug, e.g. software-engineer"),
    city: str = Query("riyadh", description="City slug, e.g. riyadh, dubai, doha")
) -> Dict[str, Any]:
    """Retrieve SEO metadata, headings, market insights, and Schema.org JobPosting JSON-LD markup."""
    return pseo_job_farm.generate_seo_page_payload(role_slug=role, city_slug=city)


@router.get("/sitemap-routes", response_model=List[str])
def get_pseo_sitemap_urls() -> List[str]:
    """Generate the full list of programmatic SEO routes for Google indexing."""
    return pseo_job_farm.get_programmatic_sitemap_urls()
