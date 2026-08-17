from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(prefix="/dashboard", tags=["1000% Super Dashboard"])

templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)

@router.get("/1000", response_class=HTMLResponse)
async def get_1000_super_dashboard(request: Request):
    """
    Renders the 1000% Super-SaaS Apex Glassmorphism Command Center (Admin only).
    """
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/user-dashboard", status_code=303)

    return templates.TemplateResponse(request, "1000_super_dashboard.html", {
        "title": "1000% Super-SaaS Command Center | JobHunt Pro",
        "current_tenant": "GCC Enterprise (Owner)",
        "deliverability_score": 98.4,
        "active_swarms": 8,
        "dedup_cooldown": "365-Day Shield Active"
    })
