"""
web/routers/reseller_portal_router.py - Sovereign Reseller, Affiliate & Dropshipping Matrix Router
=================================================================================================
- Provides the public Sovereign Reseller & Distributor Hub (/reseller, /distributor).
- High-speed REST APIs for Xianyu/Taobao auto-vending bots, Telegram mini-apps, and global SaaS affiliates.
- Auto-delivery webhooks and 1-click marketing kit downloads.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

from web.shared import templates, get_verified_user_id
from core.sovereign_reseller_engine import (
    register_or_get_reseller,
    mint_reseller_code,
    get_reseller_marketing_kit,
    generate_telegram_reseller_bot_code,
    RESELLER_TIERS,
    RETAIL_PRICES
)

from core.aegis_shield import get_client_ip, _blackhole, PROBE_BLACKHOLE_DURATION

logger = logging.getLogger(__name__)

router = APIRouter(tags=["reseller_growth_matrix"])

# In-Memory Fail2Ban & Anti-Sybil Security State
_failed_ip_attempts: Dict[str, List[float]] = {}
_ip_registrations: Dict[str, List[float]] = {}


def _record_failed_probe_and_quarantine(ip: str) -> None:
    """Tracks failed key attempts and automatically blackholes abusive IPs."""
    now = time.time()
    history = _failed_ip_attempts.setdefault(ip, [])
    # Keep only last 5 minutes
    history = [t for t in history if now - t < 300]
    history.append(now)
    _failed_ip_attempts[ip] = history

    if len(history) >= 5 and ip not in ("127.0.0.1", "localhost", "testserver", "unknown"):
        _blackhole[ip] = now + PROBE_BLACKHOLE_DURATION
        logger.warning(f"[SECURITY FORTRESS] IP {ip} blackholed for 24h due to 5+ failed API probes.")


class ResellerRegisterRequest(BaseModel):
    email: Optional[str] = Field(default=None, max_length=150)
    name: Optional[str] = Field(default=None, max_length=100)
    tier: Optional[str] = Field(default="starter_reseller", pattern=r"^(starter_reseller|gold_distributor|sovereign_partner)$")
    initial_balance: Optional[float] = Field(default=0.0, ge=0.0, le=100000.0)
    website_url_hp: Optional[str] = Field(default=None, description="Honeypot trap for malicious crawlers")


class ResellerMintRequest(BaseModel):
    reseller_key: str = Field(..., max_length=100, pattern=r"^[a-zA-Z0-9_\-]{10,100}$", description="Secret Reseller API Key")
    tier: Optional[str] = Field(default="basic", pattern=r"^(starter|basic|pro|b2b|enterprise)$")
    platform: Optional[str] = Field(default="xianyu", max_length=32, pattern=r"^[a-zA-Z0-9_\-]{1,32}$")
    buyer_id: Optional[str] = Field(default="guest_buyer", max_length=100, pattern=r"^[a-zA-Z0-9_\-\.@:]{1,100}$")
    order_reference: Optional[str] = Field(default="", max_length=100, pattern=r"^[a-zA-Z0-9_\-\.:]{0,100}$")
    partner_token_hp: Optional[str] = Field(default=None, description="Honeypot trap for malicious crawlers")


class ResellerBulkMintRequest(BaseModel):
    reseller_key: str = Field(..., max_length=100, pattern=r"^[a-zA-Z0-9_\-]{10,100}$")
    tier: Optional[str] = Field(default="basic", pattern=r"^(starter|basic|pro|b2b|enterprise)$")
    quantity: int = Field(default=5, ge=1, le=50)
    platform: Optional[str] = Field(default="xianyu", max_length=32, pattern=r"^[a-zA-Z0-9_\-]{1,32}$")


# ==============================================================================
# 🌐 1. Public UI Hub Routes (/reseller, /distributor, /affiliate-hub)
# ==============================================================================

@router.get("/reseller", response_class=HTMLResponse)
@router.get("/distributor", response_class=HTMLResponse)
@router.get("/affiliate-hub", response_class=HTMLResponse)
async def reseller_hub_page(
    request: Request,
    lang: str = Query("ar", description="Language code: ar, zh, en, ru"),
    ref: Optional[str] = Query(None)
):
    """
    Renders the Sovereign Reseller & Wholesale Distributor Portal.
    """
    user_id = get_verified_user_id(request)
    marketing_pack = get_reseller_marketing_kit(referral_code=ref or "PARTNER_PRO")

    context = {
        "request": request,
        "lang": lang.lower(),
        "user_id": user_id,
        "ref": ref or "PARTNER_PRO",
        "tiers": RESELLER_TIERS,
        "retail_prices": RETAIL_PRICES,
        "marketing_pack": marketing_pack,
    }
    return templates.TemplateResponse("reseller_hub.html", context)


# ==============================================================================
# 🚀 2. High-Speed Reseller API Endpoints (Fortress Protected)
# ==============================================================================

@router.post("/api/v2/reseller/register")
async def api_register_reseller(req: ResellerRegisterRequest, request: Request):
    """
    1-Click instant on-boarding with Anti-Sybil Rate Limiting & Bot Honeypot Traps.
    """
    client_ip = get_client_ip(request)
    now = time.time()

    # 1. Honeypot check for bots
    if req.website_url_hp:
        _record_failed_probe_and_quarantine(client_ip)
        return JSONResponse({"status": "error", "message": "Access Denied"}, status_code=403)

    # 2. Anti-Sybil Rate Limiter (Max 5 registrations per 15 mins per IP)
    reg_history = _ip_registrations.setdefault(client_ip, [])
    reg_history = [t for t in reg_history if now - t < 900]
    if len(reg_history) >= 5 and client_ip not in ("127.0.0.1", "localhost", "testserver"):
        return JSONResponse(
            {"status": "error", "error_code": "REGISTRATION_LIMIT", "message": "Registration rate limit reached. Please wait 15 minutes."},
            status_code=429
        )
    reg_history.append(now)
    _ip_registrations[client_ip] = reg_history

    res = register_or_get_reseller(
        email=req.email,
        name=req.name,
        preferred_tier=req.tier or "starter_reseller",
        initial_balance=req.initial_balance or 0.0
    )
    return JSONResponse(res, status_code=200)


@router.post("/api/v2/reseller/mint-code")
async def api_reseller_mint_code(req: ResellerMintRequest, request: Request):
    """
    High-performance (<0.02s) code generation API protected by Fail2Ban & Replay Interception.
    """
    client_ip = get_client_ip(request)

    # Honeypot Check
    if req.partner_token_hp:
        _record_failed_probe_and_quarantine(client_ip)
        return JSONResponse({"status": "error", "message": "Access Denied"}, status_code=403)

    res = mint_reseller_code(
        reseller_key=req.reseller_key,
        tier=req.tier or "basic",
        platform=req.platform or "xianyu",
        buyer_id=req.buyer_id or "guest_buyer",
        order_reference=req.order_reference or ""
    )

    if res.get("status") != "success":
        _record_failed_probe_and_quarantine(client_ip)
        return JSONResponse(res, status_code=400)

    return JSONResponse(res, status_code=200)


@router.post("/api/v2/reseller/bulk-mint")
async def api_reseller_bulk_mint(req: ResellerBulkMintRequest, request: Request):
    """
    Bulk batch minting for resellers preparing inventory batches for Xianyu/Taobao CSV vaults.
    """
    client_ip = get_client_ip(request)
    results = []
    total_wholesale = 0.0
    total_retail = 0.0

    for i in range(req.quantity):
        order_ref = f"bulk_{int(time.time())}_{i+1}"
        item = mint_reseller_code(
            reseller_key=req.reseller_key,
            tier=req.tier,
            platform=req.platform,
            buyer_id=f"batch_buyer_{i+1}",
            order_reference=order_ref
        )
        if item.get("status") == "success":
            results.append(item)
            total_wholesale += item.get("wholesale_cost_usd", 0.0)
            total_retail += item.get("retail_value_usd", 0.0)
        else:
            _record_failed_probe_and_quarantine(client_ip)
            if not results:
                return JSONResponse(item, status_code=400)
            break

    return JSONResponse({
        "status": "success",
        "batch_count": len(results),
        "total_retail_value_usd": round(total_retail, 2),
        "total_wholesale_cost_usd": round(total_wholesale, 2),
        "total_estimated_profit_usd": round(total_retail - total_wholesale, 2),
        "codes": results
    }, status_code=200)


@router.get("/api/v2/reseller/marketing-kit")
async def api_reseller_marketing_kit(
    reseller_key: str = Query("", description="Reseller API key"),
    referral_code: str = Query("PARTNER_PRO", description="Referral code")
):
    """
    Returns full multi-lingual marketing assets, high-CTR listing titles, and dispute shields.
    """
    kit = get_reseller_marketing_kit(reseller_key=reseller_key, referral_code=referral_code)
    return JSONResponse(kit, status_code=200)


@router.get("/api/v2/reseller/bot-script")
async def api_reseller_bot_script(
    reseller_key: str = Query("rk_live_demo_reseller_key", description="Reseller API key"),
    lang: str = Query("zh", description="Language code: zh, ar, en")
):
    """
    Returns copy-paste ready standalone Telegram Reseller Bot Python script in requested language.
    """
    code = generate_telegram_reseller_bot_code(reseller_key=reseller_key, lang=lang)
    return PlainTextResponse(code, media_type="text/plain")


@router.get("/api/v2/reseller/tiers")
async def api_reseller_tiers():
    """
    Returns the wholesale discounts and profit margins per tier.
    """
    return JSONResponse({
        "status": "success",
        "retail_prices": RETAIL_PRICES,
        "reseller_tiers": RESELLER_TIERS
    }, status_code=200)
