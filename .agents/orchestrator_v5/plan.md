# Execution Plan — JobHunt Pro Maximum Overdrive Optimization

## Objectives
1. **R1. Frontend UI/UX & RTL Polish**: Audit the Next.js frontend to ensure CSS Logical Properties are strictly used and build is successful.
2. **R2. Backend Concurrency & Database Sync**: Optimize event loop blocking (under 50ms) and add connection error resilience in `sync_worker.py`.
3. **R3. Scraper Stealth Hardening**: Ensure `stealth_ingest.py` scraper bypasses anti-bot and returns structured `list[dict]` of job details.
4. **R4. Security Hardening**: Guarantee JWT Bearer authorization protects all `/api/v1/*` endpoints.
5. **R5. E2E Test Suite Validation**: Validate the entire stack with `pytest tests/e2e/` passing 100%.

## Verification Gates
1. **Static Audits**: Search for physical directional properties in `frontend/src/` to confirm 0 matches.
2. **Build Audits**: Run Next.js build inside `frontend/` (`npm run build`).
3. **Behavioral Verification**: Run `pytest tests/e2e/` ensuring all E2E test scripts pass.
4. **Forensic Integrity Verification**: Run forensic auditing (`teamwork_preview_auditor`) on all implemented changes.

## Phase 1: Exploration & Diagnostics
- [ ] Task 1.1: Spawn `teamwork_preview_explorer` to inspect current code, run tests, and outline specific code modifications.
- [ ] Task 1.2: Synthesize findings and update the plan with concrete milestones.

## Phase 2: Implementation & Iteration
- [ ] Task 2.1: Spawn `teamwork_preview_worker` to implement fixes for R1, R2, R3, and R4.
- [ ] Task 2.2: Verify changes via build and test commands run by the worker.

## Phase 3: Review & Validation
- [ ] Task 3.1: Spawn `teamwork_preview_reviewer` to review code modifications.
- [ ] Task 3.2: Spawn `teamwork_preview_challenger` to stress-test concurrency and scraper resilience.

## Phase 4: Forensic Audit & Wrap-up
- [ ] Task 4.1: Run `teamwork_preview_auditor` to audit integrity.
- [ ] Task 4.2: Deliver final report to Sentinel.
