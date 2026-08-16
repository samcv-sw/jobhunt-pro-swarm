"""
JobHunt Pro SaaS — Programmatic SEO Router.
Exposes endpoints for dynamic landing page generation, sitemap URL discovery,
and schema.org rich snippets for search engine crawlers.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query, Path
from core.programmatic_seo import pseo_engine

router = APIRouter(prefix="/api/v2/pseo", tags=["Programmatic SEO Engine"])


@router.get("/landing-data/{role_slug}")
def get_landing_page_data(
    role_slug: str = Path(..., example="software-engineer"),
    location: str = Query("riyadh", example="riyadh"),
    language: str = Query("en", example="en")
) -> Dict[str, Any]:
    """
    Returns complete programmatic landing page payload with Schema.org JSON-LD and localized ATS keywords.
    """
    return pseo_engine.generate_landing_data(
        role_slug=role_slug,
        location_slug=location,
        language=language
    )


@router.get("/sitemap-urls")
def get_all_sitemap_slugs() -> Dict[str, Any]:
    """
    Returns all dynamically generated landing page slugs for automated XML sitemap generation.
    """
    slugs = pseo_engine.list_all_p_seo_slugs()
    return {
        "status": "success",
        "total_urls": len(slugs),
        "urls": [f"https://jobhuntpro.io/ats-scanner/{s}" for s in slugs]
    }
