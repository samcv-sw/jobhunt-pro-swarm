# Scope: Vector DB (RAG) Integration

## Architecture
- Integrates local Qdrant/Chroma vector DB to backend.
- Modifies `backend/ai_engine.py` to retrieve past cover letters and writing styles.
- Verification script in `tests/test_rag.py`.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Integrate Vector DB | Implement local vector database usage inside `backend/ai_engine.py` | none | PLANNED |
| 2 | Test Script | Write and run `tests/test_rag.py` to verify insert and similarity search | 1 | PLANNED |
