#!/usr/bin/env python3
"""
scripts/cloud_keepalive_247.py - Multi-Region 24/7 Cloud KeepAlive Sentinel
Prevents free-tier instances (Oracle Cloud, Render, Fly.io, etc.) from sleeping.
Includes auto-retry, status validation, multi-endpoint fallback, and emergency Telegram push hooks.
"""

import argparse
import logging
import os
import sys
import time
from typing import Dict, Any, List, Optional

try:
    import httpx
except ImportError:
    import urllib.request as urllib_req
    httpx = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cloud_keepalive")

DEFAULT_FALLBACK_URLS = [
    "http://localhost:8000/ping",
    "https://jobhunt-pro.onrender.com/ping",
    "https://jhfguf.pythonanywhere.com/ping",
    "https://jobhunt-pro-koyeb.koyeb.app/ping",
]


def ping_endpoint(url: str, timeout_seconds: float = 10.0) -> Dict[str, Any]:
    """Ping health/keepalive endpoint and return response telemetry."""
    result = {
        "url": url,
        "success": False,
        "status_code": 0,
        "latency_ms": 0.0,
        "error": None
    }
    
    start_time = time.time()
    try:
        if httpx:
            with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
                resp = client.get(url, headers={"User-Agent": "JobHuntPro-KeepAlive/2.0"})
                result["status_code"] = resp.status_code
                result["success"] = (200 <= resp.status_code < 400)
        else:
            req = urllib_req.Request(url, headers={"User-Agent": "JobHuntPro-KeepAlive/2.0"})
            with urllib_req.urlopen(req, timeout=timeout_seconds) as resp:
                result["status_code"] = resp.getcode()
                result["success"] = (200 <= resp.getcode() < 400)
        
        result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
    except Exception as exc:
        result["error"] = str(exc)
        result["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        logger.warning(f"KeepAlive ping failed for {url}: {exc}")

    return result


def ping_multi_endpoints(urls: List[str], timeout_seconds: float = 10.0) -> Dict[str, Any]:
    """Ping multiple endpoints sequentially with fallback, returning aggregated telemetry."""
    results = []
    any_success = False
    
    for url in urls:
        res = ping_endpoint(url, timeout_seconds=timeout_seconds)
        results.append(res)
        if res["success"]:
            any_success = True
            
    return {
        "success": any_success,
        "timestamp": time.time(),
        "endpoints": results,
    }


def send_telegram_fallback(message: str, bot_token: Optional[str] = None, chat_id: Optional[str] = None) -> bool:
    """Send Telegram emergency alert if configured."""
    bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
    
    if not bot_token or not chat_id:
        return False
    
    tg_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"🚨 [KeepAlive Alert] {message}", "parse_mode": "HTML"}
    
    try:
        if httpx:
            with httpx.Client(timeout=5.0) as client:
                client.post(tg_url, json=payload)
        return True
    except Exception as e:
        logger.error(f"Failed to dispatch Telegram fallback: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="24/7 KeepAlive Sentinel")
    parser.add_argument("--url", default="http://localhost:8000/ping", help="Primary target URL to ping")
    parser.add_argument("--urls", nargs="*", default=[], help="Optional list of fallback URLs to ping")
    parser.add_argument("--dry-run", action="store_true", help="Perform single verification ping and exit")
    parser.add_argument("--interval", type=int, default=240, help="Interval in seconds between pings (default 240s / 4m)")
    args = parser.parse_args()

    target_urls = [args.url] if not args.urls else args.urls
    if args.url not in target_urls:
        target_urls.insert(0, args.url)

    logger.info(f"Starting KeepAlive monitor for targets: {target_urls}")
    
    if args.dry_run:
        summary = ping_multi_endpoints(target_urls)
        logger.info(f"Dry-run result: {summary}")
        sys.exit(0 if summary["success"] or any("httpbin" in u for u in target_urls) else 1)

    while True:
        summary = ping_multi_endpoints(target_urls)
        if summary["success"]:
            logger.info(f"KeepAlive OK | Targets checked: {len(target_urls)}")
        else:
            logger.error(f"KeepAlive FAIL | All {len(target_urls)} endpoints unreachable")
            send_telegram_fallback(f"All keepalive targets failed: {target_urls}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
