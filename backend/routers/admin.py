"""JobHunt Pro — Admin Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import bindparam, text

from backend.auth import require_admin
from backend.database import async_session

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])


@router.post("/api/v1/admin/dlq/requeue", dependencies=[Depends(require_admin)])
async def dlq_requeue(request: Request = None) -> dict:
    """Requeue stale SyncOutbox records that failed to sync — IMP-207."""
    cutoff = datetime.now(UTC) - timedelta(hours=24)
    requeued_count = 0
    import asyncio

    try:
        body: dict = {}
        import contextlib

        if request:
            with contextlib.suppress(Exception):
                body = await request.json()
        queue_name = body.get("queue_name") or body.get("queue")
        task_ids = body.get("task_ids") or body.get("ids")
        async with async_session() as session:
            select_params: dict = {}
            if task_ids or queue_name:
                select_query = "SELECT id FROM ps_crud_outbox WHERE 1=1"
                if task_ids:
                    select_query += " AND id IN :task_ids"
                    select_params["task_ids"] = list(task_ids)
                if queue_name:
                    select_query += " AND table_name = :queue_name"
                    select_params["queue_name"] = str(queue_name)
            else:
                select_query = (
                    "SELECT id FROM ps_crud_outbox WHERE synced = 0 AND created_at < :cutoff"
                )
                select_params["cutoff"] = cutoff.isoformat()

            stmt = text(select_query)
            if "task_ids" in select_params:
                stmt = stmt.bindparams(bindparam("task_ids", expanding=True))

            result = await session.execute(stmt, select_params)
            all_ids = [row[0] for row in result.fetchall()]

            for i in range(0, len(all_ids), 100):
                batch_ids = all_ids[i : i + 100]
                update_query = (
                    "UPDATE ps_crud_outbox SET synced = 0, created_at = :now WHERE id IN :batch_ids"
                )
                update_params = {"now": datetime.now(UTC).isoformat(), "batch_ids": batch_ids}
                update_stmt = text(update_query).bindparams(bindparam("batch_ids", expanding=True))
                batch_result = await session.execute(update_stmt, update_params)
                await session.commit()
                requeued_count += batch_result.rowcount or 0
                await asyncio.sleep(0.01)

            logger.info("[DLQ] Requeued %s stale SyncOutbox records.", requeued_count)
    except Exception as e:  # noqa: BLE001
        logger.error("[DLQ] Requeue failed: %s", e)
        raise HTTPException(status_code=500, detail=f"DLQ requeue failed: {e}") from e
    return {"requeued": requeued_count, "cutoff_utc": cutoff.isoformat()}
