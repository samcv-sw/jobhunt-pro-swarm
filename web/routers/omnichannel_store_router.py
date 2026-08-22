"""
web/routers/omnichannel_store_router.py - Universal Multi-Platform Store & Webhook Router
========================================================================================
- Handles automated order dispatch and dispute rebuttals across:
  • Taobao / Tmall
  • AliExpress
  • Alibaba.com / 1688
  • Pinduoduo
  • FaKa Storefronts
  • Xianyu
"""

import json
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from core.omnichannel_ecommerce_matrix import dispatch_omnichannel_order, SUPPORTED_PLATFORMS
from core.universal_dispute_engine import build_platform_specific_rebuttal

logger = logging.getLogger(__name__)
router = APIRouter(tags=["omnichannel_ecommerce"])


@router.post("/api/v2/omnichannel/dispatch")
async def api_omnichannel_dispatch(request: Request):
    """
    Universal automated dispatch endpoint for Taobao, AliExpress, Alibaba, Pinduoduo, FaKa.
    """
    try:
        data = await request.json()
        platform = data.get("platform", "taobao")
        tier = data.get("tier", "pro")
        buyer_id = data.get("buyer_id", "guest_buyer")
        order_id = data.get("order_id", f"omni_{int(time.time())}")
        lang = data.get("language", "zh")
        qty = int(data.get("quantity", 1))
    except Exception:
        platform, tier, buyer_id, order_id, lang, qty = "taobao", "pro", "guest_buyer", "omni_default", "zh", 1

    result = dispatch_omnichannel_order(
        platform=platform,
        tier=tier,
        buyer_id=buyer_id,
        order_id=order_id,
        language=lang,
        quantity=qty
    )
    return JSONResponse(result, status_code=200 if result.get("status") == "success" else 400)


@router.post("/api/v2/omnichannel/dispute-rebuttal")
async def api_omnichannel_dispute(request: Request):
    """
    Generates targeted legal defense matching the exact rules of the platform (AliExpress, 1688, Taobao, PDD).
    """
    try:
        data = await request.json()
        platform = data.get("platform", "aliexpress")
        order_id = data.get("order_id", "order_12345")
        buyer_id = data.get("buyer_id", "buyer_789")
        amount = float(data.get("amount", 49.0))
        currency = data.get("currency", "USD")
    except Exception:
        platform, order_id, buyer_id, amount, currency = "aliexpress", "order_12345", "buyer_789", 49.0, "USD"

    result = build_platform_specific_rebuttal(
        platform=platform,
        order_id=order_id,
        buyer_id=buyer_id,
        amount=amount,
        currency=currency
    )
    return JSONResponse(result, status_code=200)


@router.get("/api/v2/omnichannel/platforms")
async def api_omnichannel_platforms(request: Request):
    """Returns all supported international and domestic marketplace channels."""
    return JSONResponse({
        "status": "active",
        "total_platforms": len(SUPPORTED_PLATFORMS),
        "platforms": SUPPORTED_PLATFORMS
    }, status_code=200)
