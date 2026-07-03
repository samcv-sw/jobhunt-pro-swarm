# Plan: Scraper Optimization

## Steps
1. **Initialization**:
   - Initialize coordination files (`ORIGINAL_REQUEST.md`, `BRIEFING.md`, `progress.md`, `plan.md`).
   - Start 10-minute heartbeat cron.
2. **Exploration**:
   - Spawn 3 Explorers (`teamwork_preview_explorer`) to analyze `scrapers/stealth_ingest.py` and `tests/e2e/test_r3_scraper.py`.
   - Recommend upgrades to bypass anti-bot protections and return structured `list[dict]` with `title` and `url`.
3. **Exploration Synthesis**:
   - Aggregate findings from the Explorers.
4. **Implementation**:
   - Spawn a Worker (`teamwork_preview_worker`) to apply the upgrade to `scrapers/stealth_ingest.py`.
   - Verify that requirements are met (correct bypass, correct structured parsing, pytest verification passes).
5. **Review**:
   - Spawn 2 Reviewers (`teamwork_preview_reviewer`) to independently review the code changes and test executions.
6. **Empirical Challenge**:
   - Spawn 2 Challengers (`teamwork_preview_challenger`) to independently run tests and stress-test the implementation.
7. **Forensic Audit**:
   - Spawn a Forensic Auditor (`teamwork_preview_auditor`) in benchmark integrity mode.
8. **Finalization & Synthesis**:
   - Verify all gate criteria are met.
   - Update `SCOPE.md` milestones to done.
   - Write `handoff.md` and send completion message to the parent agent.
