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

SERVICE_PACKAGES = [
    # --- V3 Weapons ---
    {
        "package": "ats-dominator",
        "name": "🧠 ATS++ Keyword Dominator",
        "price_usd": 5,
        "description": "Scans job descriptions → rewrites your CV with exact keywords → 2.6x higher ATS pass rate",
        "icon": "🧠",
        "result": "+160% ATS pass rate",
    },
    {
        "package": "the-insider",
        "name": "🕵️ The Insider",
        "price_usd": 5,
        "description": "Real-time company intel: financials, Glassdoor, news, CEO, culture → personalized application",
        "icon": "🕵️",
        "result": "Stand out with insider knowledge",
    },
    {
        "package": "penetration-letter",
        "name": "✍️ Penetration Letter",
        "price_usd": 3,
        "description": "Cover letter that name-drops company news + aligns your skills to THEIR pain points",
        "icon": "✍️",
        "result": "5x more likely to be read",
    },
    {
        "package": "follow-up-trio",
        "name": "📬 The 3-Tap Follow-Up",
        "price_usd": 5,
        "description": "Day 3 gentle → Day 7 value-add → Day 14 closing. Auto-scheduled, different tone each",
        "icon": "📬",
        "result": "3 extra chances to land interview",
    },
    {
        "package": "interview-arsenal",
        "name": "🎙️ Interview Arsenal",
        "price_usd": 10,
        "description": "15+ predicted questions with model answers → tech + behavioral + company-specific",
        "icon": "🎙️",
        "result": "Walk in fully prepared",
    },
    {
        "package": "warp-speed",
        "name": "⚡ Warp Speed",
        "price_usd": 8,
        "description": "Llama 70B AI (9x smarter) + priority processing queue → 3x faster, higher quality",
        "icon": "⚡",
        "result": "Smarter AI, no waiting",
    },
    {
        "package": "global-strike",
        "name": "🌍 Global Strike",
        "price_usd": 10,
        "description": "Multi-platform auto-apply: LinkedIn Easy Apply + company portals + job boards at once",
        "icon": "🌍",
        "result": "3x more applications",
    },
    {
        "package": "competition-radar",
        "name": "👁️ Competition Radar",
        "price_usd": 7,
        "description": "Analyzes who else applied → ranks YOUR odds → tells you where you win",
        "icon": "👁️",
        "result": "Apply where you have the edge",
    },
    # --- V4 Weapons (NEW) ---
    {
        "package": "mock-interview",
        "name": "🎭 Mock Interview AI",
        "price_usd": 15,
        "description": "Interactive voice/video interview simulator → AI grades answers, flags weaknesses, suggests improvements",
        "icon": "🎭",
        "result": "Ace every interview",
    },
    {
        "package": "linkedin-dominator",
        "name": "🔗 LinkedIn Dominator",
        "price_usd": 10,
        "description": "AI rewrites entire LinkedIn profile: headline, About, Skills, Experience → keyword-optimized for recruiters",
        "icon": "🔗",
        "result": "5x more recruiter InMails",
    },
    {
        "package": "salary-negotiator",
        "name": "💸 Salary Negotiator",
        "price_usd": 8,
        "description": "Real-time market salary data + custom negotiation scripts + counter-offer email generator",
        "icon": "💸",
        "result": "Get paid what you're worth",
    },
    {
        "package": "career-agent",
        "name": "🧠 Career Agent 24/7",
        "price_usd": 12,
        "description": "AI chatbot that knows your CV, target market, skills → answers any career question instantly",
        "icon": "🧠",
        "result": "Your personal career advisor",
    },
    {
        "package": "networking-missile",
        "name": "🎯 Networking Missile",
        "price_usd": 7,
        "description": "Auto-finds hiring managers → crafts personalized LinkedIn messages → tracks response rates",
        "icon": "🎯",
        "result": "Turn strangers into interviews",
    },
    {
        "package": "interview-ninja",
        "name": "🥷 Interview Ninja",
        "price_usd": 20,
        "description": "Live browser overlay during video interviews → real-time answer prompts + anti-ramble detection",
        "icon": "🥷",
        "result": "Secret weapon in live interviews",
    },
    {
        "package": "mena-multilang",
        "name": "🌍 MENA Multi-Lang Pro",
        "price_usd": 5,
        "description": "Professional CV + cover letter translation: Arabic ↔ English ↔ French, culturally adapted",
        "icon": "🌍",
        "result": "Dominate MENA & Gulf market",
    },
    # --- Follow-Up Automation (PAID add-on) ---
    {
        "package": "follow-up-automation-starter",
        "name": "📬 Follow-Up Automation – Starter",
        "price_usd": 4.99,
        "description": "Up to 50 AI follow-ups per campaign. Day 3 + Day 7 auto follow-ups with Groq AI messages. Boosts response rate +40%.",
        "icon": "📬",
        "result": "+40% response rate",
        "tier": "starter",
        "max_followups": 50,
    },
    {
        "package": "follow-up-automation-pro",
        "name": "📬 Follow-Up Automation – Pro",
        "price_usd": 19.99,
        "description": "Up to 200 AI follow-ups per campaign. Full 2-cycle automation with personalized Groq AI messages. +65% response rate.",
        "icon": "📬",
        "result": "+65% response rate",
        "tier": "pro",
        "max_followups": 200,
    },
    {
        "package": "follow-up-automation-enterprise",
        "name": "📬 Follow-Up Automation – Enterprise",
        "price_usd": 49.99,
        "description": "Up to 500 AI follow-ups per campaign. Maximum coverage with priority AI + multi-tone follow-up cycles.",
        "icon": "📬",
        "result": "+85% response rate",
        "tier": "enterprise",
        "max_followups": 500,
    },
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

