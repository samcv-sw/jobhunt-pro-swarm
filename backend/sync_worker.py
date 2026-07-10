"""
Sync Worker — Outbox Pattern
Streams local SQLite mutations to remote Neon PostgreSQL asynchronously.
Handles connection failures gracefully; never crashes the process.
"""
import asyncio
import json
import logging
import os
import random
import sys
import time

import asyncpg

if not hasattr(asyncpg, "Error"):
    asyncpg.Error = asyncpg.PostgresError
from sqlalchemy import select

from .database import REMOTE_PG_URL, async_session
from .models import SyncOutbox

logger = logging.getLogger(__name__)

CONNECTION_EXCEPTIONS = (
    asyncpg.PostgresConnectionError,
    asyncpg.InterfaceError,
    OSError,
    asyncio.TimeoutError,
)

async def _push_record_to_cloud(conn: asyncpg.Connection, record: SyncOutbox) -> bool:
    """
    Pushes a single outbox record to the remote Neon PostgreSQL database.
    Returns True on success, False on failure.
    """
    try:
        payload_json = json.dumps(record.payload) if record.payload else "{}"
        start_time = time.perf_counter()
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
        latency = time.perf_counter() - start_time
        logger.info(f"[SyncTelemetry] Push record {record.id} to Neon PG latency: {latency:.6f}s")
        return True
    except CONNECTION_EXCEPTIONS as e:
        logger.error(f"Connection exception during push of record {record.id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to push record {record.id} to cloud (soft error/data failure): {e}", exc_info=True)
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dead_letter_queue.log")
            record_repr = (
                f"ID: {record.id}, Table: {record.table_name}, Record ID: {record.record_id}, "
                f"Operation: {record.operation}, Payload: {record.payload}, Created At: {record.created_at}, "
                f"Error: {e}\n"
            )
            def _write_log(path, data):
                with open(path, "a", encoding="utf-8") as f:
                    f.write(data)
            await asyncio.to_thread(_write_log, log_path, record_repr)
        except Exception as write_err:
            logger.error(f"Failed to write record {record.id} to dead-letter queue log: {write_err}")
        return False


async def sync_outbox_to_cloud():
    """
    Background worker that continuously streams local SQLite changes
    to the Neon PostgreSQL database via the outbox pattern.
    Handles connection failures gracefully without crashing.
    """
    logger.info("[SyncWorker] Started. Monitoring outbox for unsynced records...")

    cloud_conn = None
    while True:
        try:
            # Strip async+asyncpg scheme for raw asyncpg connection
            raw_pg_url = REMOTE_PG_URL.replace("postgresql+asyncpg://", "postgresql://")

            if not raw_pg_url or "localhost" in raw_pg_url:
                logger.debug("[SyncWorker] No remote PG configured. Skipping sync cycle.")
                await asyncio.sleep(30)
                continue

            # Reuse connection if active, otherwise reconnect
            if not cloud_conn or cloud_conn.is_closed():
                logger.info("[SyncWorker] Re-establishing remote DB connection...")
                cloud_conn = await asyncpg.connect(raw_pg_url)

            async with async_session() as session:
                result = await session.execute(
                    select(SyncOutbox)
                    .where(SyncOutbox.synced.is_(False))
                    .limit(100)
                )
                unsynced_records = result.scalars().all()

                if not unsynced_records:
                    logger.debug("[SyncWorker] No unsynced records. Sleeping...")
                else:
                    synced_count = 0
                    connection_error = None
                    for record in unsynced_records:
                        try:
                            success = await _push_record_to_cloud(cloud_conn, record)
                            if success:
                                record.synced = True
                                synced_count += 1
                            else:
                                record.synced = True
                                logger.warning(f"[SyncWorker] Record {record.id} routed to dead-letter queue (DLQ) due to soft error.")
                        except CONNECTION_EXCEPTIONS as e:
                            logger.error(f"[SyncWorker] Connection lost during record push. Aborting batch: {e}")
                            connection_error = e
                            break

                    await session.commit()
                    if connection_error:
                        raise connection_error

                    logger.info(
                        f"[SyncWorker] Cycle complete — {synced_count}/{len(unsynced_records)} records pushed to cloud."
                    )

        except (asyncpg.Error, asyncpg.InterfaceError, OSError, asyncio.TimeoutError) as e:
            logger.warning(f"[SyncWorker] Remote DB connection lost/unreachable (will retry in 30s): {e}")
            if cloud_conn:
                try:
                    await cloud_conn.close()
                except Exception:
                    pass
                cloud_conn = None
        except Exception as e:
            logger.error(f"[SyncWorker] Unexpected error: {e}")
        
        # Poll every 30 seconds
        await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(sync_outbox_to_cloud())
