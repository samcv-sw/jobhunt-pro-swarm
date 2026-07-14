# BRIEFING — 2026-07-12T13:26:00Z

## Mission
Investigate the codebase for Upstash Redis caching, Neon PostgreSQL connection pooling, and propose thread-safe local caching + SQLite fallback/query queue solutions.

## 🔒 My Identity
- Archetype: explorer
- Roles: Read-only investigator
- Working directory: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_1
- Original parent: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Milestone: Milestone 3 - DB and Cache Rate-Limit Shield

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Operating in CODE_ONLY network mode. No external HTTP requests.

## Current Parent
- Conversation ID: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Updated: 2026-07-12T13:26:00Z

## Investigation State
- **Explored paths**:
  - `backend/cache.py` - FastAPI cache backend config (Redis vs InMemory).
  - `core/edge_cache.py` - Upstash Redis REST API interface and LLM caching helper functions.
  - `core/pg_sqlite_shim.py` - Database routing shim supporting PG and SQLite fallback.
  - `backend/database.py` - SQLAlchemy database connection setup for FastAPI.
  - `core/async_db.py` - Asyncpg database connector and job queue logic.
  - `core/neon_warmer.py` - Chronological database warmer logic.
- **Key findings**:
  - Redis is used as FastAPI Cache (socket pool max 10) and EdgeCache (HTTP REST API) for LLM cover letters, ATS scores, active campaigns, and Groq rate-limits.
  - Connection pooling is configured in `pg_sqlite_shim.py` (psycopg2 ThreadedConnectionPool, max 3) and `backend/database.py` (SQLAlchemy, size 3, max overflow 2). Both use 280s idle recycling and `SELECT 1` pre-ping checks.
  - The SQLite fallback currently does a hard switch when Neon is offline, causing data fragmentation across containers and eventual data loss when PG comes back online.
- **Unexplored areas**: None. Codebase mapped completely.

## Key Decisions Made
- Recommend L1/L2 write-through caching in `core/edge_cache.py` to shield Redis.
- Recommend offline write-journaling and async replay daemon in `core/pg_sqlite_shim.py` to handle Neon sleep/timeouts safely.

## Artifact Index
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_1\ORIGINAL_REQUEST.md — Original request details.
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m3_hf_1\BRIEFING.md — Current briefing state.
