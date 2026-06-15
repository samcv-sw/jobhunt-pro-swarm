"""
pricing_manager.py - Clean pricing configuration for JobHunt Pro v2
4 tiers: Free ($0), Basic ($5), Pro ($15), Enterprise ($50)
All payment buttons link to /register or /wallet for crypto payments.
"""
from typing import List, Dict, Any, Optional

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
    {"package": "ats-dominator", "name": "🧠 ATS++ Keyword Dominator", "price_usd": 5, "description": "Scans job descriptions → rewrites your CV with exact keywords → 2.6x higher ATS pass rate", "icon": "🧠", "result": "+160% ATS pass rate"},
    {"package": "the-insider", "name": "🕵️ The Insider", "price_usd": 5, "description": "Real-time company intel: financials, Glassdoor, news, CEO, culture → personalized application", "icon": "🕵️", "result": "Stand out with insider knowledge"},
    {"package": "penetration-letter", "name": "✍️ Penetration Letter", "price_usd": 3, "description": "Cover letter that name-drops company news + aligns your skills to THEIR pain points", "icon": "✍️", "result": "5x more likely to be read"},
    {"package": "follow-up-trio", "name": "📬 The 3-Tap Follow-Up", "price_usd": 5, "description": "Day 3 gentle → Day 7 value-add → Day 14 closing. Auto-scheduled, different tone each", "icon": "📬", "result": "3 extra chances to land interview"},
    {"package": "interview-arsenal", "name": "🎙️ Interview Arsenal", "price_usd": 10, "description": "15+ predicted questions with model answers → tech + behavioral + company-specific", "icon": "🎙️", "result": "Walk in fully prepared"},
    {"package": "warp-speed", "name": "⚡ Warp Speed", "price_usd": 8, "description": "Llama 70B AI (9x smarter) + priority processing queue → 3x faster, higher quality", "icon": "⚡", "result": "Smarter AI, no waiting"},
    {"package": "global-strike", "name": "🌍 Global Strike", "price_usd": 10, "description": "Multi-platform auto-apply: LinkedIn Easy Apply + company portals + job boards at once", "icon": "🌍", "result": "3x more applications"},
    {"package": "competition-radar", "name": "👁️ Competition Radar", "price_usd": 7, "description": "Analyzes who else applied → ranks YOUR odds → tells you where you win", "icon": "👁️", "result": "Apply where you have the edge"},
    # --- V4 Weapons (NEW) ---
    {"package": "mock-interview", "name": "🎭 Mock Interview AI", "price_usd": 15, "description": "Interactive voice/video interview simulator → AI grades answers, flags weaknesses, suggests improvements", "icon": "🎭", "result": "Ace every interview"},
    {"package": "linkedin-dominator", "name": "🔗 LinkedIn Dominator", "price_usd": 10, "description": "AI rewrites entire LinkedIn profile: headline, About, Skills, Experience → keyword-optimized for recruiters", "icon": "🔗", "result": "5x more recruiter InMails"},
    {"package": "salary-negotiator", "name": "💸 Salary Negotiator", "price_usd": 8, "description": "Real-time market salary data + custom negotiation scripts + counter-offer email generator", "icon": "💸", "result": "Get paid what you're worth"},
    {"package": "career-agent", "name": "🧠 Career Agent 24/7", "price_usd": 12, "description": "AI chatbot that knows your CV, target market, skills → answers any career question instantly", "icon": "🧠", "result": "Your personal career advisor"},
    {"package": "networking-missile", "name": "🎯 Networking Missile", "price_usd": 7, "description": "Auto-finds hiring managers → crafts personalized LinkedIn messages → tracks response rates", "icon": "🎯", "result": "Turn strangers into interviews"},
    {"package": "interview-ninja", "name": "🥷 Interview Ninja", "price_usd": 20, "description": "Live browser overlay during video interviews → real-time answer prompts + anti-ramble detection", "icon": "🥷", "result": "Secret weapon in live interviews"},
    {"package": "mena-multilang", "name": "🌍 MENA Multi-Lang Pro", "price_usd": 5, "description": "Professional CV + cover letter translation: Arabic ↔ English ↔ French, culturally adapted", "icon": "🌍", "result": "Dominate MENA & Gulf market"},
    # --- Follow-Up Automation (PAID add-on) ---
    {"package": "follow-up-automation-starter", "name": "📬 Follow-Up Automation – Starter", "price_usd": 4.99, "description": "Up to 50 AI follow-ups per campaign. Day 3 + Day 7 auto follow-ups with Groq AI messages. Boosts response rate +40%.", "icon": "📬", "result": "+40% response rate", "tier": "starter", "max_followups": 50},
    {"package": "follow-up-automation-pro", "name": "📬 Follow-Up Automation – Pro", "price_usd": 19.99, "description": "Up to 200 AI follow-ups per campaign. Full 2-cycle automation with personalized Groq AI messages. +65% response rate.", "icon": "📬", "result": "+65% response rate", "tier": "pro", "max_followups": 200},
    {"package": "follow-up-automation-enterprise", "name": "📬 Follow-Up Automation – Enterprise", "price_usd": 49.99, "description": "Up to 500 AI follow-ups per campaign. Maximum coverage with priority AI + multi-tone follow-up cycles.", "icon": "📬", "result": "+85% response rate", "tier": "enterprise", "max_followups": 500},
]

# Bundle definitions: which features are unlocked by each bouquet
BOUQUET_FEATURES = {
    "quick-strike": ["ats-dominator", "penetration-letter"],
    "pro-hunter": ["ats-dominator", "penetration-letter", "the-insider", "follow-up-trio", "linkedin-dominator"],
    "the-king": ["ats-dominator", "the-insider", "penetration-letter", "follow-up-trio", "interview-arsenal", "warp-speed", "global-strike", "competition-radar", "mock-interview", "linkedin-dominator", "salary-negotiator", "career-agent"],
    "mena-warlord": ["ats-dominator", "the-insider", "penetration-letter", "follow-up-trio", "interview-arsenal", "warp-speed", "global-strike", "competition-radar", "mock-interview", "linkedin-dominator", "salary-negotiator", "career-agent", "networking-missile", "mena-multilang"],
    "god-mode": ["ats-dominator", "the-insider", "penetration-letter", "follow-up-trio", "interview-arsenal", "warp-speed", "global-strike", "competition-radar", "mock-interview", "linkedin-dominator", "salary-negotiator", "career-agent", "networking-missile", "interview-ninja", "mena-multilang"],
}

BOUQUET_PACKAGES = [
    {"bouquet": "quick-strike", "name": "⚡ Quick Strike", "price_usd": 5, "description": "ATS Dominator + Penetration Letter — highest impact for $5", "includes": "2 weapons", "value": "$8", "savings": "40%", "icon": "⚡", "badge": "BUDGET"},
    {"bouquet": "pro-hunter", "name": "🦅 Pro Hunter V2", "price_usd": 25, "description": "4 weapons + LinkedIn Dominator — full application + profile dominance", "includes": "5 weapons", "value": "$28", "savings": "11%", "icon": "🦅", "badge": "MOST POPULAR"},
    {"bouquet": "the-king", "name": "👑 The Emperor", "price_usd": 69, "description": "12 weapons — ATS, interview, LinkedIn, salary, career agent — the complete arsenal", "includes": "12 weapons", "value": "$95", "savings": "27%", "icon": "👑", "badge": ""},
    {"bouquet": "mena-warlord", "name": "🇱🇧 MENA Warlord V2", "price_usd": 49, "description": "14 weapons: all features + Arabic/English/French translation + MENA networking", "includes": "14 weapons", "value": "$120", "savings": "59%", "icon": "🇱🇧", "badge": "REGIONAL KING"},
    {"bouquet": "god-mode", "name": "💀 God Mode V4", "price_usd": 99, "description": "ALL 15 weapons — including Interview Ninja live overlay. The ultimate job-hunting machine.", "includes": "15 weapons", "value": "$140", "savings": "29%", "icon": "💀", "badge": "ULTIMATE"},
]


def get_unlocked_features(user_id: str) -> set:
    """Return the set of feature IDs unlocked by user's purchases (services + bouquets)."""
    unlocked = set()
    try:
        from database import SessionLocal
        db = SessionLocal()
        try:
            purchases = db.execute(
                db.text("SELECT package_id, service_type FROM purchased_services WHERE user_id = :uid AND status = 'active'"),
                {"uid": user_id}
            ).fetchall()
            for p in purchases:
                pid = p[0]
                stype = p[1]
                if stype == "service":
                    unlocked.add(pid)  # direct feature: ats-dominator, the-insider, etc.
                elif stype == "bouquet":
                    # expand bouquet into its features
                    features = BOUQUET_FEATURES.get(pid, [])
                    unlocked.update(features)
        finally:
            db.close()
    except Exception:
        pass
    return unlocked


def get_all_pricing() -> Dict[str, Any]:
    """Return all pricing info combined."""
    return {
        "tiers": PRICING_TIERS,
        "services": SERVICE_PACKAGES,
        "bouquets": BOUQUET_PACKAGES,
    }


def get_tier_by_name(tier_name: str) -> Optional[Dict[str, Any]]:
    """Get tier details by name."""
    for t in PRICING_TIERS:
        if t["tier"] == tier_name:
            return t
    return None


def get_tier_by_company_count(company_count: int) -> Optional[Dict[str, Any]]:
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
    if isinstance(tier_name, str):
        t_clean = tier_name.strip().lower()
    else:
        t_clean = ""
    return tier_map.get(t_clean, 5)


def get_pricing_json() -> Dict[str, Any]:
    """Get pricing as clean JSON for API responses."""
    return {
        "success": True,
        "data": get_all_pricing(),
        "total_tiers": len(PRICING_TIERS),
    }
