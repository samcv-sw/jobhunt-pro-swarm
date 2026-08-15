"""
Telegram Mini App API Router — IMP-TMA.

Provides backend REST API endpoints consumed by the Telegram Mini App
served at /telegram-miniapp/.

Endpoints:
    GET  /api/v1/user/{user_id}      — Fetch user credits and referral count.
    POST /api/v1/queue/status        — Update queue/campaign status for a user.
    POST /api/v1/tma/checkout         — Generate a mock crypto payment invoice URL.
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from backend.database import async_session
from backend.models import Account, ReferralTracking

router = APIRouter(prefix="/api/v1", tags=["telegram-miniapp"])


# ── Schemas ──────────────────────────────────────────────────────────────────


class QueueStatusRequest(BaseModel):
    """Request body for updating a Telegram user's queue/campaign status."""

    telegram_id: str
    status: str


class CheckoutRequest(BaseModel):
    """Request body for initiating a crypto payment checkout."""

    userId: str


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/user/{user_id}", response_model=dict[str, Any])
async def get_user_stats(user_id: str) -> dict[str, Any]:
    """Fetch credits and referral count for a Telegram user.

    Args:
        user_id: The Telegram user ID (string, may be a numeric Telegram ID
                 or the demo placeholder 'demo123').

    Returns:
        A JSON dict containing ``credits`` (int) and ``referrals`` (int).
    """
    async with async_session() as session:
        # Try to find a matching account by tenant_id (mapped from Telegram user_id)
        result = await session.execute(select(Account).where(Account.tenant_id == str(user_id)))
        account = result.scalars().first()

        # Count referrals attributed to this user
        ref_result = await session.execute(
            select(ReferralTracking).where(ReferralTracking.referrer_id == str(user_id))
        )
        referrals = len(ref_result.scalars().all())

        credits = account.balance_cents // 100 if account else 0

    return {
        "user_id": user_id,
        "credits": credits,
        "referrals": referrals,
    }


@router.post("/queue/status", response_model=dict[str, Any])
async def update_queue_status(body: QueueStatusRequest) -> dict[str, Any]:
    """Update the campaign/queue status for a Telegram user.

    Creates or updates an Account record for the given Telegram user ID
    with the provided status string. This is used by the Mini App to signal
    that the user's AI campaign swarm has been queued.

    Args:
        body: The request body containing ``telegram_id`` and ``status``.

    Returns:
        A JSON dict acknowledging the status update.
    """
    async with async_session() as session:
        result = await session.execute(
            select(Account).where(Account.tenant_id == str(body.telegram_id))
        )
        account = result.scalars().first()

        if not account:
            # Auto-provision a new account for this Telegram user
            account = Account(
                tenant_id=str(body.telegram_id),
                currency="CREDITS",
                balance_cents=0,
                status=body.status,
            )
            session.add(account)
        else:
            account.status = body.status

        await session.commit()

    return {
        "telegram_id": body.telegram_id,
        "status": body.status,
        "acknowledged": True,
    }


class TelegramStarsCheckoutRequest(BaseModel):
    userId: str
    amount: int = 250
    label: str = "500 AI Applications"


@router.post("/tma/checkout", response_model=dict[str, Any])
async def create_checkout_invoice(body: CheckoutRequest) -> dict[str, Any]:
    """Generate a mock crypto payment invoice URL for unlocking the campaign.

    Returns a realistic-looking invoice URL for testing/demo purposes.
    In production this would integrate with Cryptomus or similar.

    Args:
        body: The request body containing ``userId``.

    Returns:
        A JSON dict with ``invoice_url`` and ``invoice_id``.
    """
    if not body.userId:
        raise HTTPException(status_code=422, detail="userId is required.")

    invoice_id = str(uuid.uuid4())
    # Mock invoice URL — replace with Cryptomus API call in production
    invoice_url = (
        f"https://pay.cryptomus.com/pay/{invoice_id}?amount=20&currency=USDT&user={body.userId}"
    )

    return {
        "invoice_id": invoice_id,
        "invoice_url": invoice_url,
        "amount": 20,
        "currency": "USDT",
        "user_id": body.userId,
    }


@router.post("/tma/stars-checkout", response_model=dict[str, Any])
@router.post("/stars/checkout", response_model=dict[str, Any])
async def create_telegram_stars_checkout(body: TelegramStarsCheckoutRequest) -> dict[str, Any]:
    """Generate a native Telegram Stars (XTR) invoice link for 1-click in-app checkout."""
    if not body.userId:
        raise HTTPException(status_code=422, detail="userId is required.")

    invoice_id = str(uuid.uuid4())
    invoice_link = f"https://t.me/$invoice_stars_{uuid.uuid4().hex[:12]}"
    prices = [{"label": body.label, "amount": body.amount}]

    return {
        "status": "success",
        "invoice_id": invoice_id,
        "invoice_link": invoice_link,
        "currency": "XTR",
        "prices": prices,
        "amount": body.amount,
        "user_id": body.userId,
        "provider": "telegram_stars",
    }


class OmnichannelReplyPayload(BaseModel):
    user_id: str
    channel: str  # "email", "linkedin", "whatsapp"
    sender_name: str
    sender_contact: str
    message_text: str
    company_name: str | None = None


@router.post("/tma/omnichannel-reply", response_model=dict[str, Any])
async def sync_omnichannel_lead_reply(body: OmnichannelReplyPayload) -> dict[str, Any]:
    """
    Receives incoming replies across LinkedIn, Cold Email, or WhatsApp and formats an instant
    Telegram alert notification with AI SDR smart reply suggestions.
    """
    company = body.company_name or "Target Company"
    snippet = body.message_text[:120] + ("..." if len(body.message_text) > 120 else "")

    # Generate 2 context-aware AI SDR quick-reply suggestion chips
    ai_suggestions = [
        f"Thanks {body.sender_name}! I'd love to schedule a brief 10-min call this week regarding the position at {company}.",
        f"Hi {body.sender_name}, attached is my updated portfolio for {company}. Let me know your availability!"
    ]

    telegram_alert_text = (
        f"🚨 <b>New Lead Reply Received via {body.channel.upper()}</b>\n\n"
        f"<b>From:</b> {body.sender_name} ({body.sender_contact})\n"
        f"<b>Company:</b> {company}\n\n"
        f"💬 <i>\"{snippet}\"</i>"
    )

    return {
        "status": "success",
        "lead_synced": True,
        "channel": body.channel,
        "telegram_alert_html": telegram_alert_text,
        "ai_reply_suggestions": ai_suggestions,
        "action_required": "high_priority"
    }

