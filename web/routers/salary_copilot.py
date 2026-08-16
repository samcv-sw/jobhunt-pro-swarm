"""
web/routers/salary_copilot.py - AI Salary Counter-Offer & Negotiation Copilot Router
JobHunt Pro SaaS - Gulf compensation benchmarks and AI counter-offer pitch generation.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from core.closed_loop_negotiator import closed_loop_negotiator

logger = logging.getLogger("salary_copilot_router")
router = APIRouter(tags=["Salary Copilot"])


def _deps():
    from web.app_v2 import _public_shell, render_template
    from web.shared import get_db, get_verified_user_id, templates
    return get_db, get_verified_user_id, templates, _public_shell, render_template


@router.get("/salary-negotiator", response_class=HTMLResponse)
@router.get("/en/salary-negotiator", response_class=HTMLResponse)
def get_salary_negotiator_page(request: Request):
    """Render interactive Gulf Salary Negotiation Copilot page."""
    _, get_verified_user_id_fn, _, _public_shell_fn, render_template_fn = _deps()
    user_id = get_verified_user_id_fn(request)
    
    is_en = request.url.path.startswith("/en") or request.query_params.get("lang") == "en"
    tpl = "en/salary_negotiator.html" if is_en else "salary_negotiator.html"
    title = "AI Salary Negotiation Copilot — JobHunt Pro" if is_en else "مساعد التفاوض على الرواتب بالذكاء الاصطناعي — JobHunt Pro"
    
    content = render_template_fn(tpl, request=request, active_page="salary_negotiator", user_id=user_id)
    return HTMLResponse(_public_shell_fn(content, title, active_page="salary_negotiator"))


@router.post("/api/salary-negotiator/counter-offer")
async def generate_counter_offer_api(request: Request):
    """Calculates compensation percentiles and generates customized counter-offer copy."""
    try:
        data = await request.json()
        job_title = data.get("job_title", "Senior Cloud Architect")
        city = data.get("city", "Riyadh")
        offered_monthly = float(data.get("offered_monthly", 25000.0))
        currency = data.get("currency", "SAR")
        experience_years = int(data.get("experience_years", 7))
        benefits = data.get("benefits", "Standard health insurance")

        result = closed_loop_negotiator.generate_counter_offer(
            job_title=job_title,
            city=city,
            offered_monthly=offered_monthly,
            currency=currency,
            experience_years=experience_years,
            current_benefits=benefits
        )
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error generating counter offer: {e}")
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@router.get("/api/salary-negotiator/benchmarks")
async def get_benchmarks_api(city: str = "Riyadh"):
    """Returns GCC market benchmarks across popular tech and leadership roles."""
    roles = [
        {"title": "Senior Cloud / DevOps Architect", "p50_sar": 29000, "p75_sar": 36000, "p90_sar": 45000},
        {"title": "Lead Full-Stack / Backend Engineer", "p50_sar": 26000, "p75_sar": 33000, "p90_sar": 40000},
        {"title": "Cybersecurity & SOC Director", "p50_sar": 38000, "p75_sar": 48000, "p90_sar": 58000},
        {"title": "Engineering Manager / VP Tech", "p50_sar": 45000, "p75_sar": 58000, "p90_sar": 72000}
    ]
    return JSONResponse({"success": True, "city": city, "benchmarks": roles})
