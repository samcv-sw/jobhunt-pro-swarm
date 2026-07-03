# Handoff Report — teamwork_preview_explorer

## 1. Observation
*   **Backend Database Config**: `backend/database.py` defines `LOCAL_DB_URL` as SQLite and `REMOTE_PG_URL` as Postgres (lines 11-12) and binds `async_session` to SQLite (lines 14-33).
*   **Sync Worker Execution**: `backend/sync_worker.py` queries unsynced records of `SyncOutbox` from SQLite and streams them to the remote Postgres database every 5 seconds (lines 11-81).
*   **Celery Queue Config**: `backend/celery_app.py` maps specific tasks to queues (lines 24-30): `scrape_jobs` -> `scraping`, `generate_cover_letter` -> `ai_inference`, and `send_application_email` -> `email_sender`.
*   **Frontend OPFS Storage**: `frontend/src/app/db/wasm-db.ts` loads browser-side SQLite Wasm from the Origin Private File System (OPFS) (lines 39-52), which operates client-side only.
*   **Peers' Analysis**: `.agents/explorer_k8s_2/analysis.md` and `.agents/explorer_k8s_3/analysis.md` present template proposals and highlights the ReadWriteOnce (RWO) storage mode limitations for co-located files.
*   **PostgreSQL Init Script**: `init.sql` (lines 8-340) defines schema for Postgres, and lines 341-357 alters `job_queue` which is created dynamically by `web/app_v2.py` (line 1333).

## 2. Logic Chain
1.  Because `backend/main.py` writes mutations to SQLite locally and `backend/sync_worker.py` polls SQLite to push to Postgres (Observation 1, 2), they must both access the same SQLite database file.
2.  Because standard Kubernetes storage classes only support ReadWriteOnce (RWO) volumes, deploying backend and sync-worker as separate pods will cause volume mount failures on standard clusters (Observation 5).
3.  Therefore, co-locating the `fastapi` backend and the `sync-worker` as sidecar containers in the same Pod allows them to share a local ephemeral/RWO volume, resolving storage compatibility constraints.
4.  Because Celery tasks are routed to queues with vastly different resource requirements (e.g. `scraping` runs headless Chrome and needs high memory limits, while `email_sender` is light) (Observation 3), deploying workers into queue-isolated deployments prevents memory contention and bottlenecks.
5.  Because the Next.js frontend runs as a static SPA and stores local data on client-side browser OPFS (Observation 4), no server-side PersistentVolumeClaims are required for client storage.
6.  Because path-based ingress rules (e.g., `/` for frontend and `/api` for backend) route traffic under a single domain host, CORS cross-origin complexities are natively bypassed.

## 3. Caveats
*   The startup scripts `start_safe.py` (referenced in `Dockerfile.cloud` line 69) and `start_cloud.py` (referenced in `Dockerfile.hf` line 40) do not exist in the workspace. Our templates bypass this by defining explicit run commands (e.g., `uvicorn backend.main:app` and `python -m backend.sync_worker`).
*   External databases (e.g. Neon PostgreSQL, AWS ElastiCache) can be mapped in `values.yaml` but have not been live-tested.

## 4. Conclusion
We propose a synthesized, production-grade Helm chart layout under `deploy/k8s/` that resolves SQLite sharing constraints via a co-located Sidecar pod configuration, organizes Celery workers into resource-isolated deployments matching application queues, and eliminates CORS problems using path-based Ingress routing. All copy-paste-ready templates are documented in `analysis.md`.

## 5. Verification Method
To verify the Helm chart structure and syntax:
1.  **Linter Check**: Run `helm lint deploy/k8s/` to check for chart definition format and syntax compliance.
2.  **Expansion Check**: Run `helm template jobhunt-pro deploy/k8s/ --values deploy/k8s/values.yaml` to verify the generated Kubernetes resource manifests parse without token expansion errors.
