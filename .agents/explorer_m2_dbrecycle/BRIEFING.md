# BRIEFING — 2026-07-11T00:16:30+03:00

## Mission
Explore the codebase and recommend database pool recycling and connection warmer implementation details for Milestone 2.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: Milestone 2 Explorer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_dbrecycle
- Original parent: fa9b20fb-0399-49b4-abb8-cb3e569a72a4
- Milestone: Milestone 2: Database Pool Recycling & Connection Warmer

## 🔒 Key Constraints
- Read-only investigation — do NOT implement. Only analyze and document.
- Follow Arabic / RTL UI guidelines if applicable (not applicable to this DB-focused backend explorer task).
- Output reports in the .agents/explorer_m2_dbrecycle directory.

## Current Parent
- Conversation ID: fa9b20fb-0399-49b4-abb8-cb3e569a72a4
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `backend/database.py` (SQLAlchemy async engine configuration)
  - `core/database.py` (SQLAlchemy core async engine with NullPool)
  - `web/shared.py` (FastAPI dependency connection pool setup)
  - `core/pg_sqlite_shim.py` (psycopg2 thread pool wrapper implementation)
  - `core/neon_warmer.py` (Neon DB warming cron script)
  - `render.yaml` (Render cron job configuration)
- **Key findings**:
  - `backend/database.py` currently uses a stale `pool_recycle=1800` parameter which exceeds the Neon Serverless idle timeout (300 seconds), leading to 500 errors.
  - `core/database.py` uses `NullPool`, meaning it closes/opens connections continuously. To optimize performance and satisfy pool requirements, it should be transitioned to a QueuePool with `pool_recycle=280` and `pool_pre_ping=True`.
  - `web/shared.py` configures a SQLAlchemy engine with correct `pool_recycle=280` and `pool_pre_ping=True` properties, but this engine is unused, as the file returns `shim.connect(db_url)` which relies on the psycopg2 connection pool.
  - `core/pg_sqlite_shim.py` uses a psycopg2 `ThreadedConnectionPool` directly, which has no connection recycling or pre-ping mechanism, leading to stale connection issues.
  - `core/neon_warmer.py` runs as an external cron job every 5 minutes in Render. It does not integrate with web/celery workers.
- **Unexplored areas**: None. All target files have been examined.

## Key Decisions Made
- Recommend changing `pool_recycle=1800` to `pool_recycle=280` in `backend/database.py`.
- Recommend changing `poolclass=NullPool` to `poolclass=QueuePool` (or implicit) and adding pool sizing and recycling configurations in `core/database.py`.
- Recommend implementing custom connection recycling (checking connection age against a 280-second limit) and connection testing (pre-pinging with a `SELECT 1` query) in `core/pg_sqlite_shim.py` for its `ThreadedConnectionPool`.

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_dbrecycle\ORIGINAL_REQUEST.md — Original request details.
