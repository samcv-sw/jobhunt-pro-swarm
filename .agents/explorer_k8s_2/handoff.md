# Handoff Report — explorer_k8s_2

This report details the architectural investigation and proposal for the JobHunt Pro Helm chart, mapping out all service dependencies, environment configurations, and storage requirements.

## 1. Observation
I directly observed and verified the following configurations:
- **FastAPI Database Connections**: In `backend/database.py` (lines 11-12):
  ```python
  LOCAL_DB_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./jobhunt_local.db")
  REMOTE_PG_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/jobhunt_pro")
  ```
- **Next.js Export Mode**: In `frontend/next.config.ts` (lines 3-4):
  ```typescript
  const nextConfig: NextConfig = {
    output: "export",
  ```
- **Outbox Synchronization**: In `backend/sync_worker.py` (lines 37-41):
  ```python
  async def sync_outbox_to_cloud():
      """
      Background worker that continuously streams local SQLite changes
      to the Neon PostgreSQL database via the outbox pattern.
  ```
- **Celery Task Routes**: In `backend/celery_app.py` (lines 25-29):
  ```python
      task_routes={
          "backend.tasks.scrape_jobs": {"queue": "scraping"},
          "backend.tasks.generate_cover_letter": {"queue": "ai_inference"},
          "backend.tasks.send_application_email": {"queue": "email_sender"},
      }
  ```
- **Compose Service Setup**: In `docker-compose.yml`, the backend `app` mounts `app_data:/app/data` (line 87) and defines `DB_PATH=/app/data/jobhunt_saas_v2.db` (line 79). The `sync-worker` runs `python -m backend.sync_worker` (line 154) but has no volume mounts.

## 2. Logic Chain
1. **Frontend Isolation**: Since Next.js has `output: "export"` (Observation 2), it is compiled as a static client-side SPA. It uses WebAssembly + OPFS in the browser itself, meaning client-side SQLite does not require a Kubernetes volume claim.
2. **Server-Side SQLite persistence**: The FastAPI backend acts as the write-target for the Dual Database Pattern (Observation 1), caching data in SQLite. This file must persist across pod restarts, so a Persistent Volume Claim (PVC) mounted at `/app/data` is required.
3. **Shared SQLite File Access**: Because the `sync-worker` reads changes from the local SQLite file and syncs them to Postgres (Observation 3, 5), both the `app` container (FastAPI) and the `sync-worker` container must access the exact same SQLite database.
4. **Volume Mounting Options**: If deployed as separate pods, they require `ReadWriteMany` (RWX) volume claims which are unsupported by default on standard RWO block storage (like EBS or microk8s hostpath). To resolve this cleanly without complex infrastructure, they should be deployed as multiple containers (FastAPI + `sync-worker` sidecar) inside the *same* Pod (Observation 5). They can then share a standard ReadWriteOnce (RWO) or ephemeral volume locally.
5. **CORS native resolution**: Since the frontend SPA makes client-side calls to the backend, using Ingress path-based routing (`/api/` and `/ws/` to backend, `/` to frontend) resolves CORS issues out of the box without requiring manual header tweaking.

## 3. Caveats
- This investigation is read-only. No resources were deployed.
- It is assumed that the Kubernetes cluster has an Ingress controller (like `ingress-nginx`) configured.
- If scaling FastAPI backend pods, each replica pod will have its own independent SQLite database file and local sync-worker. This works perfectly under the Outbox pattern as long as they all sync to the same central PostgreSQL database.

## 4. Conclusion
The proposed Helm chart design under `deploy/k8s/` orchestrates:
1. **Backend & Sync Worker**: Co-located in the same Pod as sidecars to utilize standard `ReadWriteOnce` storage for SQLite persistence.
2. **Celery Worker**: Replicas reading from Redis, performing resource-intensive operations, with config mapping.
3. **Redis & Postgres**: Internal services initialized with `init.sql` schema mounted via ConfigMap.
4. **Next.js Frontend**: ClusterIP deployment serving built static assets.
5. **Ingress Resource**: Unifies frontend and backend access under a single domain, native-solving CORS.

The detailed templates are fully written to `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_k8s_2\analysis.md`.

## 5. Verification Method
1. Inspect `deploy/k8s/values.yaml` and `templates/` files structure once generated.
2. Run the Helm lint command from the root directory to verify syntax compliance:
   ```bash
   helm lint deploy/k8s/
   ```
3. Test template rendering using dry-run:
   ```bash
   helm template jobhunt-pro deploy/k8s/ --debug
   ```
