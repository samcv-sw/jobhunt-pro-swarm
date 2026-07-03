# Database Connection Hardening Analysis — Handoff Report

## 1. Observation

Direct observations from the codebase reveal details about how database connections, queries, and connection errors are managed in the Outbox Sync Worker:

*   **Connection Establishment & Handling**: In `backend/sync_worker.py` (lines 62–64), the remote database connection is opened using:
    ```python
    # Attempt to open a remote connection each cycle (tolerates cold starts)
    cloud_conn = await asyncpg.connect(raw_pg_url)
    ```
    This connection attempt is surrounded by a `try/except` block catching `asyncpg.PostgresConnectionError` (line 88) and a general `except Exception as e` (line 90):
    ```python
    except asyncpg.PostgresConnectionError as e:
        logger.warning(f"[SyncWorker] Remote DB unreachable (will retry in 30s): {e}")
    except Exception as e:
        logger.error(f"[SyncWorker] Unexpected error: {e}")
    ```

*   **Locations Where `asyncpg.PostgresConnectionError` Can Occur**:
    1.  **Initial Handshake/Connection**: During `asyncpg.connect(raw_pg_url)` (line 63). If the remote database is unreachable, is starting up, or is experiencing a DNS or authentication failure, this call raises `asyncpg.PostgresConnectionError` (or a subclass such as `asyncpg.CannotConnectNowError` or `asyncpg.ConnectionDoesNotExistError`).
    2.  **Record Pushing**: During `conn.execute(...)` in `_push_record_to_cloud` (lines 25–36). If the connection drops or times out mid-batch, this statement raises `asyncpg.ConnectionDoesNotExistError` or `asyncpg.InterfaceError`.

*   **Swallowed Exceptions in Record Push**: In `backend/sync_worker.py` (lines 38–40), `_push_record_to_cloud` catches all exceptions indiscriminately:
    ```python
    except Exception as e:
        logger.error(f"Failed to push record {record.id} to cloud: {e}")
        return False
    ```
    This intercepts connection-related exceptions (e.g., `InterfaceError`, `ConnectionDoesNotExistError`, or `PostgresConnectionError`), logs them as simple push failures, and returns `False` without notifying the caller `sync_outbox_to_cloud` that the connection is dead.

*   **Test Case Structure**: In `tests/e2e/test_database.py` (lines 150–176), `test_sync_outbox_connection_error_graceful_handling` mocks `asyncpg.connect` to raise a generic `asyncpg.PostgresError("Network failure")`:
    ```python
    mock_connect = AsyncMock(side_effect=asyncpg.PostgresError("Network failure"))
    monkeypatch.setattr(asyncpg, "connect", mock_connect)
    ```
    And asserts that the sleep interval called is exactly `30` seconds (the normal poll interval):
    ```python
    assert len(sleep_calls) == 1
    assert sleep_calls[0] == 30
    ```

*   **Exception Hierarchy**: In `asyncpg`, `PostgresConnectionError` is a subclass of `PostgresError`, which itself is a direct subclass of `Exception`. Other client-side connection/network exceptions like `InterfaceError` inherit directly from `Exception` and are not children of `PostgresError`.

---

## 2. Logic Chain

1.  **Swallowed Connection Failures**: Since `_push_record_to_cloud` catches `Exception` and returns `False` (Observation 3), a network disconnect during batch execution does not raise an exception to the main `sync_outbox_to_cloud` loop. Consequently, if the connection drops on the 1st record of a 100-record batch, the worker will repeatedly try to push the remaining 99 records on the dead connection. This causes 100 consecutive timeouts/failures, generating 100 redundant error logs per cycle and causing substantial thread and socket overhead.
2.  **Incomplete Main Catch Block**: The main loop's try-catch only targets `asyncpg.PostgresConnectionError` (Observation 1). However, socket resets, connection drops, or interface errors raise `asyncpg.InterfaceError`, `OSError` (e.g. `ConnectionResetError`), or `asyncio.TimeoutError` which do not inherit from `PostgresConnectionError` (Observation 5). When these occur, they fall into the generic `except Exception` handler, resulting in high-priority "Unexpected error" logs with full tracebacks for normal connection drops.
3.  **Local SQLite State Integrity**: If connection failures bubble up out of the record-pushing loop, the SQLAlchemy transaction in `sync_outbox_to_cloud` (using context manager `async with async_session() as session:`) will exit abnormally, triggering an automatic rollback of the local SQLite session. This prevents records from being marked as `synced=True` in memory and committed to SQLite if they weren't successfully replicated. The remote database utilizes `ON CONFLICT DO NOTHING` on inserts (Observation 3), guaranteeing that retrying the aborted batch on the next cycle is safe and will not cause duplicate records in Postgres.
4.  **Resilience via Backoff**: Implementing an exponential backoff strategy (starting at 5s, doubling each cycle, capped at 300s) on connection failures will prevent the worker from hammering the remote Postgres database during network partitions or server cold starts (Neon serverless scales down to zero when idle).
5.  **Test Suite Incompatibility**: The existing test suite asserts `assert sleep_calls[0] == 30` (Observation 4) under a simulated connection failure. Introducing backoff means the first failure will sleep for `5.0` seconds instead of `30`. Therefore, the test assertion must be updated to expect `5.0` seconds, and an additional test should be added to verify that subsequent failures scale the delay exponentially (e.g., `5.0` -> `10.0` -> `20.0`).

---

## 3. Caveats

*   **Neon Serverless Cold Starts**: Neon databases auto-suspend after inactivity. The connection backoff starts at `5s`, which is usually enough for a cold start, but subsequent cycles might hit the backoff loop if DNS resolution or handshake takes longer. This is expected and handled gracefully by the exponential retry.
*   **Local DB Integrity**: The logic assumes that no concurrent processes write directly to the local SQLite database without logging to the `SyncOutbox` table.

---

## 4. Conclusion

To harden `sync_worker.py` against database connection drops, the following changes are proposed:
1.  Define a shared `CONNECTION_EXCEPTIONS` tuple containing `asyncpg.PostgresConnectionError`, `asyncpg.InterfaceError`, `OSError`, and `asyncio.TimeoutError`.
2.  Update `_push_record_to_cloud` to intercept `CONNECTION_EXCEPTIONS`, log a warning, and re-raise them so the batch is immediately aborted when a connection drop occurs.
3.  Implement exponential backoff inside `sync_outbox_to_cloud` using `initial_backoff = 5.0`, `max_backoff = 300.0`, and `backoff_factor = 2.0`.
4.  Catch `asyncpg.PostgresError` in the main loop to handle general database errors gracefully.
5.  Update `tests/e2e/test_database.py` to assert the updated backoff delay and add a test case to verify exponential scaling.

Complete copy-paste-ready implementations have been placed in the agent directory:
*   **Proposed Worker**: `.agents/explorer_dbsync_2/proposed_sync_worker.py`
*   **Proposed Test Patch**: `.agents/explorer_dbsync_2/proposed_test_database.patch`

---

## 5. Verification Method

### 1. Unified Test Execution Command
Execute the database E2E tests using the global pytest interpreter with PYTHONPATH set:
```powershell
$env:PYTHONPATH="."; pytest tests/e2e/test_database.py
```

### 2. Invalidation Conditions
The verification fails if:
*   Any database tests raise `ModuleNotFoundError: No module named 'backend'`.
*   The worker crashes (exits the loop) when encountering any network/connection drops.
*   The worker continues to try pushing records inside the loop after the connection has been lost.
*   The test logs show duplicate pushes for successfully committed outbox records.
