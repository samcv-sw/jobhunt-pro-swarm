"""
web/routers/sovereign_growth_api.py - Sovereign Growth, Review Rebates & PnL Analytics API Router
================================================================================================
- REST endpoints for Xianyu 5-star review loyalty rewards.
- Recruiter reply sentiment analysis and meeting scheduling assistant.
- Real-time zero-cost P&L financial ledger API.
- Steganographic CV watermark verification endpoint.
"""

import json
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from core.xianyu_review_incentive_engine import claim_5star_review_bonus
from core.outreach_sentiment_scheduler import analyze_recruiter_sentiment
from core.realtime_pnl_matrix import calculate_realtime_pnl_summary
from core.cv_watermark_attribution import verify_cv_watermark

logger = logging.getLogger(__name__)
router = APIRouter(tags=["sovereign_growth_apis"])


@router.post("/api/v2/xianyu/claim-review-reward")
async def api_claim_xianyu_review(request: Request):
    """
    Claims loyalty bonus credits for leaving a 5-star review on Xianyu/Taobao.
    """
    try:
        data = await request.json()
        user_id = data.get("user_id", "admin")
        nick = data.get("buyer_nick", "buyer")
        oid = data.get("order_id", "xy_order_default")
        review = data.get("review_text", "5星好评！")
    except Exception:
        user_id, nick, oid, review = "admin", "buyer", "xy_order_default", "5星好评！"

    res = claim_5star_review_bonus(user_id, nick, oid, review)
    return JSONResponse(res, status_code=200 if res.get("status") == "success" else 400)


@router.post("/api/v2/outreach/analyze-reply")
async def api_outreach_analyze_reply(request: Request):
    """
    Analyzes recruiter email response and suggests executive reply & calendar slots.
    """
    try:
        data = await request.json()
        reply_body = data.get("reply_body", "")
        sender = data.get("sender_email", "")
        job_title = data.get("job_title", "Senior Engineer")
    except Exception:
        reply_body, sender, job_title = "", "", "Senior Engineer"

    res = analyze_recruiter_sentiment(reply_body, sender, job_title)
    return JSONResponse(res, status_code=200)


@router.get("/api/v2/analytics/pnl-summary")
async def api_analytics_pnl_summary(request: Request):
    """
    Returns real-time financial ledger & P&L summary across all gateways.
    """
    res = calculate_realtime_pnl_summary()
    return JSONResponse(res, status_code=200)


@router.post("/api/v2/cv/verify-watermark")
async def api_verify_cv_watermark(request: Request):
    """
    Verifies invisible steganographic watermark in a JobHunt Pro generated CV.
    """
    try:
        data = await request.json()
        cv_text = data.get("cv_text", "")
    except Exception:
        cv_text = ""

    res = verify_cv_watermark(cv_text)
    return JSONResponse(res, status_code=200)
