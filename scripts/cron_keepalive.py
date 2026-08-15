"""
JobHunt Pro — 24/7 Zero-Cost Multi-Cloud Keep-Alive & Daemon Ping Engine
Runs asynchronously on GitHub Actions / external cron to guarantee 99.99% uptime with $0 infrastructure cost.
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

async def ping_target(url: str) -> bool:
    """Pings a target health endpoint."""
    if not url:
        return True
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "JobHuntPro-KeepAlive-Swarm/2026.2"}
        )
        start = time.time()
        with urllib.request.urlopen(req, timeout=12) as response:
            latency_ms = round((time.time() - start) * 1000, 2)
            code = response.getcode()
            print(f"[KEEPALIVE-SUCCESS] ({code}) -> {url} [Latency: {latency_ms}ms]")
            return True
    except urllib.error.HTTPError as e:
        print(f"[KEEPALIVE-HTTP] {e.code} -> {url}")
        return False
    except Exception as e:
        print(f"[KEEPALIVE-WARN] {url} -> {e}")
        return False

async def main():
    print("=== [JobHunt Pro] 24/7 Zero-Cost Cloud Keep-Alive Swarm Triggered ===")
    tasks = [ping_target(endpoint) for endpoint in TARGET_ENDPOINTS if endpoint]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    success_count = sum(1 for r in results if r is True)
    print(f"=== Keepalive Complete: {success_count}/{len(tasks)} endpoints active and healthy. ===")

if __name__ == "__main__":
    asyncio.run(main())
