"""
pricing_tiers.py - Pricing configuration for JobHunt Pro v15
"""

# Job application pricing tiers (NO FREE TIER - minimum $2 via crypto)
PRICING_TIERS = [
    {"tier": "starter", "name": "Starter", "companies": 10, "price_usd": 2, "description": "10 companies - $2 one-time (crypto/USDT)"},
    {"tier": "basic", "name": "Basic", "companies": 100, "price_usd": 5, "description": "100 companies - $5 one-time (crypto/USDT)"},
    {"tier": "pro", "name": "Pro", "companies": 500, "price_usd": 15, "description": "500 companies - $15 one-time (crypto/USDT)"},
    {"tier": "enterprise", "name": "Enterprise", "companies": 2000, "price_usd": 50, "description": "2000 companies - $50 one-time (crypto/USDT)"},
]

# Service packages (a la carte)
SERVICE_PACKAGES = [
    {"package": "cv-only", "name": "CV Optimization", "price_usd": 5, "description": "Professional CV review and optimization"},
    {"package": "cover-only", "name": "Cover Letter", "price_usd": 3, "description": "AI-generated personalized cover letter"},
    {"package": "email-only", "name": "Email Template", "price_usd": 2, "description": "Professional email template"},
    {"package": "linkedin-opt", "name": "LinkedIn Optimization", "price_usd": 10, "description": "LinkedIn profile makeover"},
    {"package": "interview-prep", "name": "Interview Prep", "price_usd": 12, "description": "AI interview coaching session"},
    {"package": "salary-negotiation", "name": "Salary Negotiation", "price_usd": 15, "description": "AI salary negotiation coaching"},
    {"package": "portfolio-review", "name": "Portfolio Review", "price_usd": 4, "description": "Professional portfolio review"},
    {"package": "networking-strategy", "name": "Networking Strategy", "price_usd": 8, "description": "Personalized networking plan"},
    {"package": "career-consultation", "name": "Career Consultation", "price_usd": 20, "description": "1-on-1 career strategy session"},
    {"package": "job-search-plan", "name": "Job Search Plan", "price_usd": 12, "description": "Custom job search action plan"},
    {"package": "company-research", "name": "Company Research", "price_usd": 5, "description": "Deep company analysis report"},
    {"package": "application-review", "name": "Application Review", "price_usd": 6, "description": "Review and improve applications"},
    {"package": "follow-up-sequence", "name": "Follow-up Sequence", "price_usd": 5, "description": "Automated follow-up emails"},
    {"package": "response-tracker", "name": "Response Tracker", "price_usd": 4, "description": "Track and analyze responses"},
    {"package": "premium-support", "name": "Premium Support", "price_usd": 8, "description": "Priority customer support"},
    {"package": "custom-report", "name": "Custom Report", "price_usd": 10, "description": "Detailed job market analysis"},
]

# Bouquet packages (bundles)
BOUQUET_PACKAGES = [
    {"bouquet": "starter-pack", "name": "Starter Pack", "price_usd": 5, "description": "Everything to start your job hunt"},
    {"bouquet": "job-hunter-pack", "name": "Job Hunter Pack", "price_usd": 15, "description": "Serious job hunting package"},
    {"bouquet": "career-launcher-pack", "name": "Career Launcher Pack", "price_usd": 15, "description": "Launch your career"},
    {"bouquet": "executive-pack", "name": "Executive Pack", "price_usd": 50, "description": "Premium executive job search"},
    {"bouquet": "full-service-pack", "name": "Full Service Pack", "price_usd": 50, "description": "Complete job search service"},
    {"bouquet": "cv-cover-pack", "name": "CV + Cover Letter", "price_usd": 5, "description": "Essential application materials"},
    {"bouquet": "interview-ready-pack", "name": "Interview Ready Pack", "price_usd": 10, "description": "Everything for interview success"},
    {"bouquet": "networking-pack", "name": "Networking Pack", "price_usd": 12, "description": "Build your professional network"},
    {"bouquet": "premium-career-pack", "name": "Premium Career Pack", "price_usd": 40, "description": "Full career transformation"},
    {"bouquet": "remote-job-pack", "name": "Remote Job Pack", "price_usd": 18, "description": "Find remote work opportunities"},
    {"bouquet": "mena-pack", "name": "MENA Region Pack", "price_usd": 12, "description": "Specialized for Middle East market"},
    {"bouquet": "tech-pack", "name": "Tech Industry Pack", "price_usd": 15, "description": "Tailored for tech professionals"},
    {"bouquet": "finance-pack", "name": "Finance Pack", "price_usd": 10, "description": "For banking and finance roles"},
    {"bouquet": "healthcare-pack", "name": "Healthcare Pack", "price_usd": 18, "description": "Healthcare industry specific"},
    {"bouquet": "engineering-pack", "name": "Engineering Pack", "price_usd": 16, "description": "For engineering professionals"},
    {"bouquet": "marketing-pack", "name": "Marketing Pack", "price_usd": 14, "description": "Marketing and creative roles"},
    {"bouquet": "education-pack", "name": "Education Pack", "price_usd": 12, "description": "Teaching and education roles"},
    {"bouquet": "graduate-pack", "name": "Graduate Pack", "price_usd": 5, "description": "For fresh graduates"},
    {"bouquet": "career-switch-pack", "name": "Career Switch Pack", "price_usd": 15, "description": "Change your career path"},
    {"bouquet": "leadership-pack", "name": "Leadership Pack", "price_usd": 10, "description": "For C-level and leadership"},
    {"bouquet": "ultimate-pack", "name": "Ultimate Pack", "price_usd": 50, "description": "The complete job search solution"},
]

def get_all_pricing():
    return {"tiers": PRICING_TIERS, "services": SERVICE_PACKAGES, "bouquets": BOUQUET_PACKAGES}

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

def get_tier_by_name(tier_name):
    for t in PRICING_TIERS:
        if t["tier"] == tier_name:
            return t
    return PRICING_TIERS[0]
