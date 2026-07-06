"""
routers/campaigns.py - Campaigns Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import os
import uuid
import logging
from datetime import datetime
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["campaigns"])

def _deps():
    from web.shared import get_db, config
    from web.app_v2 import PRICING_TIERS, BOUQUET_PACKAGES, _verify_api_key
    return get_db, config, PRICING_TIERS, BOUQUET_PACKAGES, _verify_api_key

@router.post("/api/v1/campaign")
def api_create_campaign(
    api_key: str = Form(...),
    profile_cv: str = Form(...),
    company_count: int = Form(0),
    target_titles: str = Form(""),
    target_locations: str = Form(""),
    bouquet: str = Form(""),
):
    get_db, _, PRICING_TIERS, BOUQUET_PACKAGES, _ = _deps()
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE api_key = ? AND is_active = 1", (api_key,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid API key")

    user = dict(user)

    tier = None
    for t in PRICING_TIERS:
        if t["companies"] == company_count:
            tier = t
            break

    if not tier:
        conn.close()
        raise HTTPException(status_code=400, detail="Invalid company count")

    total_price = tier["price_usd"]
    if bouquet:
        for bname in bouquet.split(","):
            bname = bname.strip()
            if not bname:
                continue
            for b in BOUQUET_PACKAGES:
                if b["bouquet"] == bname:
                    total_price += b["price_usd"]
                    break

    if user["wallet_balance"] < total_price:
        conn.close()
        raise HTTPException(status_code=402, detail="Insufficient balance")

    profile_row = conn.execute(
        "INSERT INTO cv_profiles (user_id, profile_name, cv_text) VALUES (?, ?, ?) RETURNING id",
        (user["user_id"], f"API Profile {datetime.now().strftime('%Y%m%d%H%M')}", profile_cv)
    ).fetchone()
    profile_id = profile_row["id"] if profile_row else None

    campaign_id = f"camp_{uuid.uuid4().hex[:16]}"
    order_id = f"ord_{uuid.uuid4().hex[:16]}"

    conn.execute("""INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                 (order_id, user["user_id"], "campaign", tier["tier"], company_count, total_price, "wallet", "completed"))
    conn.execute("""INSERT INTO campaigns (campaign_id, user_id, order_id, profile_id, total_companies)
                    VALUES (?, ?, ?, ?, ?)""",
                 (campaign_id, user["user_id"], order_id, profile_id, company_count))

    new_balance = user["wallet_balance"] - total_price
    conn.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (new_balance, user["user_id"]))
    conn.execute("""INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
                    VALUES (?, ?, ?, ?, ?)""",
                 (user["user_id"], "spend", -total_price, new_balance, f"API Campaign: {company_count} companies"))

    conn.commit()
    conn.close()

    # Enqueue to distributed queue for piggyback worker
    from core.job_queue import enqueue_task
    try:
        enqueue_task("run_campaign", {"campaign_id": campaign_id})
    except Exception as e:
        logger.error(f"[QUEUE] Error enqueuing campaign {campaign_id}: {e}")

    return {"campaign_id": campaign_id, "status": "pending", "companies": company_count, "price": total_price}

@router.get("/api/v1/campaign/{campaign_id}")
def api_campaign_status(campaign_id: str, api_key: str = ""):
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key required")
    get_db, _, _, _, _ = _deps()
    conn = get_db()
    user = conn.execute("SELECT user_id FROM users WHERE api_key = ?", (api_key,)).fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid API key")

    campaign = conn.execute("SELECT * FROM campaigns WHERE campaign_id = ? AND user_id = ?",
                            (campaign_id, user["user_id"])).fetchone()
    if not campaign:
        conn.close()
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = dict(campaign)
    stats_row = conn.execute("""
        SELECT COUNT(*) as total,
        SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
        SUM(CASE WHEN opened_at IS NOT NULL THEN 1 ELSE 0 END) as opened,
        SUM(CASE WHEN responded_at IS NOT NULL THEN 1 ELSE 0 END) as responded
        FROM campaign_emails WHERE campaign_id = ?
    """, (campaign_id,)).fetchone()
    stats = dict(stats_row) if stats_row else {"total": 0, "sent": 0, "opened": 0, "responded": 0}

    conn.close()
    return {**campaign, **stats}

@router.get("/api/v1/campaigns")
def api_campaigns(api_key: str = "", limit: int = 10):
    """List recent campaigns."""
    get_db, _, _, _, _verify_api_key = _deps()
    user = _verify_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")
    conn = get_db()
    rows = conn.execute("SELECT campaign_id, status, sent_count, created_at FROM campaigns WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                         (user["user_id"], limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]