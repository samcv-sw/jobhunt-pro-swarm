"""
DeepScan — Autonomous Omni-Scanning Enhancement Engine for JobHunt Pro.

DeepScan is the unified, self-optimizing scanning super-layer that orchestrates,
enhances, and amplifies every existing scanning/analysis tool in the JobHunt Pro
ecosystem. It provides:

    1. Unified Orchestration  — one entry point for all scanners.
    2. Power Rating Engine    — quantifies total system power as a percentage.
    3. Profit Forecaster      — projects revenue from every monetizable scanner.
    4. Self-Healing Audit     — detects dead/weak scanners and auto-repairs them.
    5. 10/10 Enhancement Loop — continuously pushes every metric to 100%.

DeepScan is designed to be imported and used by the FastAPI backend, the
Telegram bot, the Chrome extension, and any autonomous agent swarm.
"""

from deepscan.engine import DeepScanEngine
from deepscan.power_rating import PowerRatingEngine
from deepscan.profit_forecaster import ProfitForecaster
from deepscan.self_healer import SelfHealingAuditor

__all__ = [
    "DeepScanEngine",
    "PowerRatingEngine",
    "ProfitForecaster",
    "SelfHealingAuditor",
]

__version__ = "1.0.0"
