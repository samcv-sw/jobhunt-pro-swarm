"""
JobHunt Pro — Programmatic SEO (pSEO) Job Farm Router
API endpoints providing dynamic localized job landing page content, Schema.org JobPosting structured data,
and automated Google XML sitemaps.
"""

from fastapi import APIRouter, HTTPException, Query, Response
from typing import Dict, Any, List, Optional

from core.pseo_job_farm import pseo_job_farm, TOP_GCC_LOCATIONS, TOP_JOB_CATEGORIES

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


@router.get("/sitemap.xml")
def get_dynamic_xml_sitemap():
    """Generates real-time valid XML sitemap for Google Search Console and Bing Webmaster."""
    xml_content = pseo_job_farm.generate_dynamic_xml_sitemap()
    return Response(content=xml_content, media_type="application/xml")


@router.get("/catalog")
def get_pseo_catalog() -> Dict[str, Any]:
    """Returns supported locations, roles, and total indexed URLs count."""
    return {
        "locations": TOP_GCC_LOCATIONS,
        "roles": TOP_JOB_CATEGORIES,
        "total_generated_urls": len(pseo_job_farm.get_programmatic_sitemap_urls()),
        "status": "INDEXING_OPTIMIZED"
    }
