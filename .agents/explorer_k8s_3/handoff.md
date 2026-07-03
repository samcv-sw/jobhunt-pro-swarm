# Handoff Report — Helm Chart Design

This handoff details the analysis and proposed Helm chart design for the JobHunt Pro stack.

## 1. Observation
We analyzed the codebase and docker-compose configurations, observing the following exact details:
- **FastAPI backend**: Dockerfile CMD runs `uvicorn backend.main:app` on port 8000. It reads and writes SQLite locally (default: `/app/data/jobhunt_saas_v2.db` or `/app/data/jobhunt_local.db`) and syncs to a remote PostgreSQL DB (defined by `DATABASE_URL` and `DATABASE_URL_SYNC`).
- **Next.js frontend**: `frontend/next.config.ts` defines `output: "export"`. It builds a static SPA, but the production `Dockerfile.frontend` serves the files on port 3000 via a Node.js runner.
- **Celery configuration**: `backend/celery_app.py` configures specialized task routing to three distinct queues:
  ```python
  task_routes={
      "backend.tasks.scrape_jobs": {"queue": "scraping"},
      "backend.tasks.generate_cover_letter": {"queue": "ai_inference"},
      "backend.tasks.send_application_email": {"queue": "email_sender"},
  }
  ```
- **SQLite OPFS client**: `frontend/src/app/db/wasm-db.ts` uses browser OPFS for decentralized client-side storage, which does not require server-side volume claims.
- **SQLite Server DB & Sync Worker**: The FastAPI `app` and `sync-worker` (command: `python -m backend.sync_worker`) share the same local SQLite database file at `/app/data/`.

## 2. Logic Chain
- Since the Next.js frontend is served on port 3000 and the backend on port 8000, we need Ingress rules that route root path `/` to the frontend service and backend endpoints (`/api/`, `/ws`, `/docs`, `/redoc`) to the backend service.
- Because Celery routes tasks into three distinct queues with distinct resource requirements (e.g. `scraping` queue runs Headless Chrome and requires substantial memory/CPU while `email_sender` is extremely lightweight), they should be managed via independent Celery worker pool deployments in the Helm chart.
- Because the backend and the sync-worker both read/write to the same SQLite database file, they must share access to the same storage mount.
- If we deploy them as separate Pods, it requires a `ReadWriteMany` (RWX) storage class. Since most cloud providers default to `ReadWriteOnce` (RWO), a multi-container Pod structure (running the FastAPI app and the `sync-worker` in the same pod) is the most robust and cloud-agnostic configuration.

## 3. Caveats
- Browser-side OPFS is fully serverless and runs in the client browser, hence no Helm volume configurations are needed for it.
- Actual Helm execution, Helm repository additions, and cluster deployments were not performed as this is a read-only investigation.

## 4. Conclusion
We proposed a production-ready Helm chart design under `deploy/k8s/` that packages:
1. Next.js frontend (deployment, service, ingress rules)
2. FastAPI backend + sync-worker (running as a co-located sidecar inside a single deployment to safely share an RWO persistent volume claim)
3. Celery worker pool deployments (dynamically scalable based on queue-specific needs)
4. Redis & Postgres (deployable internally as sub-charts or configurable to external instances)
5. PersistentVolumeClaim for SQLite database storage.

All configurations and drafts have been documented in the `analysis.md` report.

## 5. Verification Method
Verify the syntax and template generation of the implemented chart using:
1. `helm lint deploy/k8s/` - check for structural correctness and conventions.
2. `helm template jobhunt-pro deploy/k8s/ --values deploy/k8s/values.yaml` - check resource rendering.
