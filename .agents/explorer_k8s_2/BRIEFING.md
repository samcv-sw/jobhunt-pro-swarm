# BRIEFING — 2026-07-03T13:18:00Z

## Mission
Explore the codebase and propose a design for a Helm chart under `deploy/k8s/` that orchestrates FastAPI backend, Next.js frontend, Celery workers, Redis, Postgres, and SQLite OPFS volume claims.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: read-only investigator
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_2
- Original parent: bb20b5b1-9c5c-412c-9da2-4c162a845a3b
- Milestone: Helm Chart Design

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Analyze docker-compose, docker-compose.prod, SCOPE.md, Dockerfiles
- Propose templates and values.yaml structure in analysis.md

## Current Parent
- Conversation ID: bb20b5b1-9c5c-412c-9da2-4c162a845a3b
- Updated: 2026-07-03T13:18:00Z

## Investigation State
- **Explored paths**:
  - `docker-compose.yml`, `docker-compose.prod.yml`, `infrastructure/docker-compose.production.yml`
  - `Dockerfile`, `Dockerfile.frontend`, `Dockerfile.cloud`
  - `backend/database.py`, `backend/sync_worker.py`, `backend/main.py`, `backend/tasks.py`, `backend/celery_app.py`
  - `frontend/next.config.ts`
  - `nginx.conf`
- **Key findings**:
  - Next.js uses client-side SQLite WASM via browser OPFS. No server-side PVC is needed for client-side OPFS.
  - Backend uses a local SQLite database for zero-latency operations synced via `sync_worker.py` to Postgres. This requires a shared storage approach in K8s (either RWX PVC or a sidecar container in a single pod sharing an ephemeral RWO volume).
  - WebSockets (`/ws/war-room`) and API requests (`/api/*`) are handled by FastAPI backend.
  - Frontend is a static export client-side SPA.
- **Unexplored areas**: None

## Key Decisions Made
- Proposed sidecar deployment of the sync worker as the default mode in backend-deployment.yaml to avoid RWX PV requirements on microk8s/local environments.
- Configured path-based Ingress routing to solve CORS natively.

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_2\analysis.md — Main Analysis Report
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_2\handoff.md — Handoff Report
