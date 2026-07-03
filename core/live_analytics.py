"""
JobHunt Pro - Live Analytics Dashboard v1.0
Real-time stats API for landing page live counters + social proof.
"""

import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
DATA_DIR = None
STATE_FILE = None

# Base counters (seeded for realism, auto-increment on each call)
_state = {
    "total_applications": 2483700,
    "total_users": 8920,
    "active_campaigns_today": 342,
    "cover_letters_generated": 156000,
    "jobs_matched_today": 28750,
    "interviews_landed_this_week": 1280,
    "countries_active": 54,
    "ai_agents_running": 200,
    "applications_per_second": 4.7,
    "last_updated": "",
}


def init(data_dir: str = None):
    global DATA_DIR, STATE_FILE
    if data_dir:
        DATA_DIR = Path(data_dir)
    else:
        DATA_DIR = Path(__file__).parent.parent / "data"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE = DATA_DIR / "live_stats.json"
    _load_state()


def _load_state():
    global _state
    if STATE_FILE and STATE_FILE.exists():
        try:
            saved = json.load(open(STATE_FILE))
            _state.update(saved)
        except Exception:
            pass


def _save_state():
    if STATE_FILE:
        _state["last_updated"] = datetime.utcnow().isoformat()
        json.dump(_state, open(STATE_FILE, "w"), indent=2)


def get_live_stats() -> dict:
    """Return live-updating stats for the landing page."""
    now = time.time()
    since_update = now - _state.get("_last_tick", now)

    # Auto-increment counters
    _state["total_applications"] += int(since_update * random.uniform(3, 7))
    _state["jobs_matched_today"] += int(since_update * random.uniform(0.5, 2))
    _state["cover_letters_generated"] += int(since_update * random.uniform(1, 3))
    _state["_last_tick"] = now

    _save_state()

    return {
        "total_applications": f"{_state['total_applications']:,}",
        "total_users": f"{_state['total_users']:,}",
        "active_campaigns_today": _state["active_campaigns_today"],
        "cover_letters_generated": f"{_state['cover_letters_generated']:,}",
        "jobs_matched_today": f"{_state['jobs_matched_today']:,}",
        "interviews_landed_this_week": f"{_state['interviews_landed_this_week']:,}",
        "countries_active": _state["countries_active"],
        "ai_agents_running": _state["ai_agents_running"],
        "applications_per_second": round(
            _state["applications_per_second"] + random.uniform(-0.5, 0.5), 1
        ),
    }
