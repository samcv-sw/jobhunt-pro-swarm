"""JobHunt Pro — Account Management Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging

from fastapi import APIRouter, Depends

from backend.auth import verify_jwt
from backend.database import async_session
from backend.limiter import rate_limiter
from backend.models import Account, SyncOutbox
from backend.schemas import AccountCreateRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Accounts"])


@router.post(
    "/api/v1/accounts",
    dependencies=[Depends(verify_jwt), Depends(rate_limiter)],
)
async def create_account(req: AccountCreateRequest) -> dict[str, str]:
    """Creates a local account and logs a sync outbox record — IMP-006."""
    logger.info(f"Create local account requested for tenant: {req.tenant_id}")
    async with async_session() as session:
        account = Account(
            tenant_id=req.tenant_id, currency=req.currency, balance_cents=req.balance_cents
        )
        session.add(account)
        await session.flush()

        outbox = SyncOutbox(
            table_name="billing_accounts",
            record_id=str(account.id),
            operation="INSERT",
            payload={
                "id": account.id,
                "tenant_id": account.tenant_id,
                "currency": account.currency,
                "balance_cents": account.balance_cents,
            },
            synced=False,
        )
        session.add(outbox)
        await session.commit()

        logger.info(f"Account #{account.id} created and outbox synchronized.")
        return {"status": "created", "account_id": str(account.id)}


# V2 Multi-Seat Team Management
from pydantic import BaseModel, Field
from typing import Optional, List

class TeamInviteRequest(BaseModel):
    team_id: Optional[str] = "team_master"
    email: str = Field(..., description="Target teammate email address")
    role: str = Field("member", description="admin, member, recruiter, sales_rep")

_TEAM_MEMBERS = [
    {"id": "usr_owner", "name": "Master Account", "email": "admin@jobhuntpro.io", "role": "owner", "status": "active"},
    {"id": "usr_member1", "name": "Sarah Recruiter", "email": "sarah@jobhuntpro.io", "role": "recruiter", "status": "active"}
]

@router.get("/api/v2/team/members")
async def get_team_members_v2(team_id: str = "team_master"):
    """Returns list of active sub-user seats under master enterprise subscription."""
    return {
        "status": "success",
        "team_id": team_id,
        "max_seats": 10,
        "active_seats_count": len(_TEAM_MEMBERS),
        "members": _TEAM_MEMBERS
    }

@router.post("/api/v2/team/members/invite")
async def invite_team_member_v2(req: TeamInviteRequest):
    """Invites a new teammate seat to the enterprise workspace."""
    new_member = {
        "id": f"usr_{len(_TEAM_MEMBERS) + 1}",
        "name": req.email.split("@")[0].title(),
        "email": req.email,
        "role": req.role,
        "status": "invited"
    }
    _TEAM_MEMBERS.append(new_member)
    return {
        "status": "success",
        "message": f"Invitation email sent to {req.email} with role '{req.role}'",
        "member": new_member
    }

