import functools
import hashlib
import json
import logging
import os
import re
from typing import Any

import httpx

try:
    import numpy as _np
    _NUMPY_AVAILABLE = True
except ImportError:
    _np = None
    _NUMPY_AVAILABLE = False
from core.pg_sqlite_shim import connect, get_backend

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

_client = None
_sqlite_cache_data = None  # In-memory storage for SQLite fallback entries to avoid database reads


def _get_client():
    global _client
    if _client is None:
        _client = httpx.Client(timeout=10.0)
    return _client


@functools.lru_cache(maxsize=1024)
def get_embedding(text: str) -> list[float]:
    """Fetch 768-dimensional embedding from Gemini's free tier."""
    if not GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY for semantic caching.")
        return []

    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
    try:
        # text-embedding-004 outputs 768 dimensions
        payload = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
        }
        client = _get_client()
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["embedding"]["values"]
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []


def calculate_offline_similarity(text1: str, text2: str) -> float:
    """Compute offline similarity using either TF-IDF Cosine Similarity or Character N-Gram Jaccard."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5))
        tfidf = vectorizer.fit_transform([text1, text2])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return float(sim)
    except Exception as e:
        logger.debug(f"Offline TF-IDF similarity failed: {e}. Falling back to Jaccard.")
        
    # Fallback to Jaccard character 3-grams
    n = 3
    if not text1 or not text2:
        return 0.0
    ngrams1 = set(text1[i:i+n] for i in range(len(text1) - n + 1))
    ngrams2 = set(text2[i:i+n] for i in range(len(text2) - n + 1))
    if not ngrams1 or not ngrams2:
        return 0.0
    return len(ngrams1.intersection(ngrams2)) / len(ngrams1.union(ngrams2))


_db_initialized = False


def ensure_db_initialized():
    global _db_initialized
    if not _db_initialized:
        init_cache_db()
        _db_initialized = True


def init_cache_db():
    """Initialize pgvector extension and the cache table dynamically based on active backend."""
    try:
        with connect() as conn:
            backend = get_backend()
            if backend == "pg":
                # Enable pgvector on PostgreSQL
                conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    id SERIAL PRIMARY KEY,
                    prompt_hash TEXT UNIQUE NOT NULL,
                    prompt_text TEXT NOT NULL,
                    embedding halfvec(768),
                    response_text TEXT NOT NULL,
                    user_id VARCHAR(64),
                    company VARCHAR(255),
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """)
                # Migration: add columns user_id and company if they don't exist
                try:
                    conn.execute("ALTER TABLE semantic_cache ADD COLUMN IF NOT EXISTS user_id VARCHAR(64);")
                    conn.execute("ALTER TABLE semantic_cache ADD COLUMN IF NOT EXISTS company VARCHAR(255);")
                except Exception:
                    pass
                conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_cache_entities ON semantic_cache(user_id, company);")
            else:
                # SQLite schema
                conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_hash TEXT UNIQUE NOT NULL,
                    prompt_text TEXT NOT NULL,
                    embedding TEXT,
                    response_text TEXT NOT NULL,
                    user_id TEXT,
                    company TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
                # Migration: add columns user_id and company if they don't exist
                for col, typ in [("user_id", "TEXT"), ("company", "TEXT")]:
                    try:
                        cols = [r[1] for r in conn.execute("PRAGMA table_info(semantic_cache)").fetchall()]
                        if col not in cols:
                            conn.execute(f"ALTER TABLE semantic_cache ADD COLUMN {col} {typ};")
                    except Exception:
                        pass
                conn.execute("CREATE INDEX IF NOT EXISTS idx_semantic_cache_entities ON semantic_cache(user_id, company);")
            logger.info(f"Semantic cache ({backend}) initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize semantic cache: {e}")


def _is_valid_cache_response(text: str) -> bool:
    """Check if the response contains any unresolved template placeholders or empty brackets."""
    if not text:
        return False
    unresolved_placeholders = [
        "{first_name}",
        "{company}",
        "{position}",
        "{title}",
        "{company_name}",
        "[Company Name]",
        "[Recruiter Name]",
        "[Job Title]",
        "[Insert",
        "<first_name>",
        "<company>",
        "<position>",
    ]
    has_unresolved = any(
        placeholder.lower() in text.lower() for placeholder in unresolved_placeholders
    )
    has_empty_braces = bool(re.search(r"\{\s*\}|\[\s*\]|<\s*>", text))
    return not (has_unresolved or has_empty_braces)


def _check_exact_match(conn: Any, prompt_hash: str, user_id: str | None, company: str | None) -> str | None:
    """Check for an exact cache match by prompt hash, partitioned by user_id and company."""
    global _sqlite_cache_data
    res = conn.execute(
        """SELECT response_text FROM semantic_cache 
           WHERE prompt_hash = ?
             AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
             AND (company = ? OR (company IS NULL AND ? IS NULL))""",
        (prompt_hash, user_id, user_id, company, company),
    ).fetchone()
    if res:
        res_text = res[0]
        if _is_valid_cache_response(res_text):
            logger.info("Exact cache hit!")
            return res_text
        else:
            logger.warning(
                "Exact cache hit contained unresolved placeholders! Invalidation triggered."
            )
            try:
                conn.execute(
                    """DELETE FROM semantic_cache 
                       WHERE prompt_hash = ?
                         AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
                         AND (company = ? OR (company IS NULL AND ? IS NULL))""",
                    (prompt_hash, user_id, user_id, company, company),
                )
                _sqlite_cache_data = None
            except Exception as ex:
                logger.error(f"Failed to delete bad exact cache entry: {ex}")
    return None


def _search_pg_vector(conn: Any, embedding: list[float], similarity_threshold: float, user_id: str | None, company: str | None) -> str | None:
    """Perform pgvector similarity search on PostgreSQL backend, partitioned by user_id and company."""
    emb_str = f"[{','.join(map(str, embedding))}]"
    query = """
    SELECT response_text, 1 - (embedding <=> ?::halfvec) AS similarity, prompt_hash
    FROM semantic_cache
    WHERE embedding IS NOT NULL
      AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
      AND (company = ? OR (company IS NULL AND ? IS NULL))
    ORDER BY embedding <=> ?::halfvec ASC
    LIMIT 1;
    """
    res = conn.execute(query, (emb_str, user_id, user_id, company, company, emb_str)).fetchone()
    if res and res[1] >= similarity_threshold:
        res_text = res[0]
        p_hash = res[2]
        if _is_valid_cache_response(res_text):
            logger.info(f"Semantic cache hit! Similarity: {res[1]:.4f}")
            return res_text
        else:
            logger.warning(
                "Semantic cache similarity hit contained unresolved placeholders! Invalidation triggered."
            )
            try:
                conn.execute(
                    """DELETE FROM semantic_cache 
                       WHERE prompt_hash = ?
                         AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
                         AND (company = ? OR (company IS NULL AND ? IS NULL))""",
                    (p_hash, user_id, user_id, company, company),
                )
            except Exception as ex:
                logger.error(
                    f"Failed to delete bad semantic cache entry: {ex}"
                )
    return None


def _search_sqlite_vector(conn: Any, embedding: list[float], similarity_threshold: float, user_id: str | None, company: str | None) -> str | None:
    """Perform local cosine similarity search for SQLite backend, partitioned by user_id and company."""
    best_response = None
    best_similarity = -1.0
    best_hash = None

    norm_a = sum(a * a for a in embedding) ** 0.5
    if norm_a > 0:
        res = conn.execute(
            """SELECT response_text, embedding, prompt_hash FROM semantic_cache 
               WHERE embedding IS NOT NULL
                 AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
                 AND (company = ? OR (company IS NULL AND ? IS NULL))""",
            (user_id, user_id, company, company)
        ).fetchall()
        
        rows = []
        for response_text, emb_json, p_hash in res:
            try:
                emb = json.loads(emb_json)
                rows.append((response_text, emb, p_hash))
            except Exception:
                continue

        if rows:
            if _NUMPY_AVAILABLE:
                try:
                    emb_matrix = _np.array(
                        [emb for _, emb, _ in rows], dtype=_np.float32
                    )
                    query_vec = _np.array(embedding, dtype=_np.float32)
                    norms = _np.linalg.norm(emb_matrix, axis=1)
                    q_norm = _np.linalg.norm(query_vec)
                    valid = norms > 0
                    sims = _np.where(
                        valid,
                        (emb_matrix @ query_vec) / (norms * q_norm),
                        -1.0,
                    )
                    best_idx = int(_np.argmax(sims))
                    best_similarity = float(sims[best_idx])
                    best_response, best_hash = rows[best_idx][0], rows[best_idx][2]
                except Exception:
                    best_response = best_similarity = best_hash = None
            
            if best_response is None:
                for response_text, emb, p_hash in rows:
                    try:
                        dot_product = sum(a * b for a, b in zip(embedding, emb, strict=False))
                        norm_b = sum(b * b for b in emb) ** 0.5
                        if norm_b > 0:
                            similarity = dot_product / (norm_a * norm_b)
                            if similarity > best_similarity:
                                best_similarity = similarity
                                best_response = response_text
                                best_hash = p_hash
                    except Exception:
                        continue

    if best_response and best_similarity >= similarity_threshold:
        if _is_valid_cache_response(best_response):
            logger.info(
                f"Semantic cache hit! Similarity: {best_similarity:.4f}"
            )
            return best_response
        else:
            logger.warning(
                "Semantic cache similarity hit contained unresolved placeholders! Invalidation triggered."
            )
            try:
                conn.execute(
                    """DELETE FROM semantic_cache 
                       WHERE prompt_hash = ?
                         AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
                         AND (company = ? OR (company IS NULL AND ? IS NULL))""",
                    (best_hash, user_id, user_id, company, company),
                )
            except Exception as ex:
                logger.error(
                    f"Failed to delete bad semantic cache entry: {ex}"
                )
    return None


def get_cached_response(prompt_text: str, similarity_threshold: float = 0.95, user_id: str | None = None, company: str | None = None) -> str | None:
    """Find a semantically similar cached response. Works on both PostgreSQL and SQLite."""
    ensure_db_initialized()
    # Support exact matching deduplication cache using SHA-256 hash.
    # Include user_id and company in hash calculation to prevent tenant leakage.
    prompt_hash = hashlib.sha256(f"{prompt_text}_{user_id}_{company}".encode("utf-8")).hexdigest()

    try:
        with connect() as conn:
            # 1. Check exact match first (O(1) operation) - compatible with both
            exact_match = _check_exact_match(conn, prompt_hash, user_id, company)
            if exact_match is not None:
                return exact_match

            # 2. If no exact match, do vector similarity search
            embedding = get_embedding(prompt_text)
            if not embedding:
                # Fallback to local similarity search!
                logger.info("Embedding API failed or unreachable. Falling back to local offline similarity check.")
                res = conn.execute(
                    """SELECT response_text, prompt_text, prompt_hash FROM semantic_cache 
                       WHERE (user_id = ? OR (user_id IS NULL AND ? IS NULL))
                         AND (company = ? OR (company IS NULL AND ? IS NULL))""",
                    (user_id, user_id, company, company)
                ).fetchall()
                
                best_response = None
                best_similarity = -1.0
                best_hash = None
                
                for response_text, cached_prompt, p_hash in res:
                    sim = calculate_offline_similarity(prompt_text, cached_prompt)
                    if sim > best_similarity:
                        best_similarity = sim
                        best_response = response_text
                        best_hash = p_hash
                        
                if best_response and best_similarity >= similarity_threshold:
                    if _is_valid_cache_response(best_response):
                        logger.info(f"Local offline similarity cache hit! Similarity: {best_similarity:.4f}")
                        return best_response
                    else:
                        logger.warning("Local offline similarity cache hit contained unresolved placeholders! Invalidation triggered.")
                        try:
                            conn.execute(
                                """DELETE FROM semantic_cache 
                                   WHERE prompt_hash = ?
                                     AND (user_id = ? OR (user_id IS NULL AND ? IS NULL))
                                     AND (company = ? OR (company IS NULL AND ? IS NULL))""",
                                (best_hash, user_id, user_id, company, company)
                            )
                        except Exception as ex:
                            logger.error(f"Failed to delete bad offline cache entry: {ex}")
                return None

            backend = get_backend()
            if backend == "pg":
                return _search_pg_vector(conn, embedding, similarity_threshold, user_id, company)
            else:
                return _search_sqlite_vector(conn, embedding, similarity_threshold, user_id, company)
    except Exception as e:
        logger.error(f"Semantic cache lookup failed: {e}")

    return None


def save_to_cache(prompt_text: str, response_text: str, user_id: str | None = None, company: str | None = None):
    """Save the AI response to the semantic cache."""
    if not _is_valid_cache_response(response_text):
        logger.warning(
            "Attempted to save a response with unresolved placeholders to semantic cache. Skipping."
        )
        return

    ensure_db_initialized()
    global _sqlite_cache_data
    # Include user_id and company in hash calculation to prevent tenant leakage.
    prompt_hash = hashlib.sha256(f"{prompt_text}_{user_id}_{company}".encode("utf-8")).hexdigest()
    embedding = get_embedding(prompt_text)

    backend = get_backend()
    if backend == "pg":
        emb_val = f"[{','.join(map(str, embedding))}]" if embedding else None
    else:
        emb_val = json.dumps(embedding) if embedding else None

    try:
        with connect() as conn:
            if backend == "pg":
                conn.execute(
                    """
                INSERT INTO semantic_cache (prompt_hash, prompt_text, embedding, response_text, user_id, company)
                VALUES (?, ?, ?::halfvec, ?, ?, ?)
                ON CONFLICT (prompt_hash) DO NOTHING;
                """,
                    (prompt_hash, prompt_text, emb_val, response_text, user_id, company),
                )
            else:
                conn.execute(
                    """
                INSERT INTO semantic_cache (prompt_hash, prompt_text, embedding, response_text, user_id, company)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (prompt_hash) DO NOTHING;
                """,
                    (prompt_hash, prompt_text, emb_val, response_text, user_id, company),
                )
                _sqlite_cache_data = None
            logger.info("Saved response to semantic cache.")
    except Exception as e:
        logger.error(f"Failed to save to semantic cache: {e}")