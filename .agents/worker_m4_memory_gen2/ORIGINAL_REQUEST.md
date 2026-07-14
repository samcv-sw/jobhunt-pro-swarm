## 2026-07-11T08:00:15Z

You are teamwork_preview_worker.
Your role is to implement the memory reclamation and OOM prevention changes for Milestone 4, and verify that they pass all tests and run without errors.

Your identity:
- Archetype: teamwork_preview_worker
- Role: Milestone 4 Worker (Replacement)
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m4_memory_gen2

Requirements:
- Enforce strict compliance with c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\AGENTS.md guidelines.
- Apply the proposed modifications from the Explorer's report (`c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m4_memory\handoff.md`):
  1. In `backend/celery_app.py`: Tune GC threshold using `gc.set_threshold(50, 5, 5)` at module load time. Configure `worker_max_tasks_per_child=10` and `worker_max_memory_per_child=150000` (150MB in KB) in Celery app settings.
  2. In `backend/main.py`: Tune GC threshold using `gc.set_threshold(50, 5, 5)` at module load time.
  3. In `backend/sync_worker.py`: Tune GC threshold using `gc.set_threshold(50, 5, 5)` at module load time. Call `gc.collect()` explicitly inside the loop iteration.
  4. In `start_cloud.py`: Replace the file with the proposed self-healing process supervisor that launches Uvicorn, Celery, and Sync Worker. It must:
     - Apply GC tuning `gc.set_threshold(50, 5, 5)`.
     - Configure Celery with prefork pool (`-c 1` on Linux, `-P solo` on Windows).
     - Run a background thread to check process RSS via `psutil` (if available) with limits: Celery=180MB, Sync Worker=80MB, Uvicorn=220MB. If exceeded, terminates the service.
     - If total RSS footprint exceeds 450MB, terminates the largest consumer.
     - Auto-restarts any terminated process.
     - Integrates the daemon health-ping thread.
- Execute the test suite using `pytest` to confirm that these modifications do not introduce any syntax errors or regressions.
- Perform a dry run of the startup script using `python start_cloud.py` or similar verification method to verify that all processes launch, run, and are monitored correctly.
- Write your handoff.md detailing what was implemented and the verification results.
- Update your progress.md inside your folder.
- When done, send a message back to parent (ID: fa9b20fb-0399-49b4-abb8-cb3e569a72a4) claiming completion.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
