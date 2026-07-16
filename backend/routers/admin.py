"""JobHunt Pro — Admin Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import bindparam, text

from backend.auth import verify_jwt, require_admin
from backend.database import async_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])


@router.post("/api/v1/admin/dlq/requeue", dependencies=[Depends(require_admin)])
async def dlq_requeue(request: Request = None) -> dict:
    """Requeue stale SyncOutbox records that failed to sync — IMP-207."""
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    requeued_count = 0
    try:
        body: dict = {}
        if request:
            try:
                body = await request.json()
            except Exception:  # noqa: BLE001
                pass
        queue_name = body.get("queue_name") or body.get("queue")
        task_ids = body.get("task_ids") or body.get("ids")
        async with async_session() as session:
            params: dict = {"now": datetime.now(UTC).isoformat()}
            if task_ids or queue_name:
                query_str = "UPDATE ps_crud_outbox SET synced = 0, created_at = :now WHERE 1=1"
                if task_ids:
                    query_str += " AND id IN :task_ids"
                    params["task_ids"] = list(task_ids)
                if queue_name:
                    query_str += " AND table_name = :queue_name"
                    params["queue_name"] = str(queue_name)
            else:
                query_str = "UPDATE ps_crud_outbox SET synced = 0, created_at = :now WHERE synced = 0 AND created_at < :cutoff"
                params["cutoff"] = cutoff.isoformat()
            stmt = text(query_str)
            if "task_ids" in params:
                stmt = stmt.bindparams(bindparam("task_ids", expanding=True))
            result = await session.execute(stmt, params)
            await session.commit()
            requeued_count = result.rowcount or 0
            logger.info("[DLQ] Requeued %s stale SyncOutbox records.", requeued_count)
    except Exception as e:  # noqa: BLE001
        logger.error("[DLQ] Requeue failed: %s", e)
        raise HTTPException(status_code=500, detail=f"DLQ requeue failed: {e}") from e
    return {"requeued": requeued_count, "cutoff_utc": cutoff.isoformat()}
