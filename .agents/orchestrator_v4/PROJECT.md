# Project: JobHunt Pro Enterprise Scaling

## Architecture
- **Backend (FastAPI)**: Serves the REST API endpoints, AI engine, and billing services.
  - `backend/ai_engine.py`: Incorporates the vector database (Chroma/Qdrant) for RAG context extraction.
  - `backend/billing.py`: Interfaces with the Stripe API to manage payments, checkouts, and subscription tiers.
- **Mobile (React Native/Expo)**: Cross-platform frontend app located in `mobile/` that connects to the FastAPI backend API endpoints. Respects AGENTS.md rules for typography (Cairo/Tajawal), RTL logical properties, and form inputs.
- **Deployment (Kubernetes/Helm)**: Orchestrates Next.js frontend, FastAPI backend, Celery Workers, Redis, Postgres, and SQLite OPFS volume claims. Standardized inside `deploy/k8s/` as a Helm chart.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Kubernetes Deployment | Helm chart under `deploy/k8s/` (Conv ID: bb20b5b1-9c5c-412c-9da2-4c162a845a3b) | none | IN_PROGRESS |
| 2 | Vector DB (RAG) | RAG backend integration in `backend/ai_engine.py` (Conv ID: c4e4ddf0-be49-4898-928d-66a9918ca89c) | none | IN_PROGRESS |
| 3 | Mobile App | React Native (Expo) app under `mobile/` (Conv ID: 8ab2f959-ac0e-4a54-8907-d96a63bf150e) | none | IN_PROGRESS |
| 4 | Stripe Billing | Stripe integration under `backend/billing.py` (Conv ID: 3f260753-c648-4e9a-8d25-1bd7e90b2de0) | none | IN_PROGRESS |
| 5 | E2E Verification & Audit | E2E tests, validation, and Forensic Audit check. | M1, M2, M3, M4 | PLANNED |

## Interface Contracts
### AI Engine (RAG) Interface
- `insert_cover_letter(text: str, metadata: dict)`: Inserts a cover letter text and metadata into the local vector store.
- `retrieve_relevant_letters(query: str, limit: int = 3) -> list`: Queries the vector store for semantically similar cover letters/styles.
- `generate_smart_cover_letter_with_rag(job_description: str, user_cv: str, tone: str) -> str`: Enhances the cover letter generation using vector DB context.

### Billing Interface
- `/api/v1/checkout` (POST): Accepts price/tier requests, returns `{ "checkout_url": str }`.
- `/api/v1/webhook/stripe` (POST): Receives Stripe event webhooks to handle subscription updates and activations.
- `check_user_limits(user_id: str, action: str) -> bool`: Checks if user tier limits allow the action.

### Mobile Frontend Interface
- Target API: HTTP backend endpoints (FastAPI dashboard/auth routes).
- UI Requirements: Arabic/English toggling, Cairo/Tajawal font family (min 16px, line-height 1.8), CSS logical properties for layout.
