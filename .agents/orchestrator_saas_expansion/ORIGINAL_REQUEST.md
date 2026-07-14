# Original User Request

## Initial Request — 2026-07-12T23:48:56Z

Migrate, optimize, and expand the JobHunt Pro platform into a zero-cost, highly resilient, and commercially scalable multi-tenant SaaS. Bypasses Render's free tier limits, resolves all 20 remaining pending TODOs, adds advanced AI/UI enhancements, and introduces enterprise SaaS features.

### Requirements

#### R1. Complete execution of all 20 remaining pending TODOs from IMPROVEMENTS_MASTER.md
Resolve each of the 20 pending TODOs below:
1. **IMP-034**: N+1 query elimination audit (Add selectinload/joinedload where queries loop).
2. **IMP-037**: Next.js bundle analysis (@next/bundle-analyzer to find large chunks).
3. **IMP-038**: Next.js ISR for static job pages (getStaticProps + revalidate:300 for job listing pages).
4. **IMP-039**: Celery task group/chord for bulk email (celery.group() for parallel batch email dispatch).
5. **IMP-095**: Email dispatch E2E tests (aiosmtpd mock SMTP to test send_application_email Celery task).
6. **IMP-097**: Telegram bot command tests (Unit test each bot command handler in isolation).
7. **IMP-099**: Locust load tests (100 concurrent users on /api/v1/jobs/scrape).
8. **IMP-100**: Mutation testing with mutmut (mutmut run on core/scam_detector.py to find weak assertions).
9. **IMP-101**: Frontend snapshot tests (Jest toMatchSnapshot() for key React components).
10. **IMP-102**: API contract tests via Schemathesis (schemathesis run against OpenAPI spec in CI).
11. **IMP-128**: Multi-region DNS failover (Cloudflare health-check-based DNS failover).
12. **IMP-154**: Dead code removal via vulture (vulture . --min-confidence 80).
13. **IMP-158**: Large function decomposition (Decompose functions >100 lines in core/).
14. **IMP-160**: Import sorting with isort (isort . --profile black).
15. **IMP-162**: Dependency version pinning (pip freeze to exact versions in requirements.txt).
16. **IMP-183**: Arabic NLP job matching (AraBERT embeddings for Arabic job-CV similarity).
17. **IMP-187**: User onboarding wizard (Multi-step: upload CV → preferences → email pool → test run).
18. **IMP-190**: LinkedIn OAuth login (LinkedIn OAuth2 via authlib; auto-import profile to CV).
19. **IMP-243**: Streaming cover letter preview (Word-by-word streaming preview in frontend dashboard).
20. **IMP-247**: CV PDF parsing accuracy (Switch from pdfminer to pdfplumber for multi-column CVs).

#### R2. Auto-Fill Browser Agent
Create `core/form_autofill.py`:
- Function `autofill_job_form(url: str, user_profile: dict)` using Playwright.
- Navigates to the job application URL.
- Detects form fields (name, email, phone, cover letter textarea).
- Fills them with user_profile data.
- Clicks submit button.
- Returns `{success: bool, screenshot_path: str}`.

### Acceptance Criteria

#### Task Completion
- [ ] All 20 remaining TODOs in `IMPROVEMENTS_MASTER.md` are completed and marked as done.
- [ ] Auto-fill browser agent `core/form_autofill.py` is implemented and functional.
- [ ] No regressions: all existing test suites pass with zero failures (`pytest tests/ -q`).
