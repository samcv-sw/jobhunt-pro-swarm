import os
import json
import logging
import hashlib
import httpx
from core.pg_sqlite_shim import connect, get_backend

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def get_embedding(text: str) -> list[float]:
    """Fetch 768-dimensional embedding from Gemini's free tier."""
    if not GEMINI_API_KEY:
        logger.warning("No GEMINI_API_KEY for semantic caching.")
        return []
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
    try:
        # text-embedding-004 outputs 768 dimensions
        payload = {"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}}
        resp = httpx.post(url, json=payload, timeout=10.0)
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

def get_cached_response(prompt_text: str, similarity_threshold: float = 0.95) -> str:
    """Find a semantically similar cached response. Works on both PostgreSQL and SQLite."""
    ensure_db_initialized()
    prompt_hash = hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()
    
    try:
        with connect() as conn:
            # 1. Check exact match first (O(1) operation) - compatible with both
            res = conn.execute("SELECT response_text FROM semantic_cache WHERE prompt_hash = ?", (prompt_hash,)).fetchone()
            if res:
                logger.info("Exact cache hit!")
                return res[0]
                
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
                SELECT response_text, 1 - (embedding <=> ?::halfvec) AS similarity 
                FROM semantic_cache 
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> ?::halfvec ASC 
                LIMIT 1;
                """
                res = conn.execute(query, (emb_str, emb_str)).fetchone()
                if res and res[1] >= similarity_threshold:
                    logger.info(f"Semantic cache hit! Similarity: {res[1]:.4f}")
                    return res[0]
            else:
                # SQLite: Local python-based cosine similarity
                res = conn.execute("SELECT response_text, embedding FROM semantic_cache WHERE embedding IS NOT NULL").fetchall()
                best_response = None
                best_similarity = -1.0
                for response_text, emb_json in res:
                    try:
                        emb = json.loads(emb_json)
                        # Pure Python Cosine Similarity
                        dot_product = sum(a * b for a, b in zip(embedding, emb))
                        norm_a = sum(a * a for a in embedding) ** 0.5
                        norm_b = sum(b * b for b in emb) ** 0.5
                        if norm_a > 0 and norm_b > 0:
                            similarity = dot_product / (norm_a * norm_b)
                            if similarity > best_similarity:
                                best_similarity = similarity
                                best_response = response_text
                    except Exception:
                        continue
                
                if best_response and best_similarity >= similarity_threshold:
                    logger.info(f"Semantic cache hit! Similarity: {best_similarity:.4f}")
                    return best_response
    except Exception as e:
        logger.error(f"Semantic cache lookup failed: {e}")
        
    return None

def save_to_cache(prompt_text: str, response_text: str):
    """Save the AI response to the semantic cache."""
    ensure_db_initialized()
    prompt_hash = hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()
    embedding = get_embedding(prompt_text)
    
    backend = get_backend()
    if backend == "pg":
        emb_val = f"[{','.join(map(str, embedding))}]" if embedding else None
    else:
        emb_val = json.dumps(embedding) if embedding else None
        
    try:
        with connect() as conn:
            if backend == "pg":
                conn.execute("""
                INSERT INTO semantic_cache (prompt_hash, prompt_text, embedding, response_text)
                VALUES (?, ?, ?::halfvec, ?)
                ON CONFLICT (prompt_hash) DO NOTHING;
                """, (prompt_hash, prompt_text, emb_val, response_text))
            else:
                conn.execute("""
                INSERT INTO semantic_cache (prompt_hash, prompt_text, embedding, response_text)
                VALUES (?, ?, ?, ?)
                ON CONFLICT (prompt_hash) DO NOTHING;
                """, (prompt_hash, prompt_text, emb_val, response_text))
            logger.info("Saved response to semantic cache.")
    except Exception as e:
        logger.error(f"Failed to save to semantic cache: {e}")
