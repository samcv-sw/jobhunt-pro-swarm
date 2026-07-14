# BRIEFING — 2026-07-12T13:35:00Z

## Mission
Investigate the codebase for Milestone 3: DB and Cache Rate-Limit Shield, and recommend implementations for:
1. Redis local thread-safe memory caching layer to shield Upstash Redis.
2. Neon PostgreSQL connection pooling configuration.
3. SQLite fail-safety fallback or query queue for Neon database wakeup/sleep and timeouts.

## 🔒 My Identity
- Archetype: Teamwork explorer
- Roles: Read-only investigator, analyzer, synthesizer
- Working directory: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_2
- Original parent: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Milestone: Milestone 3 - DB and Cache Rate-Limit Shield

## 🔒 Key Constraints
- Read-only investigation — do NOT implement (do not modify source files)
- Write findings to C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_2\handoff.md
- Notify parent agent da63cc14-7285-4a19-97cb-7b1eb7a13c9c when done

## Current Parent
- Conversation ID: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Updated: 2026-07-12T13:35:00Z

## Investigation State
- **Explored paths**:
  - `backend/cache.py` (Redis-backed Route Cache)
  - `backend/database.py` (SQLAlchemy Engine + Neon PgBouncer Pool Setup)
  - `backend/main.py` (API Endpoints + lifespan Setup)
  - `backend/models.py` (SQLAlchemy Tables + Outbox model)
  - `backend/sync_worker.py` (Outbox + Job Queue Syncer)
  - `core/edge_cache.py` (Upstash Redis HTTP/REST Client)
  - `core/ats_matcher.py` (ATS scoring + synchronous redis caching)
  - `core/pg_sqlite_shim.py` (Transparent PG Connection Shim with SQLite Fallback)
  - `core/async_db.py` (Direct `asyncpg` PG client)
  - `core/job_queue.py` (Local Job Queue)
  - `web/app_v2.py` (FastAPI Server + ASGI Rate Limiter Middleware)
  - `web/shared.py` (DB helper factory + pool settings)
- **Key findings**:
  - Redis caches route data (`backend/cache.py`), Cover Letters via REST (`core/edge_cache.py`), and ATS calculations (`core/ats_matcher.py` using sync `redis`).
  - Importantly, `web/app_v2.py` has an IP rate limiting middleware that queries Redis via `incr`/`expire` commands for **every single HTTP request**, creating a huge Redis command overhead that will easily exceed the 10k daily limit.
  - Neon PG is pooled in `backend/database.py` (SQLAlchemy) and `core/pg_sqlite_shim.py` (psycopg2 ThreadedConnectionPool). Both cap max connections at 3-5 to respect Neon's 10-connection limit.
  - However, `core/async_db.py` uses raw `asyncpg.create_pool` with `max_size=20` and without statement cache disabling or `-pooler` routing, which is a major bottleneck/failure point.
  - SQLite fallback is handled via `core/pg_sqlite_shim.py` which falls back to local SQLite on connect failure. Outbox streaming via `SyncWorker` keeps PG updated.
- **Unexplored areas**: None.

## Key Decisions Made
- Discovered and analysed all Redis and Postgres connection structures.
- Synthesized caching shield L1/L2 mechanism and query queue architecture.
- Added recommendation for local memory-based IP rate limiter to eliminate high-volume Redis operations.

## Artifact Index
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_2\ORIGINAL_REQUEST.md — Original request description
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_2\BRIEFING.md — Briefing file
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_2\progress.md — Progress log
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_2\handoff.md — Analysis and recommendation handoff report
