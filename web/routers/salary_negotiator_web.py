from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from services.salary_analytics_service import salary_analytics_service, SalaryEstimateRequest

router = APIRouter(tags=["Salary Negotiator Web"])
templates = Jinja2Templates(directory="web/templates")

@router.get("/salary-negotiator", response_class=HTMLResponse)
async def get_salary_negotiator_page(request: Request):
    return templates.TemplateResponse(request, "salary_negotiator.html", {"title": "Salary Negotiator & Market Analytics | JobHunt Pro"})

@router.post("/api/salary/estimate")
async def estimate_salary(req: SalaryEstimateRequest):
    """Estimate real-time salary benchmarks and skill gap value."""
    result = salary_analytics_service.estimate_compensation(req)
    return result

@router.get("/api/salary/negotiation-script")
async def get_negotiation_script(role: str = "Senior Engineer", offer: float = 85000.0, target: float = 105000.0):
    """Generate custom counter-offer negotiation scripts."""
    script = salary_analytics_service.generate_negotiation_script(role, offer, target)
    return script
