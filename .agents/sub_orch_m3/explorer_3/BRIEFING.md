# BRIEFING — 2026-07-12T20:55:20Z

## Mission
Investigate and design the implementation strategy for IMP-187 (User onboarding wizard) and IMP-243 (Streaming cover letter preview in frontend dashboard).

## 🔒 My Identity
- Archetype: Explorer
- Roles: Read-only investigator
- Working directory: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m3\explorer_3
- Original parent: 868ca858-dfcb-4c6b-90bd-814bc039a80e
- Milestone: IMP-187 & IMP-243 Design

## 🔒 Key Constraints
- Read-only investigation — do NOT implement / do NOT modify any code files yourself.
- Write findings to: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m3\explorer_3\analysis.md

## Current Parent
- Conversation ID: 868ca858-dfcb-4c6b-90bd-814bc039a80e
- Updated: 2026-07-12T20:55:20Z

## Investigation State
- **Explored paths**: `backend/main.py`, `backend/models.py`, `backend/email_engine.py`, `core/byo_smtp.py`, `core/multi_tenant.py`, `web/frontend_api.py`, `frontend/src/app/page.tsx`, `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/db/wasm-db.ts`
- **Key findings**:
  - Found `/api/v1/ai/generate-cover-letter/stream` POST endpoint protected by JWT, which requires a custom React stream reader.
  - Mapped onboarding steps (CV upload -> client-side parsing/wasm storage; preferences -> local storage + Wasm DB; email pool -> test SMTP connection and encrypt via ROT13; test run -> stream preview + self-test email).
  - Detected database model discrepancy where `User` in `backend/models.py` lacks SMTP configuration columns needed by `core/multi_tenant.py`.
- **Unexplored areas**: None.

## Key Decisions Made
- Exclude standard HTML5 `EventSource` in favor of a native `fetch` stream reader due to JWT authentication on `POST` requests.
- Propose adding `byo_smtp_email` and `byo_smtp_token` columns to the backend database SQLAlchemy schema.

## Artifact Index
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m3\explorer_3\analysis.md — Detailed analysis report
- C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\sub_orch_m3\explorer_3\handoff.md — Handoff report
