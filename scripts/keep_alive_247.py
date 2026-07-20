"""
JobHunt Pro — 24/7 Zero-Cost ($0) Keep-Alive Engine
Pings primary & fallback deployment endpoints asynchronously every 3 minutes
to ensure Render/Koyeb/Fly.io/HuggingFace instances never enter cold sleep.
"""

import os
import sys
import time
import asyncio
import urllib.request
import urllib.error

TARGET_ENDPOINTS = [
    os.getenv("PRIMARY_API_URL", "https://jobhunt-pro.onrender.com/healthz"),
    os.getenv("BACKEND_API_URL", "https://jhfguf.pythonanywhere.com/api/v1/health"),
    os.getenv("KOYEB_API_URL", "https://jobhunt-pro-koyeb.koyeb.app/healthz"),
]

INTERVAL_SECONDS = int(os.getenv("PING_INTERVAL", "180"))  # 3 minutes

async def ping_url(url: str):
    """Pings a single endpoint and logs status."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "JobHuntPro-KeepAlive/2026.1"}
        )
        start = time.time()
        with urllib.request.urlopen(req, timeout=10) as response:
            latency_ms = round((time.time() - start) * 1000, 2)
            code = response.getcode()
            print(f"[KEEP-ALIVE] OK ({code}) -> {url} [{latency_ms}ms]")
            return True
    except urllib.error.HTTPError as e:
        print(f"[KEEP-ALIVE] HTTP {e.code} -> {url}")
        return False
    except Exception as e:
        print(f"[KEEP-ALIVE] WARN: {url} failed: {e}")
        return False

async def main():
    print(f"=== JobHunt Pro 24/7 Keep-Alive Engine Started ===")
    print(f"Pinging {len(TARGET_ENDPOINTS)} targets every {INTERVAL_SECONDS}s...")
    
    while True:
        tasks = [ping_url(url) for url in TARGET_ENDPOINTS if url]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[KEEP-ALIVE] Stopped cleanly.")
