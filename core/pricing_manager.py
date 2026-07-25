"""
pricing_manager.py - Clean pricing configuration for JobHunt Pro v2
4 tiers: Free ($0), Basic ($5), Pro ($15), Enterprise ($50)
All payment buttons link to /register or /wallet for crypto payments.
"""

import contextlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

PRICING_TIERS = [
    {
        "tier": "free",
        "name": "Starter",
        "companies": 10,
        "price_usd": 2,
        "original_price": 4,
        "description": "10 companies - Start your campaign",
        "features": [
            "10 company applications",
            "AI cover letters",
            "Basic email tracking",
            "Community support",
        ],
        "popular": False,
        "button_text": "Get Started – $2",
        "button_class": "btn-secondary",
        "highlight": False,
        "badge": "",
        "per_company": "$0.20",
    },
    {
        "tier": "basic",
        "name": "Basic",
        "companies": 100,
        "price_usd": 5,
        "original_price": 10,
        "description": "100 companies - Perfect to start",
        "features": [
            "100 company applications",
            "AI cover letters (Gemini + Groq)",
            "Email tracking with open/click stats",
            "Follow-up automation (7 + 14 days)",
            "Basic analytics dashboard",
            "Email support",
        ],
        "popular": True,
        "button_text": "Get Basic – $5",
        "button_class": "btn-primary",
        "highlight": True,
        "badge": "BEST VALUE",
        "per_company": "$0.05",
    },
    {
        "tier": "pro",
        "name": "Pro",
        "companies": 500,
        "price_usd": 15,
        "original_price": 30,
        "description": "500 companies - For serious job seekers",
        "features": [
            "500 company applications",
            "Everything in Basic",
            "200 swarm agents working for you",
            "20 email providers for higher deliverability",
            "Company research before each application",
            "Advanced analytics dashboard",
            "Priority support",
        ],
        "popular": False,
        "button_text": "Get Pro – $15",
        "button_class": "btn-secondary",
        "highlight": False,
        "badge": "",
        "per_company": "$0.03",
    },
    {
        "tier": "enterprise",
        "name": "Enterprise",
        "companies": 2000,
        "price_usd": 50,
        "original_price": 100,
        "description": "2,000 companies - Maximum reach",
        "features": [
            "2,000 company applications",
            "Everything in Pro",
            "Custom AI model training",
            "Dedicated account manager",
            "SLA guarantee",
            "White-label option",
            "Full API access",
        ],
        "popular": False,
        "button_text": "Get Enterprise – $50",
        "button_class": "btn-magenta",
        "highlight": False,
        "badge": "PREMIUM",
        "per_company": "$0.025",
    },
]

# Import SERVICE_CATALOG directly to ensure 100% sync
from services.catalog import SERVICE_CATALOG, BOUQUET_CATALOG

SERVICE_PACKAGES = [
    {
        "package": s["id"],
        "name": s["name"],
        "price_usd": float(s["price"]),
        "features": s["features"],
        "what_they_get": s.get("what_they_get", s["description"]),
        "delivery": s.get("delivery", "instant")
    }
    for s in SERVICE_CATALOG
]

# Bundle definitions: which features are unlocked by each bouquet
BOUQUET_FEATURES = {
    "quick-strike": ["ats-dominator", "penetration-letter"],
    "pro-hunter": [
        "ats-dominator",
        "penetration-letter",
        "the-insider",
        "follow-up-trio",
        "linkedin-dominator",
    ],
    "the-king": [
        "ats-dominator",
        "the-insider",
        "penetration-letter",
        "follow-up-trio",
        "interview-arsenal",
        "warp-speed",
        "global-strike",
        "competition-radar",
        "mock-interview",
        "linkedin-dominator",
        "salary-negotiator",
        "career-agent",
    ],
    "mena-warlord": [
        "ats-dominator",
        "the-insider",
        "penetration-letter",
        "follow-up-trio",
        "interview-arsenal",
        "warp-speed",
        "global-strike",
        "competition-radar",
        "mock-interview",
        "linkedin-dominator",
        "salary-negotiator",
        "career-agent",
        "networking-missile",
        "mena-multilang",
    ],
    "god-mode": [
        "ats-dominator",
        "the-insider",
        "penetration-letter",
        "follow-up-trio",
        "interview-arsenal",
        "warp-speed",
        "global-strike",
        "competition-radar",
        "mock-interview",
        "linkedin-dominator",
        "salary-negotiator",
        "career-agent",
        "networking-missile",
        "interview-ninja",
        "mena-multilang",
    ],
}

BOUQUET_PACKAGES = [
    {
        "bouquet": "quick-strike",
        "name": "⚡ Quick Strike",
        "price_usd": 5,
        "description": "ATS Dominator + Penetration Letter — highest impact for $5",
        "includes": "2 weapons",
        "value": "$8",
        "savings": "40%",
        "icon": "⚡",
        "badge": "BUDGET",
    },
    {
        "bouquet": "pro-hunter",
        "name": "🦅 Pro Hunter V2",
        "price_usd": 25,
        "description": "4 weapons + LinkedIn Dominator — full application + profile dominance",
        "includes": "5 weapons",
        "value": "$28",
        "savings": "11%",
        "icon": "🦅",
        "badge": "MOST POPULAR",
    },
    {
        "bouquet": "the-king",
        "name": "👑 The Emperor",
        "price_usd": 69,
        "description": "12 weapons — ATS, interview, LinkedIn, salary, career agent — the complete arsenal",
        "includes": "12 weapons",
        "value": "$95",
        "savings": "27%",
        "icon": "👑",
        "badge": "",
    },
    {
        "bouquet": "mena-warlord",
        "name": "🇱🇧 MENA Warlord V2",
        "price_usd": 49,
        "description": "14 weapons: all features + Arabic/English/French translation + MENA networking",
        "includes": "14 weapons",
        "value": "$120",
        "savings": "59%",
        "icon": "🇱🇧",
        "badge": "REGIONAL KING",
    },
    {
        "bouquet": "god-mode",
        "name": "💀 God Mode V4",
        "price_usd": 99,
        "description": "ALL 15 weapons — including Interview Ninja live overlay. The ultimate job-hunting machine.",
        "includes": "15 weapons",
        "value": "$140",
        "savings": "29%",
        "icon": "💀",
        "badge": "ULTIMATE",
    },
]


# Map checkout service IDs (from services/catalog.py) to backend feature IDs (from SERVICE_PACKAGES)
CHECKOUT_SERVICE_MAPPING = {
    "cv-review": {"ats-dominator"},
    "email-template": {"penetration-letter"},
    "cover-letter-basic": {"penetration-letter"},
    "linkedin-headline": {"linkedin-dominator"},
    "job-alert-setup": {"competition-radar"},
    "skill-gap-report": {"ats-dominator"},
    "cv-optimization": {"ats-dominator"},
    "company-research": {"the-insider"},
    "followup-sequence": {"follow-up-trio"},
    "networking-plan": {"networking-missile"},
    "linkedin-optimization": {"linkedin-dominator"},
    "interview-prep": {"mock-interview", "interview-arsenal"},
    "career-consultation": {"career-agent"},
    "full-application-pack": {
        "ats-dominator",
        "the-insider",
        "penetration-letter",
        "follow-up-trio",
        "warp-speed",
        "global-strike",
    },
    "salary-negotiation": {"salary-negotiator"},
    "vip-support-month": {
        "ats-dominator",
        "the-insider",
        "penetration-letter",
        "follow-up-trio",
        "interview-arsenal",
        "warp-speed",
        "global-strike",
        "competition-radar",
        "mock-interview",
        "linkedin-dominator",
        "salary-negotiator",
        "career-agent",
        "networking-missile",
        "interview-ninja",
        "mena-multilang",
    },
}

# Map checkout bouquet IDs (from services/catalog.py) to backend feature IDs
CHECKOUT_BOUQUET_MAPPING = {
    "starter-pack": {"ats-dominator", "penetration-letter"},
    "linkedin-pack": {"linkedin-dominator"},
    "application-pack": {
        "ats-dominator",
        "the-insider",
        "penetration-letter",
        "follow-up-trio",
        "warp-speed",
        "global-strike",
    },
    "premium-pack": {
        "ats-dominator",
        "the-insider",
        "penetration-letter",
        "follow-up-trio",
        "warp-speed",
        "global-strike",
        "linkedin-dominator",
        "career-agent",
        "mock-interview",
        "interview-arsenal",
    },
    "vip-month": {
        "ats-dominator",
        "the-insider",
        "penetration-letter",
        "follow-up-trio",
        "interview-arsenal",
        "warp-speed",
        "global-strike",
        "competition-radar",
        "mock-interview",
        "linkedin-dominator",
        "salary-negotiator",
        "career-agent",
        "networking-missile",
        "interview-ninja",
        "mena-multilang",
    },
}


def get_unlocked_features(user_id: str) -> set:
    """Return the set of feature IDs unlocked by user's purchases (services + bouquets)."""
    unlocked = set()
    import os
    import sys
    from pathlib import Path

    if os.getenv("FORCE_PG") == "1" or os.getenv("CLOUD_MODE") == "true":
        try:
            import core.pg_sqlite_shim as sqlite3
        except ImportError:
            import sqlite3
    else:
        import sqlite3

    db_path = "jobhunt_saas_v2.db"
    try:
        root_dir = str(Path(__file__).resolve().parent.parent)
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        import config

        db_path = getattr(config, "DB_PATH", "jobhunt_saas_v2.db")
    except Exception:
        pass

    if not os.path.isabs(db_path):
        db_path = os.path.join(str(Path(__file__).resolve().parent.parent), db_path)

    if not os.path.exists(db_path):
        db_path = "jobhunt_saas_v2.db"

    conn = None
    try:
        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        purchases = conn.execute(
            "SELECT package_id, service_type FROM purchased_services WHERE user_id = ? AND status = 'active'",
            (user_id,),
        ).fetchall()
        for p in purchases:
            pid = p["package_id"]
            stype = p["service_type"]

            # Apply checkout mappings first, falling back to direct names
            if stype == "service":
                if pid in CHECKOUT_SERVICE_MAPPING:
                    unlocked.update(CHECKOUT_SERVICE_MAPPING[pid])
                else:
                    unlocked.add(pid)
            elif stype == "bouquet":
                if pid in CHECKOUT_BOUQUET_MAPPING:
                    unlocked.update(CHECKOUT_BOUQUET_MAPPING[pid])
                elif pid in BOUQUET_FEATURES:
                    unlocked.update(BOUQUET_FEATURES[pid])
    except Exception as e:
        logger.error(
            f"[pricing_manager] Failed to query purchased services for {user_id}: {e}"
        )
    finally:
        if conn:
            with contextlib.suppress(Exception):
                conn.close()
    return unlocked


import functools


@functools.lru_cache(maxsize=1)
def get_all_pricing() -> dict[str, Any]:
    """Return all pricing info combined (Cached for Zero-Latency)."""
    return {
        "tiers": PRICING_TIERS,
        "services": SERVICE_PACKAGES,
        "bouquets": BOUQUET_PACKAGES,
    }


def get_tier_by_name(tier_name: str) -> dict[str, Any] | None:
    """Get tier details by name."""
    for t in PRICING_TIERS:
        if t["tier"] == tier_name:
            return t
    return None


def get_tier_by_company_count(company_count: int) -> dict[str, Any] | None:
    """Get tier details by company count."""
    for t in PRICING_TIERS:
        if t["companies"] == company_count:
            return t
    return None


def calculate_daily_reward(tier_name: str) -> int:
    """Calculate daily email reward based on tier."""
    tier_map = {
        "free": 5,
        "starter": 5,
        "basic": 25,
        "pro": 100,
        "enterprise": 200,
    }
    t_clean = tier_name.strip().lower() if isinstance(tier_name, str) else ""
    return tier_map.get(t_clean, 5)


def get_pricing_json() -> dict[str, Any]:
    """Get pricing as clean JSON for API responses."""
    return {
        "success": True,
        "data": get_all_pricing(),
        "total_tiers": len(PRICING_TIERS),
    }

PPP_DISCOUNTS = {
    "LB": 0.50,  # Lebanon: 50% PPP discount
    "EG": 0.50,  # Egypt: 50% PPP discount
    "IN": 0.40,  # India: 40% PPP discount
    "PK": 0.40,  # Pakistan: 40% PPP discount
    "PH": 0.40,  # Philippines: 40% PPP discount
    "NG": 0.50,  # Nigeria: 50% PPP discount
    "KE": 0.40,  # Kenya: 40% PPP discount
}

def get_ppp_adjusted_pricing(country_code: str = "US") -> dict[str, Any]:
    """Calculate location-adjusted pricing based on country PPP multiplier."""
    c_code = (country_code or "US").upper().strip()
    discount_rate = PPP_DISCOUNTS.get(c_code, 0.0)
    multiplier = 1.0 - discount_rate

    adjusted_tiers = []
    for tier in PRICING_TIERS:
        adj_price = round(tier["price_usd"] * multiplier, 2)
        adjusted_tiers.append({
            **tier,
            "ppp_country": c_code,
            "ppp_discount_pct": int(discount_rate * 100),
            "adjusted_price_usd": adj_price,
            "button_text": f"Get {tier['name']} – ${adj_price}" if adj_price > 0 else tier["button_text"]
        })

    return {
        "country": c_code,
        "ppp_discount_applied": discount_rate > 0,
        "discount_percentage": int(discount_rate * 100),
        "tiers": adjusted_tiers,
    }

