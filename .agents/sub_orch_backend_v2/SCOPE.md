# Scope: Backend AI Enhancement and JWT Security Hardening

## Architecture
- **API Entrypoint**: FastAPI server in `backend/main.py` serving endpoints under `/api/v1/*`.
- **Security Middleware/Dependencies**: A new module `backend/auth.py` providing JWT verification and a FastAPI Dependency to intercept and authenticate requests, validating a Bearer token.
- **AI Inference Engine**: `backend/ai_engine.py` integrating with `AsyncGroq` using the Groq API.
- **Streaming Flow**: Convert cover letter generation endpoint to return an `EventSource` (Server-Sent Events) streaming chunks of the letter using Groq LPU streaming capabilities in real-time, supporting advanced context such as tone matching.

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID | Working Directory |
|---|---|---|---|---|---|---|
| 1 | Exploration & Analysis | Inspect `backend/main.py`, `backend/ai_engine.py`, existing tests. Design JWT schema and non-blocking EventStream response details. | None | DONE | 48ef0d3d-0da0-4845-bd97-1a81ccade002 | .agents/explorer_backend_v2 |
| 2 | Implementation of JWT Authentication & Streaming AI | Add JWT validation dependency in `backend/auth.py` and enforce on `/api/v1/*`. Update `backend/ai_engine.py` to stream Groq completions with advanced context (tone, etc.). | M1 | PLANNED | TBD | .agents/worker_backend_v2 |
| 3 | Verification & Auditing | Run Reviewer, Challenger, and Forensic Auditor to verify JWT protection (returns 401 on failure, 200 on success) and streaming Cover Letters. | M2 | PLANNED | TBD | .agents/review_backend_v2 |

## Interface Contracts
### Client ↔ FastAPI Authentication
- **Secure Endpoints**: Any `/api/v1/*` endpoint (e.g., `/api/v1/scrape`, `/api/v1/generate-cover-letter`, `/api/v1/accounts`) requires `Authorization: Bearer <JWT_TOKEN>` header.
- **Failure Response**: Returns HTTP 401 Unauthorized if Bearer token is missing, expired, or signature is invalid:
  - Format: `{"detail": "Could not validate credentials"}` or similar standard FastAPI HTTP exception.
- **Exemptions**: Root `/` and `/health` do not require authentication.
- **Token Generation**: For testing/integration, a hardcoded/standard secret `JWT_SECRET` is used (e.g. from env, or a fallback secret `super-secret-key`) to sign/verify tokens.

### Client ↔ Groq Streaming Cover Letter
- **Endpoint**: `POST /api/v1/generate-cover-letter` (or similar) returning `text/event-stream` format.
- **Request Body**:
  ```json
  {
    "user_cv": "text description of CV",
    "job_description": "text description of job description",
    "tone": "professional" // Optional parameter for tone matching
  }
  ```
- **Stream Format**: Standard SSE event stream with data chunks. Each chunk contains a delta of the generated cover letter text.
