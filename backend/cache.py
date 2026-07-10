from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

def setup_cache(app):
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    print("[CACHE] 🚀 Extreme In-Memory API Caching initialized.")
