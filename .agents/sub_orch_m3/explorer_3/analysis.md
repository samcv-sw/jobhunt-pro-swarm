# Implementation Strategy & Analysis: Onboarding Wizard (IMP-187) & Cover Letter Streaming (IMP-243)

This report details the architectural investigation and implementation design for integrating the User Onboarding Wizard and the Streaming Cover Letter Preview in the Next.js frontend, connecting securely to the FastAPI backend.

---

## 1. Executive Summary
- **Objective**: Design the frontend-to-backend integration strategy for the multi-step user onboarding wizard (**IMP-187**) and the word-by-word streaming cover letter preview (**IMP-243**).
- **Core Challenge**: The streaming endpoint `/api/v1/ai/generate-cover-letter/stream` is a `POST` request protected by JWT (`verify_jwt`), making standard browser `EventSource` (which only supports `GET` and lacks headers) incompatible.
- **Solution**: Implement a zero-dependency frontend stream reader in the Next.js app using `fetch` with `ReadableStream` (`response.body.getReader()`) and a binary `TextDecoder` buffer.
- **Local-First Architecture**: Align onboarding steps (CV upload, preferences, BYO SMTP setup, and test runs) with the client-side WebAssembly SQLite (OPFS) and local storage while syncing critical SMTP credentials back to the PostgreSQL database.

---

## 2. Codebase Observations & Constraints

### 2.1 Backend Streaming Endpoint (`backend/main.py` & `backend/ai_engine.py`)
In `backend/main.py`, the streaming route is defined as:
```python
@app.post("/api/v1/ai/generate-cover-letter/stream", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def stream_cover_letter(req: CoverLetterRequest, request: Request = None) -> StreamingResponse:
    ...
    return StreamingResponse(
        generate_smart_cover_letter_stream(req.job_description, req.user_cv, req.tone),
        media_type="text/event-stream"
    )
```
In `backend/ai_engine.py`, the generator yields tokens formatted as JSON-encoded Server-Sent Events (SSE):
```python
yield f"data: {json.dumps({'chunk': chunk})}\n\n"
```
Each token is sent inside a JSON object wrapper with the double-newline (`\n\n`) event separator.

### 2.2 User Database Discrepancy (`backend/models.py` vs `core/multi_tenant.py`)
In `core/multi_tenant.py` (lines 722-728), the campaign engine queries user SMTP credentials:
```python
row = conn.execute(
    "SELECT email, byo_smtp_email, byo_smtp_token FROM users WHERE user_id = ?",
    (tenant_id,),
).fetchone()
```
However, in `backend/models.py`, the `User` model **does not contain** `byo_smtp_email` and `byo_smtp_token` columns. 
* **Critical Finding**: To support Step 3 (Email Pool) of onboarding, the `User` model in `backend/models.py` must be updated to include these fields so they are correctly defined in the schema.
* **Token Encoding**: In `core/multi_tenant.py`, the `byo_smtp_token` is decoded by shifting character codes back by 13 (ROT13 variation):
  `decoded = "".join(chr(ord(c) - 13) for c in byo_token)`. 
  The frontend must ROT13-encode the email credentials (`email:password`) in the same format before writing to the database.

### 2.3 Client SQLite Wasm DB (`frontend/src/app/db/wasm-db.ts`)
The client app utilizes a local browser-based SQLite Wasm database running on OPFS (Origin Private File System) with the following schema:
- `local_cv_profiles` (stores `cv_text`, `skills`, `experience_years`, `target_titles`, `target_locations`).
- `local_campaigns` (stores local job campaign status).
- `local_sync_queue` (tracks client-side database mutations to sync with Postgres).

---

## 3. IMP-243: Streaming Cover Letter Frontend Connection

Standard browser `EventSource` does not support custom headers or `POST` requests. Since the FastAPI streaming endpoint requires JWT authentication, we must use a custom stream reader in the Next.js frontend dashboard (`frontend/src/app/dashboard/page.tsx`).

### Proposed Frontend Integration Snippet (React/TypeScript):
```typescript
import { useState } from "react";

export function useCoverLetterStream() {
  const [coverLetter, setCoverLetter] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const generateCoverLetterStream = async (cvText: string, jobDesc: string, tone: string, token: string) => {
    setIsGenerating(true);
    setCoverLetter("");
    setError(null);

    try {
      const response = await fetch("/api/v1/ai/generate-cover-letter/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          user_cv: cvText,
          job_description: jobDesc,
          tone: tone,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Streaming failed: ${response.status} - ${errorText}`);
      }

      if (!response.body) {
        throw new Error("Response body is not readable.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        // Decode binary chunk and append to buffer
        buffer += decoder.decode(value, { stream: true });

        // Split buffer by event double-newline boundary (\n\n)
        const parts = buffer.split("\n\n");
        
        // Retain any partial trailing line in buffer
        buffer = parts.pop() || "";

        for (const part of parts) {
          const line = part.trim();
          if (line.startsWith("data: ")) {
            try {
              const jsonStr = line.slice(6); // Extract JSON payload after "data: "
              const parsed = JSON.parse(jsonStr);
              if (parsed && parsed.chunk) {
                // Append chunk to state to render word-by-word
                setCoverLetter((prev) => prev + parsed.chunk);
              }
            } catch (err) {
              console.warn("Failed to parse stream chunk:", err, line);
            }
          }
        }
      }
    } catch (err: any) {
      setError(err.message || "An error occurred during streaming.");
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  return { coverLetter, isGenerating, error, generateCoverLetterStream };
}
```

---

## 4. IMP-187: Onboarding Wizard Implementation Strategy

The onboarding wizard should be presented to new users when no profiles exist in the local SQLite DB. It will be implemented as a multi-step modal or client route `/onboarding`.

### 4.1 Step-by-Step Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Onboarding Wizard Flow                          │
├───────────────┬─────────────────┬──────────────────┬───────────────────┤
│    Step 1     │     Step 2      │      Step 3      │      Step 4       │
│   Upload CV   │   Preferences   │    Email Pool    │     Test Run      │
└───────┬───────┴────────┬────────┴────────┬─────────┴─────────┬─────────┘
        │                │                 │                   │
        ▼                ▼                 ▼                   ▼
 Extract text via  Input job roles,  Input SMTP host,   Trigger scraper/
 client-side JS    skills, location  user, app password. stream cover letter.
 or backend API.   and select tone.  Verify connection  Send test email
 Store in WASM.    Store in WASM.    & save encrypted.  to own mailbox.
```

#### Step 1: Upload CV
- **UI Component**: File input zone (supporting PDF/TXT/DOCX) or Copy/Paste textarea.
- **Client Parsing (Recommended)**: Use `pdfjs-dist` to extract text directly in the browser. This eliminates backend server processing and maintains the local-first, zero-cost architecture.
- **Backend Parsing (Alternative)**: Create a new endpoint `POST /api/v1/cv/parse` in `backend/main.py` using the pre-installed `pdfplumber` library to extract text and return it as JSON:
  ```python
  @app.post("/api/v1/cv/parse", dependencies=[Depends(verify_jwt)])
  async def parse_cv_pdf(file: UploadFile = File(...)) -> dict:
      import pdfplumber
      with pdfplumber.open(file.file) as pdf:
          raw_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
      return {"cv_text": raw_text}
  ```
- **Local Storage**: Save extracted text into WASM SQLite:
  `INSERT OR REPLACE INTO local_cv_profiles (id, cv_text, created_at) VALUES (1, ?, datetime('now'));`

#### Step 2: Preferences
- **UI Component**: Form fields for target roles (chips/tags), target locations, target skills, experience years, and preferred cover letter tone.
- **Local Storage**: Run a local SQL query:
  `UPDATE local_cv_profiles SET target_titles = ?, target_locations = ?, skills = ?, experience_years = ? WHERE id = 1;`
  And store `preferred_tone` in local storage or table.

#### Step 3: Configure Email Pool (BYO SMTP)
- **UI Component**: Form to collect sender email, SMTP provider, and SMTP App Password.
- **Test Connection**: Trigger a POST request to a new/mapped test endpoint `/api/v1/smtp/test`:
  ```python
  @app.post("/api/v1/smtp/test", dependencies=[Depends(verify_jwt)])
  async def test_smtp_auth(req: SMTPTestRequest):
      from core.byo_smtp import test_smtp_connection
      success, msg = test_smtp_connection(req.email, req.password, req.provider)
      return {"success": success, "message": msg}
  ```
- **Encryption & Save**: On connection success, the client encodes credentials via ROT13 and calls `POST /api/v1/user/smtp-config` (or `/api/byo-smtp/save`) to sync SMTP parameters to the database:
  ```typescript
  const encodeROT13 = (str: string) => str.split("").map(c => String.fromCharCode(c.charCodeAt(0) + 13)).join("");
  const encryptedToken = encodeROT13(`${email}:${password}`);
  // POST payload: { byo_smtp_email: email, byo_smtp_token: encryptedToken }
  ```

#### Step 4: Test Run
- **UI Component**: Input box for a sample job description / job URL.
- **Verification Run**:
  1. Trigger cover letter generation by connecting to the stream `/api/v1/ai/generate-cover-letter/stream` and outputting it word-by-word.
  2. Allow user to click "Send Test Email". The backend will send this customized cover letter to the user's *own* email address (using the configured SMTP settings from Step 3) to verify delivery.
- **Completion**: Mark `localStorage.setItem('onboarding_completed', 'true')` and redirect user to `/dashboard`.

---

## 5. Architectural Improvements Recommendations
1. **Sync Schema Updates**: Update the SQLAlchmey `User` model in `backend/models.py` with `byo_smtp_email` and `byo_smtp_token` columns to ensure databases initialized on Render/neon align with `core/multi_tenant.py`.
2. **Mount Frontend API Router**: Mount the `frontend_api` router inside `backend/main.py` using `app.include_router(frontend_api_router)` to consolidate all endpoints in the version 3 container runner (`start_cloud.py`).
3. **WASM-SQLite Auto-Bootstrapping**: Add a initialization check inside `frontend/src/app/layout.tsx` to automatically redirect users to `/onboarding` if `SELECT COUNT(*) FROM local_cv_profiles` returns `0`.
