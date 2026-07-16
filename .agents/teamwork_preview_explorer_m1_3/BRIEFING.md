# BRIEFING — 2026-07-15T10:02:00+03:00

## Mission
Perform a read-only audit of FastAPI web routers and frontend serving endpoints, identify TODOs, placeholders, template rendering issues, performance issues, and inconsistencies with the backend REST API, and propose an optimization/cleanup strategy.

## 🔒 My Identity
- Archetype: Teamwork explorer
- Roles: Web Routers Auditor
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3
- Original parent: 662e7cb1-3688-4af0-9166-11889f406b2b
- Milestone: m1_3

## 🔒 Key Constraints
- Read-only investigation — do NOT implement.
- Inspect web/app_v2.py and web/routers/*.py.
- Propose complete optimization and cleanup strategy.

## Current Parent
- Conversation ID: 662e7cb1-3688-4af0-9166-11889f406b2b
- Updated: 2026-07-15T10:02:00+03:00

## Investigation State
- **Explored paths**: web/app_v2.py, web/routers/*.py, backend/database.py, core/database.py, core/async_db.py, tests/conftest.py, tests/test_routers_v2.py
- **Key findings**:
  - Missing `db` instance definition in `core/database.py` breaks `candidate`, `squads`, and `webhook_bot` web routers.
  - Typo `from typing import list` in `growth_station.py` raises `ImportError`.
  - `web/routers/en.py` is dead code because prefix is stripped in middleware.
  - Multi-instantiated `Jinja2Templates` leads to duplicate config/behavior.
  - Split SQLite databases paths between backend (`jobhunt_local.db`) and web (`jobhunt_saas_v2.db`) leads to desynchronized state in local dev.
  - Zero test coverage for web-tier router loading, which masked import/startup crashes.
- **Unexplored areas**: None, audit complete.

## Key Decisions Made
- Perform search-first audit to limit token usage.
- Bridge core.database and core.async_db to restore compatibility.

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3\analysis.md — Main audit report and optimization strategy
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3\handoff.md — Summary handoff report
