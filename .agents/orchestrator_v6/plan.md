# Plan: JobHunt Pro System Optimization

## Mission
Comprehensive optimization of the JobHunt Pro system. This includes a premium UI/UX redesign, backend code refactoring for performance and security, and enhancements to the AI ATS matching and scraping engines. All work must meet acceptance criteria in development integrity mode.

---

## Plan Topology & Milestones

### Phase 1: Codebase Exploration & Audit (Iteration 1)
- **Objective**: Run existing test suites, identify current bugs, audit backend files and UI/UX template/Next.js setup.
- **Agent**: `teamwork_preview_explorer`
- **Output**: Detailed audit report (`exploration_report.md`) detailing current test pass/fail status, scraper mechanics, and UI routes/files.

### Phase 2: Backend Optimization & AI/Scraper Enhancements (Iteration 2)
- **Objective**: Refactor the Python backend for performance (DB query consolidation, connection pooling) and security (input sanitization, CSRF, JWT security). Enhance AI ATS matcher accuracy, speed, and stealth scraper capabilities to bypass anti-bot, returning structured data and storing jobs without crashing.
- **Agent**: `teamwork_preview_worker`
- **Verification**: Run backend and scraper tests, execute a mock scraper run to check DB storage.

### Phase 3: Frontend UI/UX Redesign & RTL Polish (Iteration 3)
- **Objective**: Overhaul Next.js/HTML frontend to be highly premium, dynamic, glassmorphic, and mobile-responsive with Arabic RTL support (Cairo/Tajawal fonts, logical properties).
- **Agent**: `teamwork_preview_worker`
- **Verification**: Frontend build verification (`npm run build`), CSS property audit (no physical properties), manual local web app check.

### Phase 4: Full System Verification & Adversarial Testing (Iteration 4)
- **Objective**: Execute complete test suite (`tests/e2e/` and unit tests) using Reviewer/Challenger. Run Forensic Auditor to guarantee zero integrity violations.
- **Agents**: `teamwork_preview_reviewer`, `teamwork_preview_challenger`, `teamwork_preview_auditor`
- **Gate**: 100% test pass, Clean audit verdict, Premium UI validation.

---

## Detailed Execution Steps & Verification Methods

### Step 1: Initial System Audit
- **Action**: Explorer runs `pytest` and checks current status of Next.js app compilation.
- **Success Criteria**: Log of existing failures/warnings, list of files requiring optimization.

### Step 2: Backend & AI Refactoring
- **Action**: Worker applies optimization to SQLite queries, adds HTTP connection pooling, improves async concurrency, fixes `ats_matcher.py` / `ai_tailor.py` for speed & accuracy, upgrades `scrapers/stealth_ingest.py` bypass mechanisms.
- **Success Criteria**: Automated tests for backend and scrapers pass, scraper stores jobs successfully.

### Step 3: Frontend Modernization
- **Action**: Worker upgrades dashboard UI in `frontend/src/app/` to use a glassmorphism style, ensuring complete RTL CSS compliance.
- **Success Criteria**: `npm run build` succeeds, search for physical CSS properties (`margin-left`, etc.) returns 0 matches in `frontend/src/`.

### Step 4: Verification Loop
- **Action**: Reviewers verify correctness. Challenger runs performance and concurrency benchmarks. Auditor performs integrity validation.
- **Success Criteria**: All tests pass, 0 lints, audit verification is CLEAN.
