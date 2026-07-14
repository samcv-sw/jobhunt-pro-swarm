# BRIEFING — 2026-07-11T12:13:00+03:00

## Mission
Implement Milestone 1: Multi-Key JWT Secret Rotation.

## 🔒 My Identity
- Archetype: teamwork_preview_worker
- Roles: implementer, qa, specialist
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_m1_1
- Original parent: 6ecf45d6-6d9d-4904-a199-48bb6826dede
- Milestone: Milestone 1

## 🔒 Key Constraints
- CODE_ONLY network mode: no external requests, no external curls/wgets.
- Logical Properties must be used (not directly relevant for backend JWT implementation but good to remember).
- Do not cheat, no dummy implementations.

## Current Parent
- Conversation ID: 6ecf45d6-6d9d-4904-a199-48bb6826dede
- Updated: not yet

## Task Summary
- **What to build**: Multi-Key JWT secret rotation functionality in backend/auth.py, backend/main.py, and web/app_v2.py, plus test_jwt_rotation.py unit tests.
- **Success criteria**: All JWT decoding processes support multiple secret keys (e.g. JWT_SECRET_KEYS or JWT_SECRET_KEY, fallback keys). Signature checks check all keys. If expired, raise ExpiredSignatureError immediately. All 430+ unit tests pass.
- **Interface contracts**: backend/auth.py, backend/main.py, web/app_v2.py
- **Code layout**: Source in backend/ and web/, tests in tests/

## Key Decisions Made
- None yet.

## Artifact Index
- None yet.

## Change Tracker
- **Files modified**: None
- **Build status**: Unknown
- **Pending issues**: None

## Quality Status
- **Build/test result**: Unknown
- **Lint status**: Unknown
- **Tests added/modified**: None

## Loaded Skills
- None
