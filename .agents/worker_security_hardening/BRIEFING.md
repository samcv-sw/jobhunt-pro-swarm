# BRIEFING — 2026-07-14T11:40:26+03:00

## Mission
Implement security and performance improvements in backend/auth.py and backend/main.py as per the code review findings, ensuring all tests and integrity checks pass.

## 🔒 My Identity
- Archetype: worker_security_hardening
- Roles: implementer, qa, specialist
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_security_hardening
- Original parent: 1c546bb5-417c-4607-b08a-0b1e19a69db5
- Milestone: Security and Performance Hardening

## 🔒 Key Constraints
- Code modifications must follow the minimal change principle.
- No dummy/facade implementations or hardcoded test results.
- All dictionary read/write operations on _rate_state must be protected by the existing _rate_lock.
- Restrict default TRUSTED_PROXIES to "127.0.0.1".
- Expired signatures or missing credentials should not trigger IP rate limit lockouts in JWT verification.
- CORS regex patterns must be pre-compiled.

## Current Parent
- Conversation ID: 1c546bb5-417c-4607-b08a-0b1e19a69db5
- Updated: 2026-07-14T11:40:26+03:00

## Task Summary
- **What to build**: Rate limit optimization (lazy/throttled cleanup), restrictive default TRUSTED_PROXIES, remove lockout from API JWT verification (while retaining checks), pre-compile CORS regex in SecureCORSMiddleware.
- **Success criteria**: All tests (including `tests/test_hardening_v2.py`) pass, `verify_integrity.py` passes, Next.js frontend builds successfully.
- **Interface contracts**: backend/auth.py and backend/main.py
- **Code layout**: Existing codebase layout (backend/auth.py, backend/main.py)

## Key Decisions Made
- [TBD]

## Artifact Index
- c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_security_hardening\ORIGINAL_REQUEST.md — Original task description
