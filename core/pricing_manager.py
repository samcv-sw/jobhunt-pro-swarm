"""
pricing_manager.py - Clean pricing configuration for JobHunt Pro v2
4 tiers: Starter ($9), Basic ($19), Pro ($49), Enterprise/B2B ($149)
All payment buttons link to /register or /wallet for crypto payments.
"""

import contextlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

PRICING_TIERS = [
    {
        "tier": "starter",
        "name": "Starter",
        "companies": 200,
        "price_usd": 9,
        "original_price": 18,
        "description": "200 companies - Kickstart your campaign",
        "features": [
            "200 company applications",
            "AI tailored cover letters (Gemini + Groq)",
            "Live MX deliverability verification",
            "Basic email tracking",
            "Community support",
        ],
        "popular": False,
        "button_text": "Get Started – $9",
        "button_class": "btn-secondary",
        "highlight": False,
        "badge": "",
        "per_company": "$0.045",
    },
    {
        "tier": "basic",
        "name": "Basic",
        "companies": 300,
        "price_usd": 19,
        "original_price": 38,
        "description": "300 companies - Perfect for active seekers",
        "features": [
            "300 company applications",
            "AI tailored cover letters & CV tailoring",
            "Email tracking with open/click stats",
            "Follow-up automation (7 + 14 days)",
            "Conversion analytics dashboard",
            "Email support",
        ],
        "popular": True,
        "button_text": "Get Basic – $19",
        "button_class": "btn-primary",
        "highlight": True,
        "badge": "BEST VALUE",
        "per_company": "$0.063",
    },
    {
        "tier": "pro",
        "name": "Pro",
        "companies": 800,
        "price_usd": 49,
        "original_price": 98,
        "description": "800 companies - For serious job seekers",
        "features": [
            "800 company applications",
            "Everything in Basic",
            "200 swarm agents working for you",
            "20 email providers for higher deliverability",
            "Company research before each application",
            "Advanced analytics dashboard",
            "Priority support",
        ],
        "popular": False,
        "button_text": "Get Pro – $49",
        "button_class": "btn-secondary",
        "highlight": False,
        "badge": "POPULAR",
        "per_company": "$0.061",
    },
    {
        "tier": "enterprise",
        "name": "Enterprise / B2B SDR Swarm",
        "companies": 2500,
        "price_usd": 149,
        "original_price": 299,
        "description": "2,500 leads - Autonomous AI SDR Outreach Swarm & Team CRM",
        "conversion_headline": "سرب B2B SDR الأوتوماتيكي للوصول الفوري إلى 2,500 صانع قرار ومدير تنفيذي في الخليج",
        "features": [
            "2,500 company / lead applications",
            "Autonomous AI SDR cold outreach swarm",
            "Live MX verification & 365d deduplication",
            "Full CRM & webhook integration",
            "Custom AI model training",
            "Dedicated account manager",
            "SLA guarantee & full REST API access",
        ],
        "preview_hook": "/api/v2/b2b-leads/sample",
        "deliverability_guarantee": "100% Live MX Verified (0% Bounce SLA)",
        "supported_payment_methods": ["mada", "apple_pay", "visa_mastercard", "usdt_trc20", "usdt_bep20", "crypto_btc_eth_sol"],
        "popular": False,
        "button_text": "Get Enterprise – $149",
        "button_class": "btn-magenta",
        "highlight": False,
        "badge": "B2B & ENTERPRISE",
        "per_company": "$0.059",
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
    if not tier_name or not isinstance(tier_name, str):
        return None
    t_clean = tier_name.strip().lower()
    if t_clean in ("free", "starter"):
        return PRICING_TIERS[0]
    for t in PRICING_TIERS:
        if t["tier"].lower() == t_clean or t["name"].lower() == t_clean:
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

GCC_CURRENCIES: dict[str, dict[str, Any]] = {
    "SAR": {"rate": 3.75, "symbol": "ر.س", "symbol_en": "SAR", "name": "Saudi Riyal", "decimals": 0},
    "AED": {"rate": 3.67, "symbol": "د.إ", "symbol_en": "AED", "name": "UAE Dirham", "decimals": 0},
    "QAR": {"rate": 3.64, "symbol": "ر.ق", "symbol_en": "QAR", "name": "Qatari Riyal", "decimals": 0},
    "KWD": {"rate": 0.31, "symbol": "د.ك", "symbol_en": "KWD", "name": "Kuwaiti Dinar", "decimals": 2},
    "BHD": {"rate": 0.376, "symbol": "د.ب", "symbol_en": "BHD", "name": "Bahraini Dinar", "decimals": 2},
    "OMR": {"rate": 0.385, "symbol": "ر.ع", "symbol_en": "OMR", "name": "Omani Rial", "decimals": 2},
    "USD": {"rate": 1.0, "symbol": "$", "symbol_en": "USD", "name": "US Dollar", "decimals": 0},
    "EUR": {"rate": 0.92, "symbol": "€", "symbol_en": "EUR", "name": "Euro", "decimals": 0},
    "GBP": {"rate": 0.79, "symbol": "£", "symbol_en": "GBP", "name": "British Pound", "decimals": 0},
}

COUNTRY_TO_CURRENCY: dict[str, str] = {
    "SA": "SAR",
    "AE": "AED",
    "QA": "QAR",
    "KW": "KWD",
    "BH": "BHD",
    "OM": "OMR",
    "GB": "GBP",
    "US": "USD",
    "DE": "EUR",
    "FR": "EUR",
    "IT": "EUR",
    "ES": "EUR",
    "NL": "EUR",
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


def get_gcc_localized_pricing(country_code: str = "AE", preferred_currency: str | None = None) -> dict[str, Any]:
    """
    Returns pricing converted to local GCC/international currency with formatted labels in Arabic & English.
    """
    c_code = (country_code or "AE").upper().strip()
    currency_code = preferred_currency.upper().strip() if preferred_currency else COUNTRY_TO_CURRENCY.get(c_code, "USD")
    
    currency_meta = GCC_CURRENCIES.get(currency_code, GCC_CURRENCIES["USD"])
    rate = currency_meta["rate"]
    symbol_ar = currency_meta["symbol"]
    symbol_en = currency_meta["symbol_en"]
    decimals = currency_meta["decimals"]

    localized_tiers = []
    for tier in PRICING_TIERS:
        usd_price = tier["price_usd"]
        converted_raw = usd_price * rate
        converted_price = round(converted_raw, decimals) if decimals > 0 else int(round(converted_raw))
        
        orig_raw = tier.get("original_price", usd_price * 2) * rate
        converted_orig = round(orig_raw, decimals) if decimals > 0 else int(round(orig_raw))

        localized_tiers.append({
            **tier,
            "currency": currency_code,
            "currency_symbol_ar": symbol_ar,
            "currency_symbol_en": symbol_en,
            "converted_price": converted_price,
            "converted_original_price": converted_orig,
            "price_formatted_ar": f"{converted_price} {symbol_ar}",
            "price_formatted_en": f"{symbol_en} {converted_price}" if symbol_en != "$" else f"${converted_price}",
            "button_text_ar": f"اشترك الآن – {converted_price} {symbol_ar}",
            "button_text_en": f"Get {tier['name']} – {symbol_en} {converted_price}",
        })

    return {
        "success": True,
        "country_code": c_code,
        "currency": currency_code,
        "currency_code": currency_code,
        "currency_name": currency_meta["name"],
        "symbol_ar": symbol_ar,
        "symbol_en": symbol_en,
        "rate": rate,
        "exchange_rate_vs_usd": rate,
        "tiers": localized_tiers,
    }


def calculate_job_search_roi(
    target_monthly_salary_usd: float = 4000.0,
    manual_hours_per_week: float = 10.0,
    selected_tier: str = "pro"
) -> dict[str, Any]:
    """
    Calculates estimated time saved, financial value of time, and acceleration ROI multiplier.
    Helps prospective job seekers see the high ROI of using JobHunt Pro.
    """
    tier_info = get_tier_by_name(selected_tier) or PRICING_TIERS[2]  # Default Pro
    tier_cost = tier_info["price_usd"]

    # Target hourly rate assuming 160 hours/month
    hourly_rate = max(round(target_monthly_salary_usd / 160.0, 2), 10.0)
    
    # Monthly manual search time
    monthly_manual_hours = manual_hours_per_week * 4.2
    
    # JobHunt Pro automates ~92% of the search & dispatch time
    hours_saved_monthly = round(monthly_manual_hours * 0.92, 1)
    value_of_saved_time = round(hours_saved_monthly * hourly_rate, 2)
    
    # Standard manual search duration (average 16 weeks / 4 months) vs automated (approx 4-6 weeks)
    time_to_hire_acceleration_weeks = 8  # Saves 2 full months on average
    accelerated_earnings = round((time_to_hire_acceleration_weeks / 4.0) * target_monthly_salary_usd, 2)
    
    total_financial_benefit = round(value_of_saved_time + accelerated_earnings, 2)
    roi_multiplier = round(total_financial_benefit / max(tier_cost, 1.0), 1)

    return {
        "tier": tier_info["tier"],
        "tier_name": tier_info["name"],
        "tier_cost_usd": tier_cost,
        "target_monthly_salary_usd": target_monthly_salary_usd,
        "hourly_value_usd": hourly_rate,
        "hours_saved_monthly": hours_saved_monthly,
        "monthly_time_value_saved_usd": value_of_saved_time,
        "time_to_hire_acceleration_weeks": time_to_hire_acceleration_weeks,
        "accelerated_career_earnings_usd": accelerated_earnings,
        "total_financial_benefit_usd": total_financial_benefit,
        "roi_multiplier": roi_multiplier,
        "roi_headline": f"توفير {hours_saved_monthly} ساعة شهرياً وعائد استثماري يفوق {roi_multiplier}x ضعف التكلفة",
    }


def get_b2b_sdr_swarm_tier() -> dict[str, Any]:
    """Retrieve full configuration and conversion parameters for the B2B SDR Swarm tier ($149)."""
    return PRICING_TIERS[3]


def get_lead_magnet_config() -> dict[str, Any]:
    """Configuration for Free ATS Resume Scanner lead magnet & interactive preview widget."""
    return {
        "scanner_title_ar": "مقياس فحص السيرة الذاتية الذكي ATS مجاناً",
        "scanner_title_en": "Free AI ATS Resume & Career Gap Scanner",
        "badge": "100% Free • No Signup Required",
        "instant_scan_endpoint": "/api/v2/public/ats-instant-score",
        "preview_leads_endpoint": "/api/v2/b2b-leads/sample",
        "upsell_tiers": {
            "micro_service": {"name": "ATS Keyword Injection", "price_usd": 5, "checkout_url": "/checkout_v3?service=cv-keyword&amount=5"},
            "basic_seeker": {"name": "Basic 100 Companies + AI CV Polish", "price_usd": 19, "checkout_url": "/checkout_v3?plan=basic&amount=19"},
            "b2b_sdr_swarm": {"name": "B2B SDR Swarm (2,500 Leads)", "price_usd": 149, "checkout_url": "/checkout_v3?plan=enterprise&amount=149", "crypto_url": "/wallet?deposit=149&plan=enterprise"},
        },
        "supported_gateways": ["mada", "apple_pay", "visa_mastercard", "usdt_trc20", "crypto_btc_eth_sol"]
    }



