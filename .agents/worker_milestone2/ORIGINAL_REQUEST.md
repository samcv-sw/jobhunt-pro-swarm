## 2026-07-03T20:34:43Z

Your role is teamwork_preview_worker for Milestone 2. Your working directory is c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_milestone2\.
Your task is to implement the backend optimizations (R2) and AI/Scraper enhancements (R3) based on the findings of Explorer 2 and Explorer 3.

Please address the following changes:
1. Syntax / Indentation Fix:
   - Fix the IndentationError in core/telegram/bot.py around lines 20-25 so that the import statement is properly indented.
2. Security Hardening:
   - Update the CSRF middleware in web/app_v2.py (around lines 826-860). Ensure that if 'ok' is False, the middleware immediately intercepts the request and returns a Response("CSRF validation failed", status_code=403) instead of letting it pass through.
   - Update backend/auth.py to remove the default fallback string for JWT_SECRET_KEY, so that it raises an error or fails if the 'JWT_SECRET_KEY' environment variable is not defined in a production context.
3. AI Module Performance & Accuracy:
   - Refactor core/ats_matcher.py to:
     - Filter n-grams using a standardized taxonomy of tech keywords.
     - Implement synonym mapping (e.g. 'K8s' to 'Kubernetes', 'AWS' to 'Amazon Web Services').
     - Optimize the matching loops using length checks or initial letter hashes before performing edit distance.
     - Replace static boosts with dynamic IDF-based weighting.
   - Refactor core/ai_tailor.py to perform a fast TF-IDF cosine-similarity subset filter on resume highlight bullets before sending prompts to the LLM to minimize token count and improve speed.
4. Scraper Stealth & Extraction:
   - Enhance scrapers/stealth_ingest.py to:
     - Parse JSON-LD structured data from `<script type="application/ld+json">` tags to extract job lists reliably.
     - Add a generative LLM fallback parser that cleans raw HTML and formats it into structured JSON lists.
     - Ensure the scraper always returns a clean `list[dict]` with at least 'title' and 'url' keys.
5. Verification:
   - Run the full suite of unit and integration tests (tests/test_ats_matcher.py, tests/test_ats_scorer.py, tests/test_anti_ban.py, tests/test_concurrency.py, tests/test_pa_job_scraper.py, tests/e2e/test_r3_scraper.py, etc.) using the global python interpreter to ensure they all pass.
   - Write your implementation details, files modified, and test outputs to handoff.md in your working directory. Notify the parent orchestrator via send_message when complete.

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT
> hardcode test results, create dummy/facade implementations, or
> circumvent the intended task. A Forensic Auditor will independently
> verify your work. Integrity violations WILL be detected and your
> work WILL be rejected.
