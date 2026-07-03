# Scope: Kubernetes Deployment

## Architecture
- Orchestrates Next.js frontend, FastAPI backend, Celery Workers, Redis, Postgres, and SQLite OPFS volume claims.
- Target path: `deploy/k8s/`
- Tool check: `helm lint deploy/k8s/`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Create Helm Chart | Define deployment, service, ingress, volume templates for the stack under `deploy/k8s/` | none | PLANNED |
| 2 | Lint Chart | Run helm lint checks on the generated chart | 1 | PLANNED |
