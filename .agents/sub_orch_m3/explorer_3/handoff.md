# Handoff Report: IMP-187 and IMP-243 Strategy Investigation

## 1. Observation
- **Streaming Endpoint Location**: In `backend/main.py` lines 806-816:
  ```python
  @app.post("/api/v1/ai/generate-cover-letter/stream", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
  async def stream_cover_letter(req: CoverLetterRequest, request: Request = None) -> StreamingResponse:
      return StreamingResponse(
          generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
          media_type="text/event-stream"
      )
  ```
- **SSE Chunk Encoding**: In `backend/ai_engine.py` line 137, the output is formatted as:
  `yield f"data: {json.dumps({'chunk': chunk})}\n\n"`
- **User Model Deficiency**: In `backend/models.py` lines 127-146, the `User` table lacks the `byo_smtp_email` and `byo_smtp_token` fields. However, `core/multi_tenant.py` lines 721-728 queries them directly:
  ```python
  row = conn.execute(
      "SELECT email, byo_smtp_email, byo_smtp_token FROM users WHERE user_id = ?",
      (tenant_id,),
  ).fetchone()
  ```
- **Local Wasm Storage**: In `frontend/src/app/db/wasm-db.ts` lines 63-71, the database initializes the `local_cv_profiles` table:
  ```sql
  CREATE TABLE IF NOT EXISTS local_cv_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cv_text TEXT,
    skills TEXT,
    experience_years INTEGER,
    target_titles TEXT,
    target_locations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  );
  ```

## 2. Logic Chain
- **Custom Client Reader Needed**: Standard HTML5 `EventSource` only supports `GET` requests and cannot carry custom headers (like `Authorization: Bearer <token>` required by `verify_jwt` on the backend). Therefore, the Next.js frontend must connect using `fetch` with `ReadableStream` and decode the streamed binary stream to render words word-by-word.
- **Client-Side PDF Extraction**: To preserve the zero-cost decentralized client-side architecture, Step 1 (Upload CV) can extract raw text from PDF files directly in the browser using the `pdfjs-dist` package.
- **SMTP Setup and Sync**: In Step 3 (Email Pool), the campaign engine decrypts the credentials via ROT13 (`decoded = "".join(chr(ord(c) - 13) for c in byo_token)`). The frontend must apply a ROT13 encoding shift of +13 to `email:password` before saving.
- **DB Model Alignment**: Since the SQLAlchemy schema in `backend/models.py` is missing the `byo_smtp_email` and `byo_smtp_token` columns, adding these to `backend/models.py` is a prerequisite for saving configurations in Step 3.

## 3. Caveats
- No code files were modified during this investigation.
- We assume that the user will configure app passwords (especially for Gmail) rather than standard mailbox passwords to avoid SMTP authentication failures.

## 4. Conclusion
The implementation of the onboarding wizard (IMP-187) and streaming cover letter (IMP-243) is highly viable. The detailed integration logic and code templates have been written to `.agents/sub_orch_m3/explorer_3/analysis.md`. The implementer will need to:
1. Update `backend/models.py` to add `byo_smtp_email` and `byo_smtp_token` columns to the `User` model.
2. Mount the `frontend_api` router in `backend/main.py`.
3. Add the `/onboarding` wizard page/component in Next.js.
4. Implement the `fetch` readable stream hook in the dashboard page to consume the streaming endpoint.

## 5. Verification Method
- **Analysis Inspection**: Inspect the complete architectural analysis at: `.agents/sub_orch_m3/explorer_3/analysis.md`.
- **Backend Test Verification**: Run `pytest` to confirm that the existing backend tests run successfully and verify no regressions:
  ```powershell
  pytest
  ```
- **File Integrity**: Verify that no project source files (excluding `.agents/`) have been modified.
