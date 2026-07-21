from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Scraping Swarm Web"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/scraping-swarm", response_class=HTMLResponse)
async def get_scraping_swarm_page(request: Request):
    return templates.TemplateResponse("scraping_swarm.html", {"request": request})
