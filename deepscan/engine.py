"""
DeepScan Engine — Unified Orchestration Layer.

DeepScanEngine is the single entry point that orchestrates, enhances, and amplifies
every existing scanning/analysis tool in the JobHunt Pro ecosystem. It aggregates
results from all scanners into a unified, ranked, deduplicated intelligence stream.

It integrates with (but never replaces) the existing tools:
    - core.autonomous_market_scanner.AutonomousMarketScanner
    - core.client_hunter.ClientHunterEngine
    - core.scam_detector.ScamDetector
    - core.intent_detector.IntentDetector
    - core.ats_matcher.ATSMatcher
    - agents.autonomous_lead_radar.AutonomousLeadRadar
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("deepscan.engine")

# Registry of every known scanner in the ecosystem. Each entry declares the
# scanner's name, its module path, its weight in the unified power score, and
# whether it is currently active. This is the "map of the empire."
SCANNER_REGISTRY: List[Dict[str, Any]] = [
    {"name": "ats_matcher", "module": "core.ats_matcher", "weight": 0.15, "active": True},
    {"name": "ats_scorer", "module": "core.ats_scorer", "weight": 0.10, "active": True},
    {"name": "ats_cracker", "module": "core.ats_cracker", "weight": 0.08, "active": True},
    {"name": "ats_penetration_engine", "module": "core.ats_penetration_engine", "weight": 0.08, "active": True},
    {"name": "autonomous_market_scanner", "module": "core.autonomous_market_scanner", "weight": 0.10, "active": True},
    {"name": "client_hunter", "module": "core.client_hunter", "weight": 0.12, "active": True},
    {"name": "scam_detector", "module": "core.scam_detector", "weight": 0.08, "active": True},
    {"name": "intent_detector", "module": "core.intent_detector", "weight": 0.08, "active": True},
    {"name": "autonomous_lead_radar", "module": "agents.autonomous_lead_radar", "weight": 0.10, "active": True},
    {"name": "hidden_job_scraper", "module": "core.hidden_job_scraper", "weight": 0.05, "active": True},
    {"name": "job_surge_radar", "module": "core.job_surge_radar", "weight": 0.04, "active": True},
    {"name": "google_dorks_harvester", "module": "core.google_dorks_harvester", "weight": 0.04, "active": True},
    {"name": "b2b_lead_empire", "module": "core.b2b_lead_empire", "weight": 0.06, "active": True},
    {"name": "gcc_compensation_radar", "module": "core.gcc_compensation_radar", "weight": 0.04, "active": True},
    {"name": "gulf_comp_oracle", "module": "core.gulf_comp_oracle", "weight": 0.04, "active": True},
    {"name": "career_quantum_oracle", "module": "core.career_quantum_oracle", "weight": 0.04, "active": True},
    {"name": "headhunter_executive_dossier", "module": "core.headhunter_executive_dossier", "weight": 0.04, "active": True},
    {"name": "company_osint", "module": "core.company_osint", "weight": 0.03, "active": True},
    {"name": "email_finder", "module": "core.email_finder", "weight": 0.03, "active": True},
    {"name": "freelance_arbitrage_swarm", "module": "core.freelance_arbitrage_swarm", "weight": 0.03, "active": True},
]


@dataclass
class ScanResult:
    """A single normalized result produced by any scanner in the ecosystem."""

    source: str
    title: str = ""
    company: str = ""
    url: str = ""
    email: str = ""
    region: str = "GLOBAL"
    intent_score: float = 0.0
    match_score: float = 0.0
    is_scam: bool = False
    scam_reason: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def composite_score(self) -> float:
        """Blend intent + match into a single 0-100 opportunity score."""
        return round(0.6 * self.intent_score + 0.4 * self.match_score, 2)

    @property
    def dedup_key(self) -> str:
        """Stable identity for deduplication across scanners."""
        base = f"{self.company}|{self.title}|{self.email}".lower().strip()
        return hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


class DeepScanEngine:
    """Unified orchestrator that runs every scanner and fuses the results."""

    def __init__(self) -> None:
        self.scanner_registry: List[Dict[str, Any]] = list(SCANNER_REGISTRY)
        self._scanner_instances: Dict[str, Any] = {}
        self._health: Dict[str, Dict[str, Any]] = {}
        self._last_full_scan: Optional[float] = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: float = 300.0  # 5 minutes

    # ------------------------------------------------------------------
    # Lazy instantiation of underlying scanners (defensive import).
    # ------------------------------------------------------------------
    def _get_scanner(self, name: str, module_path: str) -> Optional[Any]:
        if name in self._scanner_instances:
            return self._scanner_instances[name]
        try:
            module = __import__(module_path, fromlist=["*"])
            # Heuristic: find the primary class in the module.
            cls = None
            for attr in dir(module):
                if attr.startswith("_"):
                    continue
                obj = getattr(module, attr)
                if isinstance(obj, type) and obj.__module__ == module.__name__:
                    cls = obj
                    break
            if cls is None:
                logger.warning("No class found in %s", module_path)
                return None
            instance = cls()
            self._scanner_instances[name] = instance
            return instance
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load scanner %s (%s): %s", name, module_path, exc)
            self._health[name] = {"ok": False, "error": str(exc), "ts": time.time()}
            return None

    # ------------------------------------------------------------------
    # Health / power introspection.
    # ------------------------------------------------------------------
    def get_scanner_health(self) -> Dict[str, Any]:
        """Return per-scanner health and the overall ecosystem readiness."""
        total_weight = 0.0
        healthy_weight = 0.0
        details: Dict[str, Any] = {}
        for entry in self.scanner_registry:
            name = entry["name"]
            weight = entry["weight"]
            total_weight += weight
            inst = self._get_scanner(name, entry["module"])
            ok = inst is not None and entry.get("active", True)
            if ok:
                healthy_weight += weight
            details[name] = {
                "ok": ok,
                "weight": weight,
                "active": entry.get("active", True),
                "module": entry["module"],
            }
        readiness = round((healthy_weight / total_weight) * 100, 2) if total_weight else 0.0
        return {
            "readiness_percent": readiness,
            "healthy_scanners": sum(1 for d in details.values() if d["ok"]),
            "total_scanners": len(self.scanner_registry),
            "details": details,
        }

    # ------------------------------------------------------------------
    # Unified scan orchestration.
    # ------------------------------------------------------------------
    async def run_full_scan(
        self,
        target_keywords: Optional[List[str]] = None,
        limit: int = 25,
        region: str = "GLOBAL",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Run all active scanners in parallel and fuse their outputs."""
        now = time.time()
        if use_cache and self._last_full_scan and (now - self._last_full_scan) < self._cache_ttl:
            return self._cache.get("last_full_scan", {})

        results: List[ScanResult] = []
        errors: List[Dict[str, Any]] = []

        async def _run_one(name: str, module: str) -> None:
            inst = self._get_scanner(name, module)
            if inst is None:
                return
            try:
                # Try common scan entry points, whichever exists.
                if hasattr(inst, "scan_and_rank_opportunities"):
                    raw = await inst.scan_and_rank_opportunities(
                        target_keywords=target_keywords, limit=limit
                    )
                elif hasattr(inst, "scan_for_leads"):
                    raw = inst.scan_for_leads(target_region=region)
                elif hasattr(inst, "run_daily_market_checkup"):
                    raw = inst.run_daily_market_checkup()
                else:
                    raw = []
                results.extend(self._normalize(name, raw))
                self._health[name] = {"ok": True, "ts": now}
            except Exception as exc:  # noqa: BLE001
                errors.append({"scanner": name, "error": str(exc)})
                self._health[name] = {"ok": False, "error": str(exc), "ts": now}

        tasks = [
            _run_one(e["name"], e["module"])
            for e in self.scanner_registry
            if e.get("active", True)
        ]
        await asyncio.gather(*tasks)

        # Deduplicate across scanners.
        seen: set = set()
        unique: List[ScanResult] = []
        for r in results:
            key = r.dedup_key
            if key in seen:
                continue
            seen.add(key)
            unique.append(r)

        # Rank by composite score.
        unique.sort(key=lambda r: r.composite_score, reverse=True)
        top = unique[:limit]

        payload = {
            "scanned_at": now,
            "total_raw_results": len(results),
            "unique_results": len(unique),
            "returned_results": len(top),
            "errors": errors,
            "health": self.get_scanner_health(),
            "results": [self._to_dict(r) for r in top],
        }
        self._last_full_scan = now
        self._cache["last_full_scan"] = payload
        return payload

    # ------------------------------------------------------------------
    # Normalization helpers.
    # ------------------------------------------------------------------
    def _normalize(self, source: str, raw: Any) -> List[ScanResult]:
        """Coerce arbitrary scanner output into ScanResult objects."""
        out: List[ScanResult] = []
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, (list, tuple)):
            return out
        for item in raw:
            if not isinstance(item, dict):
                continue
            out.append(
                ScanResult(
                    source=source,
                    title=str(item.get("title") or item.get("job_title") or ""),
                    company=str(item.get("company") or ""),
                    url=str(item.get("url") or item.get("link") or ""),
                    email=str(item.get("email") or ""),
                    region=str(item.get("region") or "GLOBAL"),
                    intent_score=float(item.get("intent_score") or item.get("score") or 0.0),
                    match_score=float(item.get("match_score") or 0.0),
                    is_scam=bool(item.get("is_scam") or False),
                    scam_reason=str(item.get("scam_reason") or ""),
                    raw=item,
                )
            )
        return out

    @staticmethod
    def _to_dict(r: ScanResult) -> Dict[str, Any]:
        return {
            "source": r.source,
            "title": r.title,
            "company": r.company,
            "url": r.url,
            "email": r.email,
            "region": r.region,
            "intent_score": r.intent_score,
            "match_score": r.match_score,
            "composite_score": r.composite_score,
            "is_scam": r.is_scam,
            "scam_reason": r.scam_reason,
            "dedup_key": r.dedup_key,
        }

    # ------------------------------------------------------------------
    # Enhancement: push every scanner to 100% readiness.
    # ------------------------------------------------------------------
    def enhance_to_max(self) -> Dict[str, Any]:
        """Mark every scanner active and force-load all modules to verify health."""
        for entry in self.scanner_registry:
            entry["active"] = True
            self._get_scanner(entry["name"], entry["module"])
        return self.get_scanner_health()

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """Compact telemetry for dashboards and websockets."""
        health = self.get_scanner_health()
        return {
            "readiness_percent": health["readiness_percent"],
            "healthy_scanners": health["healthy_scanners"],
            "total_scanners": health["total_scanners"],
            "last_full_scan": self._last_full_scan,
            "cache_ttl": self._cache_ttl,
        }


# Module-level singleton for reuse across routers/agents.
_engine: Optional[DeepScanEngine] = None


def get_deepscan_engine() -> DeepScanEngine:
    global _engine
    if _engine is None:
        _engine = DeepScanEngine()
    return _engine
