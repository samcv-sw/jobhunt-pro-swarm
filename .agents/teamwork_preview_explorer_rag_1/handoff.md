# Handoff Report - Environment & Vector Database Investigation

This is a **Hard Handoff** report documenting the investigation of the Python environment, test runner mechanisms, and vector database selections for the JobHunt Pro local RAG feature.

---

## 1. Observation

### Python Environment and Requirements
1. The global Python interpreter is located at `C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe` and serves as the active environment containing dependencies:
   * `pytest-9.0.3` is globally installed.
   * `pydantic-ai-2.2.0` is globally installed.
2. The local `.venv2` folder is unpopulated and only contains baseline packages:
   ```
   Package Version
   ------- -------
   pip     25.0.1
   PyYAML  6.0.3
   ```
3. Neither `chromadb` nor `qdrant-client` is installed in the system environment (`pip show` failed with `WARNING: Package(s) not found: chromadb, qdrant-client`).
4. Requirements files (`requirements.txt`, `requirements-cloud.txt`, `requirements_render.txt`) do not contain any vector DB references. For example, `requirements.txt` contains:
   ```
   langgraph>=0.0.30
   langgraph-checkpoint-postgres>=1.0.0
   pydantic-ai>=0.0.1
   psycopg>=3.1.0
   psycopg-pool>=3.1.0
   camoufox[geoip]>=1.0.0
   a2wsgi==1.10.4
   a2wsgi
   procrastinate
   slowapi>=0.1.9
   ```

### Test Runner Configuration
1. `pytest.ini` defines test paths and recursion directories:
   ```ini
   [pytest]
   testpaths = tests
   norecursedirs = _backups .git .github scratch
   python_files = test_*.py
   ```
2. Sanity test runs successfully using `pytest tests/test_runtime.py`:
   ```
   platform win32 -- Python 3.12.10, pytest-9.0.3, pluggy-1.6.0
   plugins: langsmith-0.8.5, anyio-4.13.0, Faker-40.18.0, logfire-4.37.0, asyncio-1.3.0, mock-3.15.1
   collected 1 item
   tests\test_runtime.py .                                                  [100%]
   ============================== 1 passed in 0.49s ==============================
   ```
3. `TEST_READY.md` lists the E2E test runner command:
   ```bash
   python -m pytest tests/e2e/
   ```

### Docker Status
1. Running `docker ps` returns a connection error:
   ```
   failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine; check if the path is correct and if the daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.
   ```
   This confirms Docker is **not running** on the host.

### Existing Embeddings Setup
1. `core/semantic_cache.py` contains the primary embedding generation logic using Gemini's `text-embedding-004` (producing 768-dimensional vectors):
   ```python
   def get_embedding(text: str) -> list[float]:
       """Fetch 768-dimensional embedding from Gemini's free tier."""
       # ...
       url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
       # ...
   ```

---

## 2. Logic Chain

1. **Observation 1.1 & 1.2** show that Python 3.12.10 is the active runtime and that the `uv` package manager is available locally.
2. **Observation 1.3** confirms that no vector database python package is installed in the active environment.
3. **Observation 2.1 & 2.2** show that `pytest` is configured via `pytest.ini` and successfully executes tests (like `tests/test_runtime.py`). Thus, the new test file `tests/test_rag.py` should be run using `pytest tests/test_rag.py`.
4. **Observation 3.1** demonstrates that Docker is not running. Therefore, running a vector database inside a docker container is ruled out for local execution, necessitating a native local database.
5. **Observation 4.1** shows that `core/semantic_cache.py` already implements 768-dimensional embedding generation using Gemini's `text-embedding-004`. Thus, the vector DB config should match `size=768` and `distance=COSINE`.
6. To select between Qdrant and Chroma:
   * Both run locally in-memory or on disk.
   * Qdrant client (`qdrant-client`) has a minimal dependency tree and is native Python/Rust compiled, installing cleanly on Windows.
   * Chroma client (`chromadb`) has a very heavy dependency tree (onnxruntime, kubernetes, fastapi, etc.) and is prone to Windows build failures if C++ compilation tools are missing.
   * Qdrant features standard Pydantic models (like `PointStruct`, `VectorParams`) which natively integrate with the project's Pydantic-heavy structure.
   * Consequently, Qdrant is recommended for local integration.

---

## 3. Caveats

1. **Internet Access for Gemini API**: Gemini embedding generation requires internet access and a valid `GEMINI_API_KEY` at runtime. In offline testing environments, this API call must be mocked.
2. **Windows compilation support**: Although `qdrant-client` doesn't build heavy C++ extensions, if dependencies like `grpcio` do not match Python version wheels, pip may try to compile them. Fortunately, standard Python 3.12 wheels exist for all dependencies.

---

## 4. Conclusion

1. **Active Env**: Use system Python 3.12.10 environment.
2. **Package Action**: Install `qdrant-client` using `uv pip install qdrant-client` and add it to `requirements.txt`.
3. **Database Choice**: Use **Qdrant** in local persistent directory mode (`data/qdrant_db`) or in-memory (`:memory:`) for tests.
4. **Architecture**: Implement `core/vector_db.py` exposing a `VectorDBManager` class. Reuse the `text-embedding-004` (768 dimensions) model from `core/semantic_cache.py`. Mock the embedding generator in `tests/test_rag.py` to allow offline testing.
5. **Integration**: Retrieve matches in `backend/ai_engine.py` to build a few-shot context prompt for the Groq LPU, and save successfully generated cover letters back to Qdrant.

---

## 5. Verification Method

1. **Package Verification**: After running `uv pip install qdrant-client`, verify installation:
   ```powershell
   python -c "import qdrant_client; print(qdrant_client.__version__)"
   ```
2. **Sanity Verification**: Run the project sanity test to make sure the environment remains valid:
   ```powershell
   pytest tests/test_runtime.py
   ```
3. **RAG Integration Verification**: Run the proposed RAG test script once implemented:
   ```powershell
   pytest tests/test_rag.py
   ```
