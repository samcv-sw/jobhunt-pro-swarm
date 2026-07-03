## 2026-07-03T10:34:16Z
You are Worker (teamwork_preview_worker).
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m2
Your objective is to implement the scraper stealth hardening improvements (R3).

Tasks:
1. Enhance `scrapers/stealth_ingest.py` by incorporating the proposed improvements from `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m1_3\proposed_stealth_ingest.py`. Ensure:
   - Aligned browser profiles (synchronizing TLS target fingerprint and HTTP headers).
   - Session-pinned proxy rotation (supporting backconnect/dynamic sessions and static lists).
   - Organic warmup steps (fetching root domain or `/robots.txt` before target URL fetches in the same session).
   - Concurrency control using `asyncio.Semaphore` (e.g. limit to 3) and random delay (jitter) between hits.
2. Integrate the test verification script `verify_bot.py` or write test code to execute verification targeting `https://bot.sannysoft.com/`. Run tests to verify the changes.
3. Verify that all celery background tasks (`scrape_jobs` in `backend/tasks.py`) still work correctly after these changes. Run test code to prove this.

MANDATORY INTEGRITY WARNING — DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your report to c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m2\handoff.md following the Handoff Protocol. Include compilation/test command details and layout compliance in your handoff report.
When done, notify your parent by calling send_message with your handoff details and path.
