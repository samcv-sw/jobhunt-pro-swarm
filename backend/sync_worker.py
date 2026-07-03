"""
Sync Worker — Outbox Pattern
Streams local SQLite mutations to remote Neon PostgreSQL asynchronously.
Handles connection failures gracefully; never crashes the process.
"""
import asyncio
import logging
import os
import json
import asyncpg
from .database import async_session, REMOTE_PG_URL
from .models import SyncOutbox
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def _push_record_to_cloud(conn: asyncpg.Connection, record: SyncOutbox) -> bool:
    """
    Pushes a single outbox record to the remote Neon PostgreSQL database.
    Returns True on success, False on failure.
    """
    try:
        payload_json = json.dumps(record.payload) if record.payload else "{}"
        await conn.execute(
            """
            INSERT INTO sync_outbox_log (table_name, record_id, operation, payload, created_at)
            VALUES ($1, $2, $3, $4::jsonb, $5)
            ON CONFLICT DO NOTHING
            """,
            record.table_name,
            record.record_id,
            record.operation,
            payload_json,
            record.created_at,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to push record {record.id} to cloud: {e}")
        return False


async def sync_outbox_to_cloud():
    """
    Background worker that continuously streams local SQLite changes
    to the Neon PostgreSQL database via the outbox pattern.
    Handles connection failures gracefully without crashing.
    """
    logger.info("[SyncWorker] Started. Monitoring outbox for unsynced records...")

    while True:
        cloud_conn = None
        try:
            # Strip async+asyncpg scheme for raw asyncpg connection
            raw_pg_url = REMOTE_PG_URL.replace("postgresql+asyncpg://", "postgresql://")

            if not raw_pg_url or "localhost" in raw_pg_url:
                logger.debug("[SyncWorker] No remote PG configured. Skipping sync cycle.")
                await asyncio.sleep(30)
                continue

            # Attempt to open a remote connection each cycle (tolerates cold starts)
            cloud_conn = await asyncpg.connect(raw_pg_url)

            async with async_session() as session:
                result = await session.execute(
                    select(SyncOutbox)
                    .where(SyncOutbox.synced == False)
                    .limit(100)
                )
                unsynced_records = result.scalars().all()

                if not unsynced_records:
                    logger.debug("[SyncWorker] No unsynced records. Sleeping...")
                else:
                    synced_count = 0
                    for record in unsynced_records:
                        success = await _push_record_to_cloud(cloud_conn, record)
                        if success:
                            record.synced = True
                            synced_count += 1

                    await session.commit()
                    logger.info(
                        f"[SyncWorker] Cycle complete — {synced_count}/{len(unsynced_records)} records pushed to cloud."
                    )

        except asyncpg.PostgresConnectionError as e:
            logger.warning(f"[SyncWorker] Remote DB unreachable (will retry in 30s): {e}")
        except Exception as e:
            logger.error(f"[SyncWorker] Unexpected error: {e}")
        finally:
            if cloud_conn and not cloud_conn.is_closed():
                await cloud_conn.close()

        # Poll every 30 seconds (generous interval to avoid hammering remote DB)
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(sync_outbox_to_cloud())
