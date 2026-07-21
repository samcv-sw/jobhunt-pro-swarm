from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["ATS Resume Sculptor Web"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/ats-resume-sculptor", response_class=HTMLResponse)
async def get_ats_sculptor_page(request: Request):
    return templates.TemplateResponse("ats_resume_sculptor.html", {"request": request})
