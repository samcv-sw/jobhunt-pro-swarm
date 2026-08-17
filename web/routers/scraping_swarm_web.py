from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Scraping Swarm Web"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/scraping-swarm", response_class=HTMLResponse)
async def get_scraping_swarm_page(request: Request):
    from web.app_v2 import require_admin
    if not require_admin(request):
        return RedirectResponse("/user-dashboard", status_code=303)
    return templates.TemplateResponse(request, "scraping_swarm.html", {})
