# Fix Flask Stack Quality and Security Issues (Milestone 3)

## Task Description
Implement the following fixes to resolve unit/integration test failures and security issues:

1. **`web/app.py`**:
   - Comment out or remove line 32: `from core.database import Database` to resolve the cascading import error.

2. **`core/pa_job_scraper.py`**:
   - In `search_linkedin_xhr`, replace the direct `httpx_Session(...)` network call (around line 1021) with a call to the standard Cloudflare routing helper:
     ```python
                     html_text = self._fetch_url(url)
     ```

3. **`core/aegis_shield.py`**:
   - Change line 285 to return `"Access Denied (Blackholed)."` to match WAF blocking test assertions:
     ```python
                     return PlainTextResponse("Access Denied (Blackholed).", status_code=403)
     ```

4. **`tests/test_tenant_smtp.py`**:
   - Create the `orders` table in the `init_db()` method (around line 65) to prevent operational missing table errors:
     ```python
             conn.execute("""
                 CREATE TABLE IF NOT EXISTS orders (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     order_id TEXT UNIQUE NOT NULL,
                     user_id TEXT NOT NULL,
                     order_type TEXT NOT NULL,
                     package_name TEXT,
                     company_count INTEGER,
                     amount_usd REAL NOT NULL,
                     payment_status TEXT DEFAULT 'pending',
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )
             """)
     ```

5. **`core/campaign_runner.py`**:
   - Update the traceback file open at line 900 to use UTF-8 encoding:
     ```python
             with open("campaign_error.txt", "w", encoding="utf-8") as f:
     ```

6. **`web/app_v2.py`**:
   - Restrict uploaded CV file formats at line 4912 to PDF, DOC/DOCX, TXT, and RTF by raising an HTTPException for other formats:
     ```python
                 else:
                     raise HTTPException(
                         status_code=400,
                         detail="Unsupported file format. Only PDF, Word (.doc, .docx), Text (.txt), and RTF (.rtf) files are allowed."
                     )
     ```

7. **Verify Tests**:
   - Run `python -m pytest tests/` with `PYTHONPATH=.`. All tests should pass.

## Scope Boundaries
- Do not modify other files or unrelated methods.
- Focus strictly on these changes.

## Expected Output
- Detailed handoff report in `handoff.md` with verification test logs.
