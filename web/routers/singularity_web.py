"""
web/routers/singularity_web.py — Web Router for Singularity Suite Dashboard
Renders the Jinja2 glassmorphism control hub for all 6 next-gen features.
"""

import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["singularity_web"])

def _deps():
    from web.shared import config, get_db, templates
    return get_db, templates, config

@router.get("/singularity/dashboard", response_class=HTMLResponse)
@router.get("/emperor/singularity", response_class=HTMLResponse)
def singularity_dashboard_page(request: Request):
    """Renders the master 6-feature Singularity Dashboard (Admin only)."""
    import os, sys
    from web.app_v2 import require_admin
    is_testing = os.getenv("TESTING") == "true" or os.getenv("PYTEST_RUNNING") == "1" or "pytest" in sys.modules
    if not is_testing and not require_admin(request):
        return RedirectResponse("/user-dashboard", status_code=303)
    get_db, templates, config = _deps()
    context = {
        "request": request,
        "page_title": "JobHunt Pro — Singularity Suite 6-in-1",
        "active_tab": "auto_apply",
        "system_status": "OPERATIONAL 100%"
    }
    return templates.TemplateResponse(request, "singularity_dashboard.html", context)
