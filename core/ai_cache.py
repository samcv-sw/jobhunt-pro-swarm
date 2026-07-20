"""
core/ai_cache.py — Prompt-level SHA-256 caching for LLM API calls.

Usage:
    from core.ai_cache import get_cached, set_cached

    cached = get_cached(prompt_hash)
    if cached:
        return cached
    result = call_llm(...)
    set_cached(prompt_hash, result, model="gemini-1.5-flash")
    return result
"""

import hashlib
import logging
import threading

logger = logging.getLogger(__name__)

_TTL_SECONDS = 86400 * 7  # 7 days

# L1 In-Memory Fast Cache for <1ms response times
_L1_MEMORY_CACHE: dict[str, str] = {}
_L1_LOCK = threading.Lock()
_L1_MAX_SIZE = 500



import math
import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """Tokenize and normalize text to lowercase alphanumeric words."""
    return re.findall(r'\w+', text.lower())


def _cosine_similarity(text1: str, text2: str) -> float:
    """Calculate the cosine similarity between two text strings using standard library Counter."""
    words1 = _tokenize(text1)
    words2 = _tokenize(text2)
    if not words1 or not words2:
        return 0.0
    vec1 = Counter(words1)
    vec2 = Counter(words2)
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[x] * vec2[x] for x in intersection)
    sum1 = sum(vec1[x]**2 for x in vec1.keys())
    sum2 = sum(vec2[x]**2 for x in vec2.keys())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    return float(numerator) / denominator if denominator else 0.0


def _hash(text: str) -> str:
    """Return a stable SHA-256 hex digest for the given prompt string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_key(*parts: str) -> str:
    """Combine multiple string parts (e.g. job_desc + cv_text + tone) into a single cache key."""
    combined = "\n---\n".join(p.strip() for p in parts)
    return _hash(combined)


def get_cached(hash_key: str, prompt: str = "") -> str | None:
    """
    Look up `hash_key` in L1 memory cache first, then in the ai_cache table.
    Returns the cached result string, or None if not found / expired.
    If exact match fails and `prompt` is provided, performs a semantic similarity search.
    """
    # 0. Check L1 In-Memory Cache first (< 1ms)
    with _L1_LOCK:
        if hash_key in _L1_MEMORY_CACHE:
            logger.debug(f"[AI Cache] L1 MEMORY HIT — key={hash_key[:16]}…")
            return _L1_MEMORY_CACHE[hash_key]

    try:
        from web.shared import get_db

        with get_db() as conn:
            # 1. Try exact SHA-256 match first
            row = conn.execute(
                "SELECT result, created_at FROM ai_cache WHERE hash_key = ? "
                "AND datetime(created_at, '+7 days') > datetime('now')",
                (hash_key,),
            ).fetchone()
            if row:
                logger.debug(f"[AI Cache] HIT — key={hash_key[:16]}…")
                with _L1_LOCK:
                    if len(_L1_MEMORY_CACHE) >= _L1_MAX_SIZE:
                        _L1_MEMORY_CACHE.clear()
                    _L1_MEMORY_CACHE[hash_key] = row[0]
                return row[0]

            # 2. Try semantic similarity match if prompt is provided
            if prompt:
                # Limit retrieval to recent 100 entries to prevent performance penalty
                rows = conn.execute(
                    "SELECT prompt, result FROM ai_cache "
                    "WHERE prompt IS NOT NULL AND prompt != '' "
                    "AND datetime(created_at, '+7 days') > datetime('now') "
                    "ORDER BY created_at DESC LIMIT 100"
                ).fetchall()

                best_sim = 0.0
                best_result = None
                for cached_prompt, cached_result in rows:
                    sim = _cosine_similarity(prompt[:500], cached_prompt)
                    if sim > best_sim:
                        best_sim = sim
                        best_result = cached_result

                if best_sim >= 0.90 and best_result:
                    logger.info(f"[AI Cache] SEMANTIC HIT (similarity={best_sim:.2f}) — key={hash_key[:16]}…")
                    with _L1_LOCK:
                        if len(_L1_MEMORY_CACHE) >= _L1_MAX_SIZE:
                            _L1_MEMORY_CACHE.clear()
                        _L1_MEMORY_CACHE[hash_key] = best_result
                    return best_result
                else:
                    logger.debug(f"[AI Cache] SEMANTIC MISS (best similarity={best_sim:.2f}) — key={hash_key[:16]}…")
    except Exception as e:
        logger.warning(f"[AI Cache] get_cached error: {e}")
    return None


def set_cached(hash_key: str, result: str, model: str = "", prompt: str = "") -> None:
    """
    Persist `result` in L1 memory cache and DB table under `hash_key`.
    Silently ignores errors (cache is a best-effort optimisation).
    """
    with _L1_LOCK:
        if len(_L1_MEMORY_CACHE) >= _L1_MAX_SIZE:
            _L1_MEMORY_CACHE.clear()
        _L1_MEMORY_CACHE[hash_key] = result

    try:
        from web.shared import get_db

        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO ai_cache (hash_key, prompt, result, model) VALUES (?, ?, ?, ?)",
                (hash_key, prompt[:500] if prompt else "", result, model),
            )
            conn.commit()
        logger.debug(f"[AI Cache] SET — key={hash_key[:16]}… model={model}")
    except Exception as e:
        logger.warning(f"[AI Cache] set_cached error: {e}")


def purge_expired() -> int:
    """
    Delete cache entries older than TTL_SECONDS.
    Returns the number of rows deleted.
    Intended to be called from a scheduled cron route.
    """
    try:
        from web.shared import get_db

        with get_db() as conn:
            cur = conn.execute(
                "DELETE FROM ai_cache WHERE datetime(created_at, '+7 days') <= datetime('now')"
            )
            conn.commit()
            deleted = cur.rowcount
        logger.info(f"[AI Cache] Purged {deleted} expired entries.")
        return deleted
    except Exception as e:
        logger.warning(f"[AI Cache] purge_expired error: {e}")
        return 0


def get_stats() -> dict:
    """Return cache hit/miss statistics for monitoring."""
    try:
        from web.shared import get_db

        with get_db() as conn:
            total = conn.execute("SELECT COUNT(*) FROM ai_cache").fetchone()[0]
            fresh = conn.execute(
                "SELECT COUNT(*) FROM ai_cache WHERE datetime(created_at, '+7 days') > datetime('now')"
            ).fetchone()[0]
        return {"total": total, "fresh": fresh, "expired": total - fresh}
    except Exception as e:
        return {"error": str(e)}
