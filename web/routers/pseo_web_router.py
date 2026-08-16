"""
web/routers/pseo_web_router.py - Programmatic SEO (pSEO) Web Router for Google Search Ranking
JobHunt Pro SaaS - Renders high-intent job landing pages with Schema.org JobPosting structured data.
"""

import logging
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from core.pseo_job_farm import pseo_job_farm, TOP_GCC_LOCATIONS, TOP_JOB_CATEGORIES

logger = logging.getLogger("pseo_web_router")
router = APIRouter(tags=["pSEO Web Pages"])


def _deps():
    from web.app_v2 import _public_shell, render_template
    from web.shared import get_db, get_verified_user_id, templates
    return get_db, get_verified_user_id, templates, _public_shell, render_template


@router.get("/jobs/{role_slug}-in-{city_slug}", response_class=HTMLResponse)
@router.get("/en/jobs/{role_slug}-in-{city_slug}", response_class=HTMLResponse)
@router.get("/jobs/{role_slug}/{city_slug}", response_class=HTMLResponse)
@router.get("/en/jobs/{role_slug}/{city_slug}", response_class=HTMLResponse)
def get_pseo_job_page(role_slug: str, city_slug: str, request: Request):
    """Renders hyper-localized programmatic SEO job page with Schema.org JSON-LD."""
    _, get_verified_user_id_fn, _, _public_shell_fn, render_template_fn = _deps()
    user_id = get_verified_user_id_fn(request)
    
    is_en = request.url.path.startswith("/en") or request.query_params.get("lang") == "en"
    tpl = "en/pseo_job_page.html" if is_en else "pseo_job_page.html"
    
    page_data = pseo_job_farm.generate_seo_page_payload(role_slug=role_slug, city_slug=city_slug)
    title = page_data["meta_title"] if is_en else page_data["meta_title_ar"]
    
    content = render_template_fn(
        tpl,
        request=request,
        page_data=page_data,
        role_slug=role_slug,
        city_slug=city_slug,
        user_id=user_id
    )
    return HTMLResponse(_public_shell_fn(content, title, active_page="jobs"))


@router.get("/jobs/catalog", response_class=HTMLResponse)
@router.get("/en/jobs/catalog", response_class=HTMLResponse)
def get_pseo_catalog_page(request: Request):
    """Renders directory of all indexed Gulf job roles and cities."""
    _, get_verified_user_id_fn, _, _public_shell_fn, render_template_fn = _deps()
    user_id = get_verified_user_id_fn(request)
    
    is_en = request.url.path.startswith("/en") or request.query_params.get("lang") == "en"
    tpl = "en/pseo_catalog.html" if is_en else "pseo_catalog.html"
    title = "Gulf Tech Careers Directory — JobHunt Pro" if is_en else "دليل الشواغر والوظائف التقنية في الخليج — JobHunt Pro"
    
    content = render_template_fn(
        tpl,
        request=request,
        locations=TOP_GCC_LOCATIONS,
        roles=TOP_JOB_CATEGORIES,
        user_id=user_id
    )
    return HTMLResponse(_public_shell_fn(content, title, active_page="jobs"))


@router.get("/sitemap-jobs.xml")
def get_jobs_xml_sitemap():
    """Returns valid XML sitemap of all programmatic job landing pages."""
    xml_content = pseo_job_farm.generate_dynamic_xml_sitemap()
    return Response(content=xml_content, media_type="application/xml")


@router.post("/api/pseo/submit-indexnow")
async def submit_pseo_indexnow_endpoint():
    """Fast-tracks all pSEO URLs directly into IndexNow protocol for instant search engine indexing."""
    from core.indexnow_protocol import IndexNowEngine
    urls = pseo_job_farm.get_programmatic_sitemap_urls()
    res = await IndexNowEngine.submit_urls(urls=urls, host="jobhuntpro.io")
    return JSONResponse(res)

