# Environment & Vector Database Investigation Report

## 1. Python Environment & Vector DB Package Status

### Active Python Environment
* **Location**: `C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe` (System-wide Python 3.12.10 installation).
* **Details**: 
  * The project workspace includes a `.venv2` directory; however, it only contains base packages (`pip` and `PyYAML`).
  * The system's global Python environment contains all the project's third-party dependencies (such as `pydantic-ai` v2.2.0, `pytest` v9.0.3, `langgraph` v1.2.6, `psycopg` v3.3.4, `httpx`, etc.) and acts as the active workspace interpreter.
  * The package manager `uv` (v0.11.6) is available on the system path, meaning dependencies can be installed fast using `uv pip install <package>`.

### Vector DB Packages Status
* **Status**: Neither `qdrant-client` nor `chromadb` is currently installed.
* **Requirements Files**:
  * `requirements.txt`: Contains core dependencies like `langgraph`, `pydantic-ai`, `psycopg`, `procrastinate`, and `slowapi`. No vector DB packages are listed.
  * `requirements-cloud.txt`: Contains deployment dependencies like `fastapi`, `uvicorn`, `itsdangerous`, `mangum`, `beautifulsoup4`, `curl_cffi`, and `procrastinate[asyncpg]`. No vector DB packages are listed.
  * `requirements_render.txt`: Web-specific packages. No vector DB packages are listed.
* **Action Required**: Add the recommended vector DB client package to `requirements.txt` and install it.

---

## 2. Test Execution Mechanism

* **Test Framework**: `pytest` (v9.0.3) is used.
* **Configuration**: `pytest.ini` in the root directory specifies:
  ```ini
  [pytest]
  testpaths = tests
  norecursedirs = _backups .git .github scratch
  python_files = test_*.py
  ```
* **Execution Commands**:
  * **E2E Test Suite**: `python -m pytest tests/e2e/` (runs frontend, backend, and database integration tests).
  * **Individual sanity test**: `pytest tests/test_runtime.py` (which successfully executes and passes in ~0.5s).
  * **Proposed Verification Test**: A new test file `tests/test_rag.py` should be run using `pytest tests/test_rag.py`.

---

## 3. Vector DB Recommendation: Qdrant vs Chroma

### Docker Daemon Status
* Running `docker ps` returns a connection failure, indicating that **Docker is not currently running**.
* Therefore, the vector database **must be able to run locally in-memory or in a persistent folder** without requiring a Docker container.

### Recommendation
We recommend using **Qdrant** (via `qdrant-client`) over Chroma.

### Rationale

| Feature | Qdrant (`qdrant-client`) | Chroma (`chromadb`) |
| :--- | :--- | :--- |
| **Local Mode** | **Excellent**: Pure python/Rust mock local backend. Supported via `QdrantClient(path="path/to/db")` or `QdrantClient(":memory:")` out-of-the-box. | **Good**: Persistent SQLite and hnswlib storage via `PersistentClient(path="...")` or `EphemeralClient()`. |
| **Dependency Weight** | **Lightweight**: Minimal direct requirements (`urllib3`, `grpcio`, `protobuf`). Avoids environment bloat. | **Heavy**: Brings in `onnxruntime`, `opentelemetry`, `kubernetes`, `fastapi`, `uvicorn`, `posthog`, etc. |
| **Windows Compilation** | **Highly Robust**: Precompiled wheels available for all dependencies; zero Windows C++ compiler issues. | **Risk of Compilation Errors**: Native library builds (like `hnswlib`) can fail if MSVC Build Tools are missing. |
| **Pydantic Compatibility** | **Excellent**: Native support for Pydantic models (e.g. `PointStruct`, `VectorParams`) which aligns with `pydantic-ai` v2.2.0. | **Moderate**: Upgrades can sometimes introduce pydantic v1 vs v2 conflicts. |
| **Production Path** | **Seamless**: Same code API works with local file DB, local Docker container, or Qdrant Cloud. | **Limited**: Transitioning from embedded to server/cloud is less common and harder to manage. |

---

## 4. Proposed Local Vector DB Architecture

### A. Embedding Generation
The project already features an embedding generation function in `core/semantic_cache.py` using Gemini's `text-embedding-004` (768 dimensions):
```python
def get_embedding(text: str) -> list[float]:
    """Fetch 768-dimensional embedding from Gemini's free tier."""
```
* **Production**: Reuse `get_embedding(text)` to generate query and doc vectors.
* **Testing / Offline Mode**: In `tests/test_rag.py`, mock `get_embedding` to return a static mock 768-dimensional vector (e.g., `[0.1] * 768`) to ensure the test suite runs offline and doesn't hit external APIs.

### B. Vector Database Manager (`core/vector_db.py`)
Introduce a new module to manage the Qdrant local client, initialize collections, and handle CRUD.

```python
import os
import uuid
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

class VectorDBManager:
    def __init__(self, collection_name: str = "cover_letters"):
        self.collection_name = collection_name
        
        # Read config from environment variables
        self.in_memory = os.getenv("QDRANT_IN_MEMORY", "false").lower() == "true"
        self.db_path = os.getenv("QDRANT_PATH", "./data/qdrant_db")
        
        if self.in_memory:
            logger.info("Initializing in-memory Qdrant client")
            self.client = QdrantClient(":memory:")
        else:
            logger.info(f"Initializing persistent Qdrant client at {self.db_path}")
            os.makedirs(self.db_path, exist_ok=True)
            self.client = QdrantClient(path=self.db_path)
            
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                logger.info(f"Creating collection '{self.collection_name}' with 768 dimensions")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")
            raise

    def insert_cover_letter(self, text: str, embedding: list[float], metadata: dict, doc_id: str = None) -> str:
        """Insert a cover letter vector and payload into the collection."""
        if not doc_id:
            doc_id = str(uuid.uuid4())
            
        point = PointStruct(
            id=doc_id,
            vector=embedding,
            payload={
                "text": text,
                **metadata
            }
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        return doc_id

    def search_similar(self, query_embedding: list[float], limit: int = 3) -> list[dict]:
        """Retrieve similar past cover letters."""
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=limit
        )
        return [
            {
                "id": hit.id,
                "text": hit.payload.get("text", ""),
                "score": hit.score,
                "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
            }
            for hit in results
        ]
```

### C. Backend Integration (`backend/ai_engine.py`)
In `backend/ai_engine.py`, the cover letter generation functions can be augmented with Vector DB context retrieval:

1. **Query**: Retrieve historical cover letters matching the current job description semantic vector:
   ```python
   # 1. Generate embedding for current job description
   query_emb = get_embedding(job_description)
   
   # 2. Fetch matches
   vdb = VectorDBManager()
   matches = vdb.search_similar(query_emb, limit=2)
   
   # 3. Format as few-shot examples
   rag_context = ""
   if matches:
       rag_context = "\nHere are examples of past successful cover letters matching this style:\n"
       for idx, match in enumerate(matches, 1):
           rag_context += f"Example {idx}:\n{match['text']}\n---\n"
   ```
2. **Inject**: Append the `rag_context` to the system prompt or user prompt passed to the Groq LLM.
3. **Persist**: Upon successful generation of a cover letter, insert it into Qdrant:
   ```python
   # 4. Store newly generated letter
   generated_letter_text = parsed_response["body"]
   new_emb = get_embedding(generated_letter_text)
   vdb.insert_cover_letter(
       text=generated_letter_text,
       embedding=new_emb,
       metadata={
           "job_description": job_description,
           "company": "extracted_company",
           "tone": tone
       }
   )
   ```

### D. Configuration Variables (`.env` and `.env.example`)
Append the following variables:
```bash
# Vector Database Configuration
VECTOR_DB_TYPE=qdrant
QDRANT_PATH=./data/qdrant_db
QDRANT_IN_MEMORY=false
```
During tests, environment variables should be overridden or the manager should be initialized with `in_memory=True`.
