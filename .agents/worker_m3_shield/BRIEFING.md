# BRIEFING — 2026-07-12T13:59:45Z

## Mission
Implement Milestone 3: DB and Cache Rate-Limit Shield.

## 🔒 My Identity
- Archetype: implementer
- Roles: implementer, qa, specialist
- Working directory: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m3_shield
- Original parent: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Milestone: Milestone 3 - DB and Cache Rate-Limit Shield

## 🔒 Key Constraints
- Maximize autonomy: make intelligent defaults, do not ask user.
- CODE_ONLY network mode: no external requests, use only local tools.
- Never write source code inside the .agents directory.

## Current Parent
- Conversation ID: da63cc14-7285-4a19-97cb-7b1eb7a13c9c
- Updated: not yet

## Task Summary
- **What to build**: 
  1. Thread-safe L1 memory cache shield inside `core/edge_cache.py` as an in-process cache wrapper mapping TTL by key prefix (immutable cover letters 10 min, ATS score 30 min, campaigns 1 min, rate-limit resets 5 sec).
  2. ASGI Rate-Limiting middleware in `web/app_v2.py` changed to run purely in memory using thread-safe sliding window.
  3. Update `core/ats_matcher.py` (and any other files calling synchronous standard redis) to use `edge_cache` asynchronously.
  4. Harden direct asyncpg pool parameters in `core/async_db.py` to match SQLAlchemy limits (max_size=3, statement_cache_size=0, pooler routing, max_inactive_connection_lifetime=280).
  5. SQLite Write-Buffer / Failover Query Queue in `core/pg_sqlite_shim.py` to buffer writes when Neon is offline, and process them asynchronously in a background loop.
- **Success criteria**: All functionality verified via unit/integration tests with no regressions.
- **Interface contracts**: Refer to handoff reports.
- **Code layout**: Source in core/ and web/.

## Change Tracker
- **Files modified**: None
- **Build status**: Unknown
- **Pending issues**: None

## Quality Status
- **Build/test result**: TBD
- **Lint status**: TBD
- **Tests added/modified**: TBD

## Loaded Skills
- None

## Key Decisions Made
- [TBD]

## Artifact Index
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m3_shield\ORIGINAL_REQUEST.md - Original request
