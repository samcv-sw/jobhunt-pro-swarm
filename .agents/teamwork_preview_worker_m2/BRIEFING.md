# BRIEFING — 2026-07-03T16:19:03+03:00

## Mission
Implement local Vector DB (Qdrant) integration for RAG-based cover letter generation.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_m2
- Original parent: c4e4ddf0-be49-4898-928d-66a9918ca89c
- Milestone: Milestone 2: RAG Cover Letter Integration

## 🔒 Key Constraints
- CODE_ONLY network mode: no external internet/HTTP calls.
- DO NOT CHEAT: real state, real behavior, no hardcoded verification strings or mock logic.
- Follow Arabic / RTL UI guidelines if applicable (none in backend, but keep in mind).

## Current Parent
- Conversation ID: c4e4ddf0-be49-4898-928d-66a9918ca89c
- Updated: not yet

## Task Summary
- **What to build**:
  1. Add `qdrant-client` to `requirements.txt` and install.
  2. Implement `core/vector_db.py` to manage Qdrant client, initialize collection ("cover_letters"), insert and query letters. Include a deterministic fallback hashing vector generator if `get_embedding` is offline or empty.
  3. Integrate into `backend/ai_engine.py` (optional `user_id` and `use_rag` parameters, retrieve, inject style block, ingest generated letter).
  4. Update `backend/main.py` (retrieve `user_id` from JWT, pass it to task/generator).
  5. Update `backend/tasks.py` (add `user_id` parameter to celery task).
  6. Append environment variables to `.env` and `.env.example`.
  7. Copy proposed tests from `teamwork_preview_explorer_rag_3` to `tests/test_rag.py`.
- **Success criteria**:
  - `pytest tests/test_rag.py` passes cleanly.
  - Cover letters generated are automatically stored in Qdrant and retrieved dynamically.
- **Interface contracts**: backend/main.py, backend/ai_engine.py, backend/tasks.py, core/vector_db.py
- **Code layout**: Python backend codebase.

## Key Decisions Made
- Use Qdrant client with `path` or `in_memory` configuration.
- Implement token-hashing deterministic fallback as L2-normalized 768-d vector.

## Artifact Index
- `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_m2\handoff.md` — Handoff report

## Change Tracker
- **Files modified**: None yet
- **Build status**: TBD
- **Pending issues**: TBD

## Quality Status
- **Build/test result**: TBD
- **Lint status**: TBD
- **Tests added/modified**: None yet

## Loaded Skills
- None loaded.
