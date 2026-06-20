import os
import json
import logging
import hashlib
import httpx
from core.pg_sqlite_shim import PgConnectionWrapper

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

def init_cache_db():
    """Initialize pgvector extension and the cache table."""
    try:
        with PgConnectionWrapper() as conn:
            # Enable pgvector
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create semantic cache table with halfvec (16-bit) to cut storage by 50%
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
            logger.info("Semantic cache (pgvector) initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize pgvector semantic cache: {e}")

def get_cached_response(prompt_text: str, similarity_threshold: float = 0.95) -> str:
    """Find a semantically similar cached response."""
    prompt_hash = hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()
    
    with PgConnectionWrapper() as conn:
        # 1. Check exact match first (O(1) operation)
        res = conn.execute("SELECT response_text FROM semantic_cache WHERE prompt_hash = %s", (prompt_hash,)).fetchone()
        if res:
            logger.info("Exact cache hit!")
            return res[0]
            
        # 2. If no exact match, do vector similarity search
        embedding = get_embedding(prompt_text)
        if not embedding:
            return None
            
        # format vector for pgvector literal: '[0.1, 0.2, ...]'
        emb_str = f"[{','.join(map(str, embedding))}]"
        
        # <=> is cosine distance in pgvector. Similarity = 1 - distance.
        query = """
        SELECT response_text, 1 - (embedding <=> %s::halfvec) AS similarity 
        FROM semantic_cache 
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::halfvec ASC 
        LIMIT 1;
        """
        res = conn.execute(query, (emb_str, emb_str)).fetchone()
        
        if res and res[1] >= similarity_threshold:
            logger.info(f"Semantic cache hit! Similarity: {res[1]:.4f}")
            return res[0]
            
    return None

def save_to_cache(prompt_text: str, response_text: str):
    """Save the AI response to the semantic cache."""
    prompt_hash = hashlib.sha256(prompt_text.encode('utf-8')).hexdigest()
    embedding = get_embedding(prompt_text)
    
    emb_str = f"[{','.join(map(str, embedding))}]" if embedding else None
    
    try:
        with PgConnectionWrapper() as conn:
            conn.execute("""
            INSERT INTO semantic_cache (prompt_hash, prompt_text, embedding, response_text)
            VALUES (%s, %s, %s::halfvec, %s)
            ON CONFLICT (prompt_hash) DO NOTHING;
            """, (prompt_hash, prompt_text, emb_str, response_text))
            logger.info("Saved response to semantic cache.")
    except Exception as e:
        logger.error(f"Failed to save to semantic cache: {e}")
