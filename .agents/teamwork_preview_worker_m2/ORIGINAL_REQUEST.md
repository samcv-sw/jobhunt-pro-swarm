## 2026-07-03T13:19:03Z
Implement local Vector DB (RAG) Integration.
Specifically:
1. Add `qdrant-client` to `requirements.txt` and install it using pip/uv.
2. Implement `core/vector_db.py` to manage Qdrant client, initialize collection ("cover_letters" with cosine distance and 768 dimensions), insert generated cover letters, and query similar cover letters.
   - It must import `get_embedding` from `core.semantic_cache`.
   - If `get_embedding(text)` returns an empty list (offline or missing API key), it must fall back to a deterministic local token-hashing algorithm that projects words into a normalized (L2-norm) 768-dimensional float vector.
3. Update `backend/ai_engine.py`:
   - `generate_smart_cover_letter` and `generate_smart_cover_letter_stream` must accept optional `user_id: str = None` and `use_rag: bool = True` parameters.
   - In both functions, retrieve similar cover letters matching the target job description (filtered by the user's `user_id`) using your vector DB manager.
   - Inject the retrieved past cover letters into the Groq chat completion system prompt inside a ## Style Reference & Past Cover Letters (Few-Shot Examples) block to guide writing style.
   - Automatically ingest newly generated cover letters into the vector database.
4. Update `backend/main.py`:
   - Retrieve `user_id` from jwt_payload in the cover letter endpoints `/api/v1/generate-cover-letter` and `/api/v1/ai/generate-cover-letter/stream`.
   - Pass the user ID down to the Celery task and generator.
5. Update `backend/tasks.py`:
   - Add `user_id` parameter to `generate_cover_letter` Celery task and pass it to `generate_smart_cover_letter`.
6. Append the following environment variables to `.env.example` and `.env`:
   # ── Vector DB / RAG (Qdrant) ──────────────────
   QDRANT_PATH=./data/qdrant_db
   QDRANT_IN_MEMORY=false
7. Create `tests/test_rag.py` using the template proposed by the Test Strategy Explorer (`c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_rag_3\proposed_test_rag.py`), adjusting imports to use the real `core.vector_db` implementation.
8. Run pytest tests/test_rag.py and make sure it passes.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write a handoff report at c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_m2\handoff.md when complete, showing build/test results, and send_message back to c4e4ddf0-be49-4898-928d-66a9918ca89c.
