## 2026-07-16T17:23:17Z
You are a teamwork_preview_explorer subagent.
Your identity is: teamwork_preview_explorer_m1_3
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_3
Your parent conversation ID is: 78a73b8e-5c44-4f6a-821d-6c013b3e5512

Task:
1. Read the PROJECT.md and plan.md in c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_orchestrator_deep_opt\
2. Analyze backend routers and main entry point (`backend/main.py`, `web/app_v2.py`, `web/routers/*.py`) for compatibility issues with PythonAnywhere's restricted environment (socket/thread limits, outbound proxies).
3. Investigate the speed of core endpoints (e.g., dashboard stats `/api/v1/dashboard/stats`, DLQ endpoint `/api/v1/admin/dlq/requeue`) to identify possible timeout risks.
4. Inspect the auth rate limits (Aegis/Banshield) and scraper anti-ban headers.
5. Execute the test suite using `uv run pytest` to obtain the baseline test status (which tests pass, fail, or are skipped).
6. Create an audit report detailing findings and optimization steps.
7. Save your report as analysis.md in your working directory.
8. Write handoff.md in your working directory and notify the parent.
