from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["Interview Copilot Web"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/interview-copilot", response_class=HTMLResponse)
async def get_copilot_page(request: Request):
    return templates.TemplateResponse("interview_copilot.html", {"request": request})
