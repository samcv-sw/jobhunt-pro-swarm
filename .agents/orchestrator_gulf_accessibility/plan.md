# Master Plan: JobHunt Pro Gulf Accessibility & Optimization

## Architecture & Scope
- Backend: FastAPI, Neon DB (PostgreSQL) with local SQLite fallback, JWT-based auth, dynamic CORS regex verification, API rate limits.
- Frontend: Next.js App Router (Next 15 / React 19) in `frontend/` using Tailwind CSS, supporting LTR/RTL bilingual flows.
- Testing: Comprehensive test suite of 611+ unit & E2E tests inside `tests/` directory.

## Milestones

### Milestone 1: Code Auditing and Exploration
- **Objective**: Audit the codebase for current database pooling config, JWT secrets configuration, CORS middleware, rate limiters, frontend styling/components, and test layout.
- **Worker**: Explorer subagent
- **Success Criteria**: A comprehensive report outlining file targets, existing issues, and implementation recommendations.

### Milestone 2: Frontend UI/UX Hardening
- **Objective**: Refactor frontend layouts, styles, and templates to be 100% compliant with logical properties, Gulf typography guidelines, and dynamic icon flipping.
- **Worker**: Worker subagent
- **Reviewer**: Reviewer subagent (runs visual check / lints)
- **Success Criteria**: 0 physical CSS directional properties, Cairo/Tajawal font stacks, min font size 14px, no letter-spacing in Arabic, and dynamic directional icons. Next.js builds successfully.

### Milestone 3: Backend Database and Security Optimization
- **Objective**: Optimize database connections (Neon PgBouncer pooling + SQLite fallback), implement secure JWT auth, robust rate limiting, and strict regex CORS origin checks.
- **Worker**: Worker subagent
- **Reviewer**: Reviewer subagent
- **Success Criteria**: Backend API routes functional, passing security unit tests, connection pooling working without leaks.

### Milestone 4: Verification and E2E Testing
- **Objective**: Run the full test suite and frontend builds to ensure all 611+ tests pass with zero regressions and no console errors.
- **Worker**: Challenger and Reviewer subagents
- **Auditor**: Forensic Auditor subagent (performs integrity verification)
- **Success Criteria**: 100% test pass rate (611+ tests), clean build logs, clean Forensic Auditor verdict.
