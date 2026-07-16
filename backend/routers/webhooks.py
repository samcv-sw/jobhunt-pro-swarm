"""JobHunt Pro — Webhook & Bounce Processing Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging
import hmac
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.auth import _IS_TESTING
from backend.database import async_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])


def _get_webhook_secret() -> str | None:
    return os.environ.get("WEBHOOK_SECRET")


async def require_webhook_secret(request: Request) -> None:
    """Validate inbound webhook using a shared secret header — IMP-SEC-WH.

    Brevo/SendGrid webhooks are unauthenticated by default; we require a
    pre-shared secret via the ``X-Webhook-Secret`` header. Fails closed: if no
    secret is configured server-side, all webhook calls are rejected unless
    running in an explicit test environment.
    """
    expected = _get_webhook_secret()
    if not expected:
        if not _IS_TESTING:
            raise HTTPException(status_code=403, detail="Webhook authentication is not configured.")
        return
    provided = request.headers.get("X-Webhook-Secret") or request.headers.get("authorization") or ""
    if provided.lower().startswith("bearer "):
        provided = provided[7:]
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Invalid webhook secret.")


async def log_to_dlq(payload: Any, error: Exception, webhook_type: str) -> None:
    try:
        import json
        import asyncio
        from datetime import datetime, UTC
        
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
        logger.error(f"Failed to write {webhook_type} webhook payload to dead-letter queue log: {write_err}")


@router.post("/api/v1/webhooks/brevo", dependencies=[Depends(require_webhook_secret)])
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


@router.post("/api/v1/webhooks/sendgrid", dependencies=[Depends(require_webhook_secret)])
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
