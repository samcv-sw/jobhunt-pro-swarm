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

# Connection-related exceptions to catch and trigger backoff/retry
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
    Raises connection exceptions to trigger backoff in the main loop.
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
    except CONNECTION_EXCEPTIONS as e:
        logger.warning(f"[SyncWorker] Connection lost while pushing record {record.id}: {e}")
        raise
    except Exception as e:
        logger.error(f"[SyncWorker] Failed to push record {record.id} to cloud: {e}")
        return False


async def sync_outbox_to_cloud():
    """
    Background worker that continuously streams local SQLite changes
    to the Neon PostgreSQL database via the outbox pattern.
    Handles connection failures gracefully with exponential backoff.
    """
    logger.info("[SyncWorker] Started. Monitoring outbox for unsynced records...")

    # Backoff configurations
    base_poll_interval = 30.0   # Normal polling interval when healthy
    initial_backoff = 5.0       # First retry wait time on failure
    max_backoff = 300.0         # Upper limit of backoff time (5 minutes)
    backoff_factor = 2.0        # Exponential multiplier
    
    current_backoff = initial_backoff
    consecutive_failures = 0

    while True:
        cloud_conn = None
        sleep_time = base_poll_interval
        try:
            # Strip async+asyncpg scheme for raw asyncpg connection
            raw_pg_url = REMOTE_PG_URL.replace("postgresql+asyncpg://", "postgresql://")

            if not raw_pg_url or "localhost" in raw_pg_url:
                logger.debug("[SyncWorker] No remote PG configured. Skipping sync cycle.")
                await asyncio.sleep(base_poll_interval)
                continue

            # Attempt to open a remote connection each cycle (tolerates cold starts)
            cloud_conn = await asyncpg.connect(raw_pg_url)

            # Connection success: reset backoff tracking
            current_backoff = initial_backoff
            consecutive_failures = 0

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
                        # Propagates connection exceptions but returns False on data/unexpected errors
                        success = await _push_record_to_cloud(cloud_conn, record)
                        if success:
                            record.synced = True
                            synced_count += 1

                    await session.commit()
                    logger.info(
                        f"[SyncWorker] Cycle complete — {synced_count}/{len(unsynced_records)} records pushed to cloud."
                    )

        except CONNECTION_EXCEPTIONS as e:
            consecutive_failures += 1
            sleep_time = current_backoff
            logger.warning(
                f"[SyncWorker] Connection issue (failure #{consecutive_failures}). "
                f"Retrying in {sleep_time}s. Error details: {e}"
            )
            # Increase backoff time exponentially for the next failure
            current_backoff = min(current_backoff * backoff_factor, max_backoff)

        except asyncpg.PostgresError as e:
            consecutive_failures += 1
            sleep_time = current_backoff
            logger.warning(
                f"[SyncWorker] PostgreSQL error (failure #{consecutive_failures}). "
                f"Retrying in {sleep_time}s. Error details: {e}"
            )
            current_backoff = min(current_backoff * backoff_factor, max_backoff)

        except Exception as e:
            logger.error(f"[SyncWorker] Unexpected error: {e}", exc_info=True)

        finally:
            if cloud_conn and not cloud_conn.is_closed():
                try:
                    await cloud_conn.close()
                except Exception as close_err:
                    logger.debug(f"[SyncWorker] Error closing connection: {close_err}")

        # Poll/Wait for the determined sleep interval (backoff or base polling)
        await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    asyncio.run(sync_outbox_to_cloud())
