"""JobHunt Pro — Unsubscribe & Tracking Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging
import os

from fastapi import APIRouter, Request, HTTPException
from starlette.responses import Response

from backend.auth import _IS_TESTING
from backend.database import async_session


def _get_signing_secret() -> str:
    """Return the secret used to sign unsubscribe/tracking tokens — IMP-SEC-UNSUB.

    Fails closed: if JWT_SECRET_KEY is not configured and we are not in an
    explicit test run, raise so we never fall back to a hardcoded secret.
    """
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        if not _IS_TESTING:
            raise RuntimeError("JWT_SECRET_KEY is not configured; cannot sign/verify tokens.")
        return "jobhunt-pro-secret-key-32bytes-ok!!"
    return secret

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Unsubscribe & Tracking"])


# ---------------------------------------------------------------------------
# IMP-225: Unsubscribe Token Endpoint
# ---------------------------------------------------------------------------

@router.get("/api/v1/unsubscribe/{token}")
async def unsubscribe(token: str, request: Request = None) -> dict:
    """Validate signed unsubscribe token and mark user as unsubscribed — IMP-225."""
    try:
        from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
        _secret = _get_signing_secret()
        s = URLSafeTimedSerializer(_secret)
        try:
            email = s.loads(token, max_age=7 * 24 * 3600)  # 7 days
        except SignatureExpired:
            raise HTTPException(status_code=410, detail="Unsubscribe link has expired")
        except BadSignature:
            raise HTTPException(status_code=400, detail="Invalid unsubscribe token")

        # Mark unsubscribed in DB
        try:
            from sqlalchemy import text as _text
            async with async_session() as session:
                await session.execute(
                    _text("UPDATE users SET unsubscribed = 1 WHERE email = :email"),
                    {"email": email}
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to update unsubscribe in DB: {e}")

        logger.info(f"[Unsubscribe] {email} unsubscribed successfully")
        return {"status": "unsubscribed", "email": email}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unsubscribe failed: {e}")


# ---------------------------------------------------------------------------
# IMP-226: Hardened Signed Tracking Pixel Endpoint
# ---------------------------------------------------------------------------

@router.get("/api/v1/track/{email_log_id}")
async def track_email(
    email_log_id: str,
    email: str,
    expiry: int,
    sig: str,
    request: Request = None
) -> Response:
    """Validate signed tracking pixel and record open event — IMP-226."""
    import hashlib
    import hmac
    import time

    # Check expiry
    if time.time() > expiry:
        raise HTTPException(status_code=403, detail="Tracking link expired")

    secret = _get_signing_secret().encode("utf-8")
    message = f"{email_log_id}:{email}:{expiry}".encode()
    expected_sig = hmac.new(secret, message, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected_sig, sig):
        raise HTTPException(status_code=403, detail="Invalid signature")

    # Record open event in DB
    try:
        from sqlalchemy import text as _text
        async with async_session() as session:
            await session.execute(
                _text("UPDATE applications SET opened = 1, opened_at = CURRENT_TIMESTAMP WHERE tracking_id = :tid"),
                {"tid": email_log_id}
            )
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to record open event for {email_log_id}: {e}")

    # Return 1x1 transparent GIF
    pixel = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    return Response(content=pixel, media_type="image/gif")
