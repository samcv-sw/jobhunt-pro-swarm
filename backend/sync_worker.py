"""
Sync Worker — Outbox Pattern
Streams local SQLite mutations to remote Neon PostgreSQL asynchronously.
Handles connection failures gracefully; never crashes the process.
"""

import asyncio
import gc
import json
import logging
import os
import sys
import time

gc.set_threshold(50, 5, 5)

import asyncpg

if not hasattr(asyncpg, "Error"):
    asyncpg.Error = asyncpg.PostgresError
import contextlib

from sqlalchemy import select

from .database import REMOTE_PG_URL, async_session, format_neon_connection_string
from .models import SyncOutbox

logger = logging.getLogger(__name__)

CONNECTION_EXCEPTIONS = (
    asyncpg.PostgresConnectionError,
    asyncpg.InterfaceError,
    OSError,
    asyncio.TimeoutError,
)

# TooManyConnectionsError is not always present in older asyncpg builds.
_TOO_MANY_CONNS = getattr(asyncpg, "TooManyConnectionsError", None)


def _build_pg_url(raw_url: str) -> str:
    """Ensure the asyncpg DSN has the PgBouncer-required params.

    Appends ``sslmode=require`` and ``prepareThreshold=0`` to *raw_url* when
    they are not already present.  Both params are needed so that PgBouncer
    (transaction-pooling mode) does not receive named prepared statements it
    cannot route.

    Args:
        raw_url: A ``postgresql://`` DSN, possibly with an existing query string.

    Returns:
        The modified DSN with the two params guaranteed to be present.
    """
    from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

    try:
        parsed = urlparse(raw_url)
        params = dict(parse_qsl(parsed.query))
        params.setdefault("sslmode", "require")
        params.setdefault("prepareThreshold", "0")
        new_query = urlencode(params)
        return urlunparse(parsed._replace(query=new_query))
    except Exception as exc:
        logger.warning("[SyncWorker] Could not append PgBouncer params to URL: %s", exc)
        return raw_url


async def _connect_with_retry(dsn: str, **connect_kwargs) -> asyncpg.Connection:
    """Connect to Postgres with exponential-backoff retry on TooManyConnectionsError.

    Attempt schedule: immediate → 2 s → 4 s → 8 s (3 retries after the
    initial attempt, 4 total).

    Args:
        dsn:             asyncpg-compatible DSN.
        **connect_kwargs: Extra kwargs forwarded to ``asyncpg.connect()``.

    Returns:
        An open ``asyncpg.Connection``.

    Raises:
        Exception: Re-raises the last exception if all attempts are exhausted.
    """
    max_attempts = 4  # 1 initial + 3 retries
    delays = [0, 2, 4, 8]  # seconds before each attempt
    last_exc: Exception | None = None

    for attempt, delay in enumerate(delays, start=1):
        if delay:
            logger.warning(
                "[SyncWorker] Connection failed — retrying in %ds (attempt %d/%d)",
                delay,
                attempt,
                max_attempts,
            )
            await asyncio.sleep(delay)
        try:
            conn = await asyncpg.connect(dsn, **connect_kwargs)
            if attempt > 1:
                logger.info("[SyncWorker] Reconnected successfully on attempt %d.", attempt)
            return conn
        except Exception as exc:
            last_exc = exc
            # Retry on connection-related failures or cold starts
            if isinstance(
                exc, (asyncpg.PostgresConnectionError, asyncio.TimeoutError, OSError)
            ) or (_TOO_MANY_CONNS and isinstance(exc, _TOO_MANY_CONNS)):
                logger.warning("[SyncWorker] Connection error on attempt %d: %s", attempt, exc)
                continue
            raise

    raise last_exc  # type: ignore[misc]


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
        logger.error(
            f"Failed to push record {record.id} to cloud (soft error/data failure): {e}",
            exc_info=True,
        )
        try:
            log_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "dead_letter_queue.log"
            )
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
            logger.error(
                f"Failed to write record {record.id} to dead-letter queue log: {write_err}"
            )
        return False


async def sync_outbox_to_cloud():
    """
    Background worker that continuously streams local SQLite changes
    to the Neon PostgreSQL database via the outbox pattern.
    Also acts as a fallback worker for local SQLite job_queue tasks.
    Handles connection failures gracefully without crashing.
    """
    logger.info("[SyncWorker] Started. Monitoring outbox and job queue...")

    cloud_conn = None
    while True:
        did_work = False
        connection_failed = False

        # 1. Process local SQLite job queue tasks
        try:
            from core.job_queue import complete_task, dequeue_task, fail_task

            task = await asyncio.to_thread(dequeue_task)
            if task:
                did_work = True
                logger.info(
                    f"[SyncWorker] Dequeued local task #{task['id']} (type: {task['task_type']})"
                )
                if task["task_type"] == "scrape":
                    payload = task["payload"]
                    target_urls = payload.get("target_urls", [])
                    user_id = payload.get("user_id", "")

                    try:
                        from scrapers.stealth_ingest import stealth_scrape_jobs

                        structured_jobs = await stealth_scrape_jobs(target_urls)
                        logger.info(
                            f"[SyncWorker] Local scrape completed for user {user_id}: {len(structured_jobs)} jobs."
                        )

                        # Mark task as completed
                        await asyncio.to_thread(complete_task, task["id"])

                        # Add a record to the outbox to sync results to remote PostgreSQL
                        async with async_session() as session:
                            outbox = SyncOutbox(
                                table_name="scraped_jobs_sync",
                                record_id=f"local_job_{task['id']}",
                                operation="INSERT",
                                payload={
                                    "user_id": user_id,
                                    "jobs_found": len(structured_jobs),
                                    "jobs": structured_jobs,
                                    "timestamp": time.time(),
                                },
                                synced=False,
                            )
                            session.add(outbox)
                            await session.commit()
                    except Exception as scrape_exc:
                        logger.error(f"[SyncWorker] Local scrape task failed: {scrape_exc}")
                        await asyncio.to_thread(fail_task, task["id"], str(scrape_exc))
        except Exception as task_exc:
            logger.error(f"[SyncWorker] Error processing local job queue: {task_exc}")

        # 2. Sync outbox records to remote PG
        try:
            db_url_raw = REMOTE_PG_URL
            if not db_url_raw or "localhost" in db_url_raw:
                logger.debug("[SyncWorker] No remote PG configured. Skipping outbox sync cycle.")
            else:
                formatted_url = format_neon_connection_string(db_url_raw)
                if "?" in formatted_url:
                    raw_pg_url = formatted_url.split("?", 1)[0]
                else:
                    raw_pg_url = formatted_url

                if raw_pg_url.startswith("postgresql+asyncpg://"):
                    raw_pg_url = raw_pg_url.replace("postgresql+asyncpg://", "postgresql://", 1)
                elif raw_pg_url.startswith("postgres://"):
                    raw_pg_url = raw_pg_url.replace("postgres://", "postgresql://", 1)

                # Reuse connection if active, otherwise reconnect
                if not cloud_conn or cloud_conn.is_closed():
                    logger.info("[SyncWorker] Re-establishing remote DB connection...")
                    # Append PgBouncer-required params before connecting
                    pgbouncer_url = _build_pg_url(raw_pg_url)
                    cloud_conn = await _connect_with_retry(
                        pgbouncer_url,
                        ssl="require",
                        statement_cache_size=0,
                        timeout=10.0,
                    )

                async with async_session() as session:
                    result = await session.execute(
                        select(SyncOutbox).where(SyncOutbox.synced.is_(False)).limit(100)
                    )
                    unsynced_records = result.scalars().all()

                    if unsynced_records:
                        did_work = True
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
                                    logger.warning(
                                        f"[SyncWorker] Record {record.id} routed to dead-letter queue (DLQ) due to soft error."
                                    )
                            except CONNECTION_EXCEPTIONS as e:
                                logger.error(
                                    f"[SyncWorker] Connection lost during record push. Aborting batch: {e}"
                                )
                                connection_error = e
                                break

                        await session.commit()
                        if connection_error:
                            raise connection_error

                        logger.info(
                            f"[SyncWorker] Cycle complete — {synced_count}/{len(unsynced_records)} records pushed to cloud."
                        )

        except (TimeoutError, asyncpg.Error, asyncpg.InterfaceError, OSError) as e:
            logger.warning(
                f"[SyncWorker] Remote DB connection lost/unreachable (will retry in 30s): {e}"
            )
            connection_failed = True
            if cloud_conn:
                with contextlib.suppress(Exception):
                    await cloud_conn.close()
                cloud_conn = None
        except Exception as e:
            logger.error(f"[SyncWorker] Unexpected error: {e}")

        # Explicit garbage collection to free up memory from db sessions
        gc.collect()

        # Poll dynamically: 30s if connection failed, idle, or in testing mode; 1s if work was done successfully
        is_testing = "pytest" in sys.modules or os.getenv("TESTING", "false").lower() == "true"
        sleep_time = 30 if (connection_failed or not did_work or is_testing) else 1
        await asyncio.sleep(sleep_time)


if __name__ == "__main__":
    asyncio.run(sync_outbox_to_cloud())
