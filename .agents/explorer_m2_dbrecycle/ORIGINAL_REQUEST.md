## 2026-07-11T00:14:41Z
You are teamwork_preview_explorer.
Your role is to explore the codebase and recommend an implementation strategy for Milestone 2: Database Pool Recycling & Connection Warmer.

Your identity:
- Archetype: teamwork_preview_explorer
- Role: Milestone 2 Explorer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_dbrecycle

Context & Requirements:
- We need to configure SQLAlchemy connection pool properties (`pool_recycle=280`, `pool_pre_ping=True`) to automatically handle Neon Serverless Postgres DB spin-down and cold starts without throwing `500 Internal Server Error` exceptions.
- Target files:
  1. `backend/database.py`
  2. `core/database.py`
  3. `web/shared.py` (check if it handles database connections and if pool_recycle is already correct or needs modification)
  4. `core/pg_sqlite_shim.py` (check if the psycopg2 connection pool also needs any recycling or connection warmer properties)
  5. `core/neon_warmer.py` (check how it runs and if it is integrated with the web or celery worker)

What to do:
1. Examine these target files.
2. Analyze where SQLAlchemy engines are created and ensure they all define `pool_recycle=280` and `pool_pre_ping=True` when connecting to PostgreSQL/Neon.
3. Check `core/pg_sqlite_shim.py` psycopg2 pool instantiation and check if we should add connection testing or timeout/recycling logic.
4. Formulate the exact code modifications required. Do not make code modifications yourself (as you are a read-only Explorer).
5. Write your detailed analysis and recommended strategy to c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_dbrecycle\handoff.md.
6. Update your progress.md inside your folder.
7. When done, send a message back to parent (ID: fa9b20fb-0399-49b4-abb8-cb3e569a72a4) claiming completion.
