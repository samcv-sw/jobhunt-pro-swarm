# BRIEFING — 2026-07-03T13:18:35Z

## Mission
Explore the codebase and propose a Helm chart design under `deploy/k8s/` orchestrating FastAPI backend, Next.js frontend, Celery workers, Redis, Postgres, and SQLite OPFS volume claims.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: Investigator, Analyst, Explorer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_3
- Original parent: bb20b5b1-9c5c-412c-9da2-4c162a845a3b
- Milestone: Helm Chart Design

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- CODE_ONLY network mode (no external websites/services, no external curl/wget)
- Write only to own folder (c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_3)
- Read-only on the rest of the workspace

## Current Parent
- Conversation ID: bb20b5b1-9c5c-412c-9da2-4c162a845a3b
- Updated: 2026-07-03T13:18:35Z

## Investigation State
- **Explored paths**: `docker-compose.yml`, `docker-compose.prod.yml`, `backend/database.py`, `backend/sync_worker.py`, `backend/celery_app.py`, `frontend/next.config.ts`, `frontend/src/app/db/wasm-db.ts`
- **Key findings**: Next.js static SPA export; client-side browser OPFS (no server volumes needed); backend/sync-worker SQLite sharing; Celery task queue routing (`scraping`, `ai_inference`, `email_sender`).
- **Unexplored areas**: None (investigation complete)

## Key Decisions Made
- Propose sidecar container architecture inside the backend Deployment pod for backend and sync-worker to share SQLite local DB file under `ReadWriteOnce` volume constraints.
- Map Celery task routes to independent, separately scalable Deployment worker pools.
- Use standard Ingress routing rules to serve frontend and backend API/WebSocket endpoints under a single domain.

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_3\analysis.md — Detailed Helm chart design and configuration analysis
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_3\handoff.md — Handoff report for orchestrator
