from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from core.database import db
import secrets
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/squads/create")
async def create_squad(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login")

    async with db.pool.acquire() as conn:
        # Check if user already has a squad
        user = await conn.fetchrow(
            "SELECT squad_id FROM users WHERE user_id = $1", user_id
        )
        if user["squad_id"]:
            return RedirectResponse(url="/dashboard?error=already_in_squad")

        squad_id = "sqd_" + secrets.token_hex(6)
        referral_code = secrets.token_hex(4)

        async with conn.transaction():
            # Create Squad
            await conn.execute(
                """
                INSERT INTO job_squads (squad_id, owner_id) VALUES ($1, $2)
            """,
                squad_id,
                user_id,
            )

            # Update User
            await conn.execute(
                """
                UPDATE users SET squad_id = $1, referral_code = $2 WHERE user_id = $3
            """,
                squad_id,
                referral_code,
                user_id,
            )

    return RedirectResponse(url=f"/dashboard?squad={squad_id}&ref={referral_code}")


@router.get("/invite/{referral_code}")
async def join_squad_via_invite(request: Request, referral_code: str):
    """Viral Loop: New user clicks invite link -> Joins squad -> Upgrades all if 3/3."""
    async with db.pool.acquire() as conn:
        owner = await conn.fetchrow(
            "SELECT user_id, squad_id FROM users WHERE referral_code = $1",
            referral_code,
        )
        if not owner or not owner["squad_id"]:
            return RedirectResponse(url="/register?error=invalid_invite")

        squad = await conn.fetchrow(
            "SELECT * FROM job_squads WHERE squad_id = $1", owner["squad_id"]
        )

        if squad["is_complete"] or squad["member_count"] >= 3:
            return RedirectResponse(url="/register?error=squad_full")

        # Save invite intent in session for post-registration
        request.session["pending_squad_id"] = owner["squad_id"]

    return RedirectResponse(url="/register?invited=true")


async def process_pending_squad(conn, user_id: str, squad_id: str):
    """Called after successful registration if user was invited."""
    await conn.execute(
        "UPDATE users SET squad_id = $1 WHERE user_id = $2", squad_id, user_id
    )

    # Increment squad counter
    squad = await conn.fetchrow(
        """
        UPDATE job_squads SET member_count = member_count + 1 
        WHERE squad_id = $1 RETURNING member_count
    """,
        squad_id,
    )

    # China Viral Trick: If Squad reaches 3 members, EVERYONE gets 30 days Premium!
    if squad["member_count"] == 3:
        thirty_days = datetime.now() + timedelta(days=30)
        await conn.execute(
            """
            UPDATE users SET subscription_status = 'premium', subscription_end_date = $1 
            WHERE squad_id = $2
        """,
            thirty_days,
            squad_id,
        )

        await conn.execute(
            "UPDATE job_squads SET is_complete = TRUE WHERE squad_id = $1", squad_id
        )
        logger.info(
            f"[VIRAL LOOP] Squad {squad_id} completed! 3 users upgraded to Premium."
        )
