"""JobHunt Pro — Referral Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text as _text

from backend.auth import verify_jwt
from backend.database import async_session
from backend.schemas import ReferralRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Referral"])


@router.post("/api/v1/referral/track", dependencies=[Depends(verify_jwt)])
async def track_referral(req: ReferralRequest, payload: dict = Depends(verify_jwt)) -> dict:
    """Store referral code for the authenticated user — IMP-189."""
    user_id = payload.get("sub", "")
    try:
        async with async_session() as session:
            await session.execute(
                _text("UPDATE users SET referred_by = :ref WHERE user_id = :uid"),
                {"ref": req.ref_code, "uid": user_id},
            )
            await session.commit()
    except Exception as e:  # noqa: BLE001
        logger.warning("Referral tracking DB update failed (column may not exist yet): %s", e)
    return {"status": "tracked", "ref_code": req.ref_code, "user_id": user_id}
