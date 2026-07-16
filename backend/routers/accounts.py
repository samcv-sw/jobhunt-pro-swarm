"""JobHunt Pro — Account Management Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging
from fastapi import APIRouter, Depends

from backend.auth import verify_jwt
from backend.database import async_session
from backend.limiter import rate_limiter
from backend.schemas import AccountCreateRequest
from backend.models import Account, SyncOutbox

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
            tenant_id=req.tenant_id,
            currency=req.currency,
            balance_cents=req.balance_cents
        )
        session.add(account)
        await session.flush()

        outbox = SyncOutbox(
            table_name="accounts",
            record_id=str(account.id),
            operation="INSERT",
            payload={
                "id": account.id,
                "tenant_id": account.tenant_id,
                "currency": account.currency,
                "balance_cents": account.balance_cents
            },
            synced=False
        )
        session.add(outbox)
        await session.commit()

        logger.info(f"Account #{account.id} created and outbox synchronized.")
        return {"status": "created", "account_id": str(account.id)}
