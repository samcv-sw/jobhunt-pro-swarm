"""
JobHunt Pro SaaS — Multi-Region Edge Cloud Orchestrator (v2026.1)
Geo-distributed deployment monitor, real-time edge latency matrix,
and zero-downtime failover router.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger(__name__)


class EdgeRegion:
    def __init__(self, region_code: str, region_name: str, endpoint_url: str):
        self.region_code = region_code
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.is_healthy = True
        self.last_latency_ms = 0.0
        self.last_check = 0.0


class MultiRegionOrchestrator:
    """
    Manages global multi-region edge deployments (e.g. us-east, eu-central, me-south-1 GCC).
    Performs periodic health checks and routes traffic to the nearest healthy region.
    """

    def __init__(self):
        self.regions: Dict[str, EdgeRegion] = {
            "me-south-1": EdgeRegion("me-south-1", "GCC / Dubai Edge", "https://gcc-edge.jobhuntpro.com/health"),
            "eu-central-1": EdgeRegion("eu-central-1", "Frankfurt Edge", "https://eu-edge.jobhuntpro.com/health"),
            "us-east-1": EdgeRegion("us-east-1", "N. Virginia Primary", "https://us-edge.jobhuntpro.com/health"),
        }
        self.primary_region = "us-east-1"

    async def check_region_health(self, region_code: str) -> bool:
        """Pings region health endpoint and measures latency."""
        region = self.regions.get(region_code)
        if not region:
            return False

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(region.endpoint_url)
                latency_ms = (time.time() - start_time) * 1000.0
                region.last_latency_ms = round(latency_ms, 2)
                region.last_check = time.time()
                region.is_healthy = (res.status_code == 200)
                return region.is_healthy
        except Exception:
            region.is_healthy = False
            region.last_latency_ms = 9999.0
            return False

    async def run_global_health_check(self) -> Dict[str, Any]:
        """Runs parallel health checks across all registered edge regions."""
        tasks = [self.check_region_health(code) for code in self.regions.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)

        healthy_count = sum(1 for r in self.regions.values() if r.is_healthy)
        best_region = self.select_optimal_region("me-south-1")

        return {
            "timestamp": time.time(),
            "total_regions": len(self.regions),
            "healthy_regions": healthy_count,
            "optimal_region": best_region,
            "matrix": {
                code: {
                    "name": r.region_name,
                    "healthy": r.is_healthy,
                    "latency_ms": r.last_latency_ms,
                }
                for code, r in self.regions.items()
            },
        }

    def select_optimal_region(self, client_preferred_region: str = "me-south-1") -> str:
        """Selects healthiest and lowest latency edge region for client."""
        preferred = self.regions.get(client_preferred_region)
        if preferred and preferred.is_healthy and preferred.last_latency_ms < 200:
            return client_preferred_region

        # Find healthy region with lowest latency
        healthy_regions = [r for r in self.regions.values() if r.is_healthy]
        if not healthy_regions:
            return self.primary_region

        best = min(healthy_regions, key=lambda r: r.last_latency_ms)
        return best.region_code


multi_region_orchestrator = MultiRegionOrchestrator()
