"""
web/routers/market_radar.py - Gulf Labor Market Intelligence & Radar Router
JobHunt Pro SaaS - Real-time market trends, in-demand skills, and hiring velocity.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from core.market_intel import GulfMarketIntelligence

logger = logging.getLogger("market_radar_router")
router = APIRouter(tags=["Market Intel Radar"])


def _deps():
    from web.app_v2 import _public_shell, render_template
    from web.shared import get_db, get_verified_user_id, templates
    return get_db, get_verified_user_id, templates, _public_shell, render_template


@router.get("/market-intel", response_class=HTMLResponse)
@router.get("/en/market-intel", response_class=HTMLResponse)
def get_market_intel_page(request: Request):
    """Render interactive GCC Market Intelligence Radar."""
    _, get_verified_user_id_fn, _, _public_shell_fn, render_template_fn = _deps()
    user_id = get_verified_user_id_fn(request)
    
    is_en = request.url.path.startswith("/en") or request.query_params.get("lang") == "en"
    tpl = "en/market_intel.html" if is_en else "market_intel.html"
    title = "Gulf Labor Market Intelligence Radar — JobHunt Pro" if is_en else "رادار استخبارات سوق العمل الخليجي — JobHunt Pro"
    
    content = render_template_fn(tpl, request=request, active_page="market_intel", user_id=user_id)
    return HTMLResponse(_public_shell_fn(content, title, active_page="market_intel"))


@router.get("/api/market-intel/trends")
async def get_market_trends():
    """Returns GCC labor market trends summary."""
    return JSONResponse(GulfMarketIntelligence.get_market_trends_summary())


@router.get("/api/market-intel/city/{city_name}")
async def get_city_market_data(city_name: str):
    """Returns detailed hiring velocity and top skills for a specific city."""
    return JSONResponse(GulfMarketIntelligence.get_city_details(city_name))
