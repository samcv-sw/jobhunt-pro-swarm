# BRIEFING — 2026-07-03T13:19:50Z

## Mission
Explore the codebase and propose a Helm chart design under `deploy/k8s/` that orchestrates FastAPI backend, Next.js frontend, Celery workers, Redis, Postgres, and SQLite OPFS volume claims.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: Explorer, Investigator, Synthesizer
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_1
- Original parent: bb20b5b1-9c5c-412c-9da2-4c162a845a3b
- Milestone: k8s-m1

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Code-only network mode: no external HTTP/HTTPS connections allowed

## Current Parent
- Conversation ID: bb20b5b1-9c5c-412c-9da2-4c162a845a3b
- Updated: 2026-07-03T13:18:45Z (Received status request)

## Investigation State
- **Explored paths**:
  - `docker-compose.yml`, `docker-compose.prod.yml`
  - `Dockerfile`, `Dockerfile.cloud`, `Dockerfile.frontend`
  - `init.sql`, `backend/database.py`, `backend/models.py`, `backend/tasks.py`
  - `core/queue_worker.py`, `core/pg_sqlite_shim.py`
  - `.agents/explorer_k8s_2/analysis.md`, `.agents/explorer_k8s_3/analysis.md`
- **Key findings**:
  - Browser SQLite (Wasm-OPFS) is purely client-side; no server PVC is needed.
  - Server SQLite database is used locally by FastAPI and `sync_worker` to sync to Postgres. They must share the same database file.
  - Since standard K8s storage is ReadWriteOnce (RWO), deploying them as separate pods fails. Sidecar pattern in the backend pod solves this.
  - Celery uses distinct queues (`scraping`, `ai_inference`, `email_sender`) which have vastly different resource characteristics (e.g. Scraping needs headless Chrome and more memory). Splitting workers into queue-isolated pools is recommended.
  - Path-based routing in Ingress (`/` to frontend, `/api` / `/ws` / `/docs` to backend) avoids CORS issues natively.
- **Unexplored areas**: None.

## Key Decisions Made
- Synthesized findings from Explorer 2 and Explorer 3, resulting in a hardened Helm Chart design in `analysis.md`.
- Chosen default sidecar architecture for the sync worker to maximize cluster portability (RWO).
- Chosen range-based loop over worker pools in Celery templates.

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_1\ORIGINAL_REQUEST.md — Original request and status request log
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_1\BRIEFING.md — Current working briefing document
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_1\analysis.md — Synthesized Helm chart proposal and complete templates
