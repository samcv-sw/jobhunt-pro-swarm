# Fix Database Shim Imports and Verify Tests (Milestone 1 Core Fix)

## Task Description
1. Edit `core/pg_sqlite_shim.py` to add standard PEP 249 database module constants and exception exports:
   ```python
   apilevel = "2.0"
   threadsafety = 1
   paramstyle = "qmark"
   Warning = real_sqlite3.Warning
   DataError = real_sqlite3.DataError
   ```
2. Once modified, verify the PEP 249 compatibility.
3. Run the pytest suites to see if they collect and run correctly:
   - Command: `python -m pytest tests/` with environment variable `PYTHONPATH` set to `.`
   - Command: `python -m pytest tests/e2e/` with environment variable `PYTHONPATH` set to `.`
4. Document the test results, including any passing or failing test cases.
5. Verify the Next.js frontend build command:
   - Command: `node node_modules\next\dist\bin\next build` inside the `frontend/` directory.

## Scope Boundaries
- Do not make any other changes to the python files or next.js files.
- Focus only on the `core/pg_sqlite_shim.py` changes and test/build verification.

## Expected Output
- A detailed handoff report in `handoff.md` with the verbatim command outputs and test/build verification status.
