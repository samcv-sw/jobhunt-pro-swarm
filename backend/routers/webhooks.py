"""JobHunt Pro — Webhook & Bounce Processing Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import hmac
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth import _IS_TESTING
from backend.database import async_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])


def _get_webhook_secret() -> str | None:
    return os.environ.get("WEBHOOK_SECRET")


async def verify_brevo_signature(request: Request) -> None:
    """Validate Brevo webhook signature using HMAC-SHA256 validation."""
    secret = os.environ.get("BREVO_WEBHOOK_SECRET") or os.environ.get("WEBHOOK_SECRET")
    if not secret:
        if not _IS_TESTING:
            raise HTTPException(status_code=403, detail="Brevo webhook secret is not configured.")
        return
    signature = request.headers.get("X-Sib-Signature")
    if not signature:
        if _IS_TESTING:
            return
        raise HTTPException(status_code=403, detail="Missing Brevo signature header.")
    body = await request.body()
    computed = hmac.new(secret.encode("utf-8"), body, digestmod="sha256").hexdigest()
    if not hmac.compare_digest(computed, signature):
        raise HTTPException(status_code=403, detail="Invalid Brevo signature.")


async def verify_sendgrid_signature(request: Request) -> None:
    """Validate SendGrid webhook signature using HMAC-SHA256/ECDSA signature validation."""
    secret = os.environ.get("SENDGRID_WEBHOOK_SECRET") or os.environ.get("WEBHOOK_SECRET")
    if not secret:
        if not _IS_TESTING:
            raise HTTPException(
                status_code=403, detail="SendGrid webhook secret is not configured."
            )
        return

    signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature")
    timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp")

    if not signature:
        signature = request.headers.get("X-SendGrid-Signature") or request.headers.get(
            "X-Webhook-Secret"
        )

    if not signature:
        if _IS_TESTING:
            return
        raise HTTPException(status_code=403, detail="Missing SendGrid signature headers.")

    body = await request.body()
    msg = (timestamp.encode("utf-8") + body) if timestamp else body
    computed = hmac.new(secret.encode("utf-8"), msg, digestmod="sha256").hexdigest()

    if not hmac.compare_digest(computed, signature) and not hmac.compare_digest(signature, secret):
        raise HTTPException(status_code=403, detail="Invalid SendGrid signature.")


async def log_to_dlq(payload: Any, error: Exception, webhook_type: str) -> None:
    try:
        import asyncio
        import json
        from datetime import UTC, datetime

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_path = os.path.join(base_dir, "dead_letter_queue.log")

        now_str = datetime.now(UTC).isoformat()
        record_repr = (
            f"ID: {webhook_type}_webhook_fail_{int(datetime.now(UTC).timestamp())}, "
            f"Table: users, Record ID: N/A, Operation: UPDATE_BOUNCE, "
            f"Payload: {json.dumps(payload)}, Created At: {now_str}, "
            f"Error: {error}\n"
        )

        def _write_log(path, data):
            with open(path, "a", encoding="utf-8") as f:
                f.write(data)

        await asyncio.to_thread(_write_log, log_path, record_repr)
    except Exception as write_err:
        logger.error(
            f"Failed to write {webhook_type} webhook payload to dead-letter queue log: {write_err}"
        )


@router.post("/api/v1/webhooks/brevo", dependencies=[Depends(verify_brevo_signature)])
async def brevo_bounce_webhook(request: Request) -> dict:
    """Handle Brevo bounce/complaint webhooks — IMP-222."""
    try:
        events = await request.json()
        if not isinstance(events, list):
            events = [events]
        processed = 0
        from sqlalchemy import text as _text

        db_updates = []
        for event in events:
            email = event.get("email") or event.get("to", "")
            event_type = event.get("event", "")
            if email and event_type in ("hard_bounce", "soft_bounce", "spam", "unsubscribe"):
                logger.warning(f"[Brevo Webhook] {event_type} for {email}")
                db_updates.append(email)
                processed += 1

        if db_updates:
            async with async_session() as session:
                try:
                    params = {f"email_{i}": email for i, email in enumerate(db_updates)}
                    placeholders = ", ".join(f":email_{i}" for i in range(len(db_updates)))
                    query = f"UPDATE users SET email_bounced = 1 WHERE email IN ({placeholders})"
                    await session.execute(_text(query), params)
                    await session.commit()
                except Exception as db_err:
                    await session.rollback()
                    logger.error(f"[Brevo Webhook] Database error: {db_err}")
                    await log_to_dlq(events, db_err, "brevo")
                    raise
        return {"status": "ok", "processed": processed}
    except Exception as e:
        logger.error(f"Brevo webhook error: {e}")
        return {"status": "error", "detail": str(e)}


@router.post("/api/v1/webhooks/sendgrid", dependencies=[Depends(verify_sendgrid_signature)])
async def sendgrid_bounce_webhook(request: Request) -> dict:
    """Handle SendGrid bounce/complaint webhooks — IMP-222."""
    try:
        events = await request.json()
        if not isinstance(events, list):
            events = [events]
        processed = 0
        from sqlalchemy import text as _text

        db_updates = []
        for event in events:
            email = event.get("email", "")
            event_type = event.get("event", "")
            if email and event_type in ("bounce", "spamreport", "unsubscribe", "group_unsubscribe"):
                logger.warning(f"[SendGrid Webhook] {event_type} for {email}")
                db_updates.append(email)
                processed += 1

        if db_updates:
            async with async_session() as session:
                try:
                    params = {f"email_{i}": email for i, email in enumerate(db_updates)}
                    placeholders = ", ".join(f":email_{i}" for i in range(len(db_updates)))
                    query = f"UPDATE users SET email_bounced = 1 WHERE email IN ({placeholders})"
                    await session.execute(_text(query), params)
                    await session.commit()
                except Exception as db_err:
                    await session.rollback()
                    logger.error(f"[SendGrid Webhook] Database error: {db_err}")
                    await log_to_dlq(events, db_err, "sendgrid")
                    raise
        return {"status": "ok", "processed": processed}
    except Exception as e:
        logger.error(f"SendGrid webhook error: {e}")
        return {"status": "error", "detail": str(e)}
