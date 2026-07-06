# Plan: Security Verification & Hardening

## Overview
This plan coordinates worker, reviewer, challenger, and auditor subagents to verify and harden the application's security controls, ensuring all requirements in `SCOPE.md` are correctly implemented, robustly tested, and fully compliant.

## Verification Steps
1. **Worker Implementation & Verification (`worker_security_v5_gen3`)**:
   - Audit `backend/main.py` and `web/app_v2.py` for all 5 security requirements:
     1. WebSocket auth in `/ws/war-room`.
     2. Protect all unauthenticated `/api/v1/*` endpoints (`/api/v1/daily-login`, `/api/v1/login-streak`, `/api/v1/ats-score`, `/api/v1/ats-score-bulk`, `/api/v1/roast`, `/api/nodriver-feed`).
     3. Fix `NameError` crash in `/api/v1/roast`.
     4. SSRF redirect bypass validation in `/api/v1/fetch-url`.
     5. FastAPI rate-limiting in `backend/main.py`.
   - Run the existing security test suite (`pytest`) and verify everything passes.
   - Deliver a handoff.md report with passing test logs.

2. **Reviewer Audit (`reviewer_security_v5_gen3`)**:
   - Inspect the code changes made by the worker.
   - Verify code quality, logical properties conformance, and security standards.
   - Confirm all endpoints have proper verification and rate limits.

3. **Challenger Adversarial Testing (`challenger_security_v5_gen3`)**:
   - Build a custom test harness/stress-test or adversarial scripts to verify that:
     - Invalid/missing JWTs are blocked.
     - WebSocket subprotocol or query parameter bypasses are handled.
     - Redirection chains to internal IPs are blocked (SSRF).
     - Volumetric rate limits trigger HTTP 429 correctly.
   - Run the adversarial tests and report results.

4. **Auditor Integrity Check (`auditor_security_v5_gen3`)**:
   - Perform static analysis, runtime verification, and integrity checks.
   - Ensure zero cheating or hardcoded bypasses exist.
   - Deliver a clean audit report.

5. **Milestone Completion & Synthesis**:
   - Synthesize results from all agents.
   - Generate `handoff.md` and report back to the parent.
