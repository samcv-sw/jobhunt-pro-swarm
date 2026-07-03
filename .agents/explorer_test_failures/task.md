# Audit Test Failures (Milestone 1 Test Audit)

## Task Description
Run pytest and identify the specific failures in both `tests/` and `tests/e2e/`:
1. Run `python -m pytest tests/` with `PYTHONPATH=.` and capture the failure tracebacks and names of failed tests.
2. Run `python -m pytest tests/e2e/` with `PYTHONPATH=.` and capture the failure tracebacks and names of failed tests.
3. Investigate the cause of each failure (e.g. why is `chrome120` in `STEALTH_PROFILES` failing, why is `dir="auto"` failing, or any schema issues).
4. List the exact filenames, test function names, reasons for failure, and recommended fixes for each failure.

## Scope Boundaries
- Do NOT modify any source files.
- Focus on producing a clear audit report of the test failures.

## Expected Output
- A detailed handoff report in `handoff.md` summarizing the test failures and how to fix them.
