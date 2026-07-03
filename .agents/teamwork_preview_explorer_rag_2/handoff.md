# Handoff Report — Vector DB (RAG) Integration Analysis

## 1. Observation
- We analyzed `backend/ai_engine.py` (lines 44-149) and observed that the two cover letter generation functions are:
  - `generate_smart_cover_letter(job_description: str, user_cv: str) -> dict` (lines 44-97)
  - `generate_smart_cover_letter_stream(job_description: str, user_cv: str, tone: str)` (lines 98-149)
- Both functions use `AsyncGroq` client to complete prompts using model `llama3-70b-8192` with static system/user prompts. Neither function accepts `user_id` or queries any database.
- We analyzed the python environment via `run_command` (`python -m pip list` and imports) and confirmed that `qdrant-client`, `chromadb`, and `sentence-transformers` are currently NOT installed in the environment.
- However, `numpy` (v1.26.4 or similar) and `scikit-learn` (v1.9.0) are installed.
- The project runs tests using `pytest` as configured in `pytest.ini`.

---

## 2. Logic Chain
- **Step 1**: To retrieve past cover letters and writing styles for a specific user, the system must know which user is requesting the generation. Therefore, we must extract `user_id` from the JWT in the FastAPI endpoints (like `/api/v1/generate-cover-letter` and `/api/v1/ai/generate-cover-letter/stream`) and pass it through to the AI engine functions.
- **Step 2**: Since the agent system runs under strict CODE_ONLY network restrictions, any vector embedding generation function must run 100% locally and offline, without downloading models from HuggingFace at runtime.
- **Step 3**: To achieve this, we can implement a custom deterministic pseudo-embedding generator using standard Python libraries and `numpy`. By hashing tokens and projecting them to a 384-dimensional space, we get normalized vectors that support Cosine Distance matching without any network overhead.
- **Step 4**: A dedicated module `backend/vector_store.py` is the cleanest architectural pattern to handle vector DB operations (connection, indexing, query, upsert) without cluttering the LLM logic in `backend/ai_engine.py`.
- **Step 5**: For streaming generations, the full cover letter is not available until the stream completes. By accumulating stream chunks into an internal list, we can concatenate and upsert the complete letter asynchronously (using `asyncio.create_task`) after the stream finishes, avoiding any latency impact on the user.

---

## 3. Caveats
- **Read-Only Scoped**: We did not install packages or modify the codebase directly because of the read-only constraint.
- **Dependency Assumption**: Our solution assumes `qdrant-client` will be installed in the environment. If it cannot be installed, a lightweight database wrapper using SQLite or simple JSON file storage can be used with the same vector search math.
- **Semantic Quality**: The custom deterministic hash-based embedding represents word overlap similarity. In a production environment with internet access, this should be swapped for `sentence-transformers` or OpenAI/Groq embeddings for true semantic understanding.

---

## 4. Conclusion
Integrating local Vector DB RAG is highly feasible:
1. Create `backend/vector_store.py` using Qdrant (in-process disk or in-memory mode) and the custom offline embedding function.
2. Update `backend/ai_engine.py` signatures to accept `user_id` and `use_rag` parameters.
3. Query the vector DB and inject formatting/style examples into the LLM system prompt as few-shot guides.
4. Auto-save newly generated cover letters back to the vector DB asynchronously.

---

## 5. Verification Method
1. **Verification File**: Create `tests/test_rag.py`.
2. **Execution Command**: Run `pytest tests/test_rag.py` to assert that:
   - Collection is created successfully.
   - Points can be inserted with `upsert_cover_letter`.
   - `search_similar_cover_letters` returns the correct results with metadata filters applied.
3. **Invalidation Conditions**: If `qdrant-client` fails to run in-process without docker, or if the mock embedding vectors fail unit norm checks, this design is invalid and needs revision.
