import os
import json
import logging
import hashlib
import re
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


def _get_client():
    global _client
    if _client is None:
        _client = httpx.Client(timeout=10.0)
    return _client


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


def get_cached_response(prompt_text: str, similarity_threshold: float = 0.95) -> str:
    """Find a semantically similar cached response. Works on both PostgreSQL and SQLite."""
    ensure_db_initialized()
    prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

    try:
        with connect() as conn:
            # 1. Check exact match first (O(1) operation) - compatible with both
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
                    except Exception as ex:
                        logger.error(f"Failed to delete bad exact cache entry: {ex}")

            # 2. If no exact match, do vector similarity search
            embedding = get_embedding(prompt_text)
            if not embedding:
                return None

            backend = get_backend()
            if backend == "pg":
                # format vector for pgvector literal: '[0.1, 0.2, ...]'
                emb_str = f"[{','.join(map(str, embedding))}]"
                # <=> is cosine distance in pgvector. Similarity = 1 - distance.
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
            else:
                # SQLite: Local python-based cosine similarity
                res = conn.execute(
                    "SELECT response_text, embedding, prompt_hash FROM semantic_cache WHERE embedding IS NOT NULL"
                ).fetchall()
                best_response = None
                best_similarity = -1.0
                best_hash = None

                # Numpy-accelerated cosine similarity (falls back to pure-Python)
                norm_a = sum(a * a for a in embedding) ** 0.5
                if norm_a > 0:
                    if _NUMPY_AVAILABLE and res:
                        # Build matrix of all cached embeddings at once
                        try:
                            rows = [(rt, ph) for rt, ej, ph in res]
                            emb_matrix = _np.array(
                                [json.loads(ej) for _, ej, _ in res], dtype=_np.float32
                            )
                            query_vec = _np.array(embedding, dtype=_np.float32)
                            norms = _np.linalg.norm(emb_matrix, axis=1)
                            q_norm = _np.linalg.norm(query_vec)
                            # Avoid division by zero
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
                            # Fall through to pure-Python path
                            best_response = best_similarity = best_hash = None
                            for response_text, emb_json, p_hash in res:
                                try:
                                    emb = json.loads(emb_json)
                                    dot_product = sum(
                                        a * b for a, b in zip(embedding, emb)
                                    )
                                    norm_b = sum(b * b for b in emb) ** 0.5
                                    if norm_b > 0:
                                        similarity = dot_product / (norm_a * norm_b)
                                        if (
                                            best_similarity is None
                                            or similarity > best_similarity
                                        ):
                                            best_similarity = similarity
                                            best_response = response_text
                                            best_hash = p_hash
                                except Exception:
                                    continue
                    else:
                        # Pure-Python fallback
                        best_response = None
                        best_similarity = -1.0
                        best_hash = None
                        for response_text, emb_json, p_hash in res:
                            try:
                                emb = json.loads(emb_json)
                                dot_product = sum(a * b for a, b in zip(embedding, emb))
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
                        except Exception as ex:
                            logger.error(
                                f"Failed to delete bad semantic cache entry: {ex}"
                            )
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
            logger.info("Saved response to semantic cache.")
    except Exception as e:
        logger.error(f"Failed to save to semantic cache: {e}")
