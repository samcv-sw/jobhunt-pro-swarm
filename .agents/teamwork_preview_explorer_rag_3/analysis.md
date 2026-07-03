# Vector DB (RAG) Integration Test Strategy Analysis

## Executive Summary
This report outlines the strategy to verify the local Vector DB (RAG) integration using a test script `tests/test_rag.py`. We recommend using an in-process, in-memory database setup (such as Qdrant in-memory mode or SQLite custom similarity) combined with a deterministic, L2-normalized offline mock encoder to ensure fast, zero-dependency, and isolated testing.

---

## 1. Existing Test Infrastructure & Patterns

Based on an audit of the `tests/` directory:
- **FastAPI / HTTP Testing (`tests/test_backend.py`)**: Uses `pytest` with `pytest-asyncio` as the runner. The backend endpoints are tested using `httpx.AsyncClient` coupled with the ASGI transport `ASGITransport(app=app)`.
- **Mocking Strategy**: 
  - Uses `pytest.fixture(autouse=True)` with `monkeypatch` to mock Celery delay methods to prevent connecting to Redis in tests.
  - Mocks async generators / streams via local async generator mocks (e.g. `mock_stream`).
  - `tests/test_ats_scorer.py` uses `unittest.IsolatedAsyncioTestCase` for async unit tests, patching `AsyncGroq` using `@patch("core.ats_scorer.AsyncGroq")` and `AsyncMock` to simulate JSON chat completions.
- **Database Testing (`tests/e2e/test_database.py`)**: Uses a module-scoped fixture `setup_test_db()` to run `Base.metadata.create_all` for SQLAlchemy, using a local SQLite file (`./jobhunt_local.db`).
- **Active Pytest Plugins**: The environment runs `pytest-9.0.3` with active plugins: `asyncio`, `mock`, `anyio`, `Faker`, `logfire`, and `langsmith`.

---

## 2. Embedding Generation Mechanism & Test Strategy

### Existing Mechanism
The codebase currently has an embedding generation function `get_embedding(text: str) -> list[float]` in `core/semantic_cache.py`. It calls Gemini's free tier `text-embedding-004` model and yields a 768-dimensional float vector. It requires a live `GEMINI_API_KEY` and internet access.

### Comparison of Embedding Strategies for Tests
| Option | Pros | Cons | Recommendation |
| :--- | :--- | :--- | :--- |
| **Mock Offline Encoder** | Zero dependencies, 100% offline, deterministic, runs in microseconds. | Does not verify the live API connection. | **Strongly Recommended (Primary)** |
| **Local Sentence-Transformers** | Tests with actual semantic vectors. | `sentence-transformers` is NOT installed. Heavy download footprint violates `CODE_ONLY` isolation. | **Not Recommended** |
| **Live API (Gemini/OpenAI/Groq)** | Verifies live integration. | Requires API keys, slow, rate-limited, fails in offline environments. | **Not Recommended for Unit Tests** |

### Implementing a Deterministic Mock Encoder
For testing, we patch the embedding generator to return a deterministic unit vector (L2-normalized) of 768 dimensions based on keywords in the text. This allows us to assert that query similarity is calculated correctly.
For example:
- Text containing "python" gets a high weight at index 100.
- Text containing "network" gets a high weight at index 200.
- Cosine similarity (simply the dot product of two unit vectors) will be close to $1.0$ for matching terms and $0.0$ for non-matching terms.

---

## 3. Database Architecture Recommendation for Local Tests

The requirement is to integrate a local vector database like **Qdrant** or **Chroma** to store and retrieve cover letters.
- **Qdrant**: Strongly recommended. `qdrant-client` supports a lightweight in-memory storage mode:
  ```python
  from qdrant_client import QdrantClient
  client = QdrantClient(location=":memory:")
  ```
  This creates an isolated, in-process vector DB instance with zero binary compile requirements and zero external services.
- **Chroma**: Heavy binary dependencies (like `hnswlib`), which often fail to install or compile on Windows.
- **SQLite Custom Similarity**: Alternatively, since `core/semantic_cache.py` already implements a robust local fallback utilizing pure Python/NumPy cosine similarity on SQLite text fields, reusing this pattern for cover letters is a zero-dependency alternative.

---

## 4. Test Suite Coverage & Assertions (`tests/test_rag.py`)

The test suite must verify the following coverage areas:
1. **Mock Encoder Validity**: Assert that the encoder generates a `list` of `float` of exactly 768 dimensions and is L2-normalized.
2. **Insertion & Persistence**: Insert a cover letter and associated metadata (e.g. user ID, job title) and verify that it is written successfully without database constraints issues.
3. **Exact Matching**: Querying with the exact text should return the document with a similarity score of $\approx 1.0$.
4. **Semantic Search & Ranking**:
   - Insert a "Python Backend" cover letter and a "Cisco Networking" cover letter.
   - Query for "Django web programmer". Assert that the Python cover letter is returned as the top result (index 0) with a higher similarity score than the Networking letter.
   - Query for "BGP routing configuration". Assert that the Networking letter is returned as the top result.
5. **Empty Database Handling**: Perform a similarity query on an empty collection and verify that it returns an empty list gracefully.
6. **Robustness to Special Characters**: Insert and query with special characters, emojis, and Arabic text (e.g., Cairo/Tajawal fonts support) and verify no encoding or SQL exceptions occur.
7. **Error/Exception Isolation**: Mock the database backend to fail and verify that the application handles the failure gracefully.

---

## 5. Proposed Test Implementation Code
A complete, copy-paste-ready template has been written to the working directory:
`c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_rag_3\proposed_test_rag.py`
This script simulates the entire test lifecycle using `pytest` and can be easily adapted to the final vector DB class wrapper.
