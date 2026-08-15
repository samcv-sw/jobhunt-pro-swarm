"""
core/cloud_orchestration_hub.py
================================
Enterprise 24/7 Zero-Cost Cloud Orchestration & Self-Healing Hub.
Manages permanent free-tier cloud infrastructure, automated keep-alive pulses,
health pingers, and serverless failover for JobHunt Pro SaaS.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("CloudOrchestrationHub")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class CloudOrchestrationHub:
    """
    Orchestrates 24/7 zero-cost operations across free-tier cloud hosts,
    preventing idle sleep cycles and maintaining active health telemetry.
    """

    def __init__(self, endpoints: Optional[List[str]] = None, ping_interval_sec: int = 600):
        self.endpoints = endpoints or [
            os.getenv("PRODUCTION_URL", "https://jobhunt-pro.onrender.com"),
            os.getenv("BACKUP_CLOUD_URL", "https://jobhunt-pro.koyeb.app"),
            os.getenv("CLOUDFLARE_WORKER_URL", "https://jobhunt-pro.workers.dev"),
        ]
        # Filter out empty or placeholder URLs
        self.endpoints = [ep for ep in self.endpoints if ep and ep.startswith("http")]
        self.ping_interval_sec = ping_interval_sec
        self.is_running = False
        self._last_health_status: Dict[str, Dict[str, Any]] = {}

    async def ping_endpoint(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        """Pings an individual cloud endpoint and records latency and status."""
        health_url = f"{url.rstrip('/')}/health"
        start_time = time.monotonic()
        try:
            resp = await client.get(health_url, timeout=12.0)
            latency_ms = round((time.monotonic() - start_time) * 1000, 2)
            is_healthy = resp.status_code in [200, 204, 301, 302, 404]  # Alive response
            return {
                "url": url,
                "status_code": resp.status_code,
                "latency_ms": latency_ms,
                "healthy": is_healthy,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
        except Exception as exc:
            latency_ms = round((time.monotonic() - start_time) * 1000, 2)
            return {
                "url": url,
                "status_code": 0,
                "latency_ms": latency_ms,
                "healthy": False,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(exc),
            }

    async def execute_health_pulse(self) -> Dict[str, Any]:
        """
        Executes a concurrent keep-alive pulse across all registered endpoints.
        """
        if not self.endpoints:
            return {"status": "no_endpoints", "results": []}

        results = []
        async with httpx.AsyncClient(headers={"User-Agent": "JobHuntPro-CloudPulse/2.0"}) as client:
            tasks = [self.ping_endpoint(client, ep) for ep in self.endpoints]
            results = await asyncio.gather(*tasks, return_exceptions=False)

        for res in results:
            self._last_health_status[res["url"]] = res

        healthy_count = sum(1 for r in results if r["healthy"])
        return {
            "total_endpoints": len(self.endpoints),
            "healthy_count": healthy_count,
            "all_healthy": healthy_count == len(self.endpoints),
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def start_eternal_loop(self):
        """Runs the continuous background keep-alive loop."""
        self.is_running = True
        logger.info("[CloudHub] Eternal 24/7 Keep-Alive Loop started.")
        while self.is_running:
            try:
                report = await self.execute_health_pulse()
                logger.info(
                    f"[CloudHub] Pulse executed: {report.get('healthy_count')}/{report.get('total_endpoints')} active."
                )
            except Exception as e:
                logger.error(f"[CloudHub] Error during health pulse: {e}")
            await asyncio.sleep(self.ping_interval_sec)

    def stop(self):
        """Stops the eternal loop."""
        self.is_running = False
        logger.info("[CloudHub] Eternal loop stopped.")

    def get_latest_telemetry(self) -> Dict[str, Any]:
        """Returns the latest captured telemetry snapshot."""
        return {
            "is_running": self.is_running,
            "ping_interval_sec": self.ping_interval_sec,
            "endpoints_monitored": len(self.endpoints),
            "status_map": self._last_health_status,
        }


# Global singleton instance
cloud_hub = CloudOrchestrationHub()
