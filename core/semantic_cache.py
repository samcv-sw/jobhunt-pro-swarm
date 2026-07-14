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
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """)
            else:
                # SQLite schema
                conn.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_hash TEXT UNIQUE NOT NULL,
                    prompt_text TEXT NOT NULL,
                    embedding TEXT,
                    response_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """)
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


def _check_exact_match(conn: Any, prompt_hash: str) -> str | None:
    """Check for an exact cache match by prompt hash.

    Args:
        conn: The database connection.
        prompt_hash: The SHA-256 hash of the prompt.

    Returns:
        The cached response text if found and valid, otherwise None.
    """
    global _sqlite_cache_data
    res = conn.execute(
        "SELECT response_text FROM semantic_cache WHERE prompt_hash = ?",
        (prompt_hash,),
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
                    "DELETE FROM semantic_cache WHERE prompt_hash = ?",
                    (prompt_hash,),
                )
                _sqlite_cache_data = None
            except Exception as ex:
                logger.error(f"Failed to delete bad exact cache entry: {ex}")
    return None


def _search_pg_vector(conn: Any, embedding: list[float], similarity_threshold: float) -> str | None:
    """Perform pgvector similarity search on PostgreSQL backend.

    Args:
        conn: The database connection.
        embedding: The vector embedding list of floats.
        similarity_threshold: Minimum cosine similarity required.

    Returns:
        The cached response text if a similar valid entry is found, otherwise None.
    """
    emb_str = f"[{','.join(map(str, embedding))}]"
    query = """
    SELECT response_text, 1 - (embedding <=> ?::halfvec) AS similarity, prompt_hash
    FROM semantic_cache
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> ?::halfvec ASC
    LIMIT 1;
    """
    res = conn.execute(query, (emb_str, emb_str)).fetchone()
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
                    "DELETE FROM semantic_cache WHERE prompt_hash = ?",
                    (p_hash,),
                )
            except Exception as ex:
                logger.error(
                    f"Failed to delete bad semantic cache entry: {ex}"
                )
    return None


def _search_sqlite_vector(conn: Any, embedding: list[float], similarity_threshold: float) -> str | None:
    """Perform local cosine similarity search for SQLite backend.

    Args:
        conn: The database connection.
        embedding: The vector embedding list of floats.
        similarity_threshold: Minimum cosine similarity required.

    Returns:
        The cached response text if a similar valid entry is found, otherwise None.
    """
    global _sqlite_cache_data
    best_response = None
    best_similarity = -1.0
    best_hash = None

    norm_a = sum(a * a for a in embedding) ** 0.5
    if norm_a > 0:
        if _sqlite_cache_data is None:
            res = conn.execute(
                "SELECT response_text, embedding, prompt_hash FROM semantic_cache WHERE embedding IS NOT NULL"
            ).fetchall()
            _sqlite_cache_data = []
            for response_text, emb_json, p_hash in res:
                try:
                    emb = json.loads(emb_json)
                    _sqlite_cache_data.append((response_text, emb, p_hash))
                except Exception:
                    continue

        if _sqlite_cache_data:
            if _NUMPY_AVAILABLE:
                try:
                    rows = [(rt, ph) for rt, _, ph in _sqlite_cache_data]
                    emb_matrix = _np.array(
                        [emb for _, emb, _ in _sqlite_cache_data], dtype=_np.float32
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
                    best_response, best_hash = rows[best_idx]
                except Exception:
                    best_response = best_similarity = best_hash = None
                    for response_text, emb, p_hash in _sqlite_cache_data:
                        try:
                            dot_product = sum(a * b for a, b in zip(embedding, emb, strict=False))
                            norm_b = sum(b * b for b in emb) ** 0.5
                            if norm_b > 0:
                                similarity = dot_product / (norm_a * norm_b)
                                if best_similarity is None or similarity > best_similarity:
                                    best_similarity = similarity
                                    best_response = response_text
                                    best_hash = p_hash
                        except Exception:
                            continue
            else:
                for response_text, emb, p_hash in _sqlite_cache_data:
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
                    "DELETE FROM semantic_cache WHERE prompt_hash = ?",
                    (best_hash,),
                )
                _sqlite_cache_data = None
            except Exception as ex:
                logger.error(
                    f"Failed to delete bad semantic cache entry: {ex}"
                )
    return None


def get_cached_response(prompt_text: str, similarity_threshold: float = 0.95) -> str | None:
    """Find a semantically similar cached response. Works on both PostgreSQL and SQLite.

    Args:
        prompt_text: The prompt text to search for in the cache.
        similarity_threshold: The minimum similarity ratio to consider a match.

    Returns:
        The cached response text as a string if found, otherwise None.
    """
    ensure_db_initialized()
    prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

    try:
        with connect() as conn:
            # 1. Check exact match first (O(1) operation) - compatible with both
            exact_match = _check_exact_match(conn, prompt_hash)
            if exact_match is not None:
                return exact_match

            # 2. If no exact match, do vector similarity search
            embedding = get_embedding(prompt_text)
            if not embedding:
                return None

            backend = get_backend()
            if backend == "pg":
                return _search_pg_vector(conn, embedding, similarity_threshold)
            else:
                return _search_sqlite_vector(conn, embedding, similarity_threshold)
    except Exception as e:
        logger.error(f"Semantic cache lookup failed: {e}")

    return None


def save_to_cache(prompt_text: str, response_text: str):
    """Save the AI response to the semantic cache."""
    if not _is_valid_cache_response(response_text):
        logger.warning(
            "Attempted to save a response with unresolved placeholders to semantic cache. Skipping."
        )
        return

    ensure_db_initialized()
    global _sqlite_cache_data
    prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
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
                INSERT INTO semantic_cache (prompt_hash, prompt_text, embedding, response_text)
                VALUES (?, ?, ?::halfvec, ?)
                ON CONFLICT (prompt_hash) DO NOTHING;
                """,
                    (prompt_hash, prompt_text, emb_val, response_text),
                )
            else:
                conn.execute(
                    """
                INSERT INTO semantic_cache (prompt_hash, prompt_text, embedding, response_text)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (prompt_hash) DO NOTHING;
                """,
                    (prompt_hash, prompt_text, emb_val, response_text),
                )
                _sqlite_cache_data = None
            logger.info("Saved response to semantic cache.")
    except Exception as e:
        logger.error(f"Failed to save to semantic cache: {e}")
