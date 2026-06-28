"""
JobHunt Pro — Service Catalog v2
Micro-services priced $2–$20 for instant automated delivery
Each service has: id, name, price, description, delivery_time, features, fulfillment_func
"""
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

SERVICE_CATALOG = [
    # ═══════════════════════════════════════════
    # TIER 1: MICRO ($2 - $5) — Instant digital
    # ═══════════════════════════════════════════
    {
        "id": "cv-review",
        "name": "CV Review & Score",
        "price": 2,
        "description": "AI-powered CV analysis — get a score out of 100 with specific improvement tips",
        "delivery": "instant",
        "features": ["ATS compatibility score", "Keyword gap analysis", "Format suggestions", "Section-by-section feedback"],
        "what_they_get": "PDF report with score, 10+ improvement suggestions, keyword optimization list",
    },
    {
        "id": "email-template",
        "name": "Professional Email Template",
        "price": 2,
        "description": "Custom-written cold email template for job applications that gets responses",
        "delivery": "instant",
        "features": ["Subject line A/B tested", "Body template", "Follow-up template", "Call-to-action optimized"],
        "what_they_get": "3 email templates (initial + 2 follow-ups) in plain text + HTML format",
    },
    {
        "id": "cover-letter-basic",
        "name": "Cover Letter (Basic)",
        "price": 3,
        "description": "AI-generated cover letter tailored to their target job title and industry",
        "delivery": "instant",
        "features": ["Personalized opening", "Skills highlight section", "Professional closing", "PDF + DOCX format"],
        "what_they_get": "Ready-to-use cover letter in their name, 2-3 paragraphs, PDF format",
    },
    {
        "id": "linkedin-headline",
        "name": "LinkedIn Headline & Bio",
        "price": 3,
        "description": "Optimized LinkedIn headline and about section to attract recruiters",
        "delivery": "instant",
        "features": ["SEO-optimized headline", "Recruiter-focused summary", "Keyword rich", "Character-count optimized"],
        "what_they_get": "3 headline variants + 150-word About section + hashtag recommendations",
    },
    {
        "id": "job-alert-setup",
        "name": "Job Alert Automation",
        "price": 4,
        "description": "Set up 24/7 automated job alerts across multiple platforms",
        "delivery": "1 hour",
        "features": ["Monitors 5+ job boards", "Real-time notifications", "Apply-ready alerts", "Filters by salary/location"],
        "what_they_get": "30 days of automated job monitoring with daily email digests",
    },
    {
        "id": "skill-gap-report",
        "name": "Skills Gap Report",
        "price": 4,
        "description": "AI analyzes their CV against 100+ target job listings to find missing skills",
        "delivery": "instant",
        "features": ["Market demand analysis", "Missing certification detection", "Priority skill ranking", "Learning roadmap"],
        "what_they_get": "PDF report with top-10 missing skills, certification recommendations, 3-month learning plan",
    },
    {
        "id": "response-tracker",
        "name": "Application Response Tracker",
        "price": 4,
        "description": "Track every application, follow-up, and response in a dashboard",
        "delivery": "instant",
        "features": ["Real-time status tracking", "Follow-up reminders", "Response analytics", "Export to CSV"],
        "what_they_get": "7 days access to tracking dashboard with all their applications monitored",
    },
    {
        "id": "cv-optimization",
        "name": "CV Keyword Optimization",
        "price": 5,
        "description": "Rewrite their CV with recruiter-optimized keywords for ATS systems",
        "delivery": "instant",
        "features": ["ATS keyword injection", "Role-specific optimization", "Action verb enhancement", "Quantified achievements"],
        "what_they_get": "Optimized CV file with ATS score report showing before/after comparison",
    },

    # ═══════════════════════════════════════════
    # TIER 2: STANDARD ($5 - $10) — 24h delivery
    # ═══════════════════════════════════════════
    {
        "id": "company-research",
        "name": "Company Research Report",
        "price": 5,
        "description": "Deep-dive research on 5 target companies including culture, hiring, and decision-makers",
        "delivery": "24 hours",
        "features": ["Company culture analysis", "Hiring team identified", "Recent news/trends", "Interview question prep"],
        "what_they_get": "5 company profiles with key contacts, recent hiring patterns, and tailored interview tips",
    },
    {
        "id": "followup-sequence",
        "name": "Automated Follow-up Sequence",
        "price": 5,
        "description": "3-email automated follow-up sequence sent over 30 days after each application",
        "delivery": "instant",
        "features": ["3 professionally written emails", "Timed at 7/14/30 days", "Tracked opens/clicks", "A/B tested subject lines"],
        "what_they_get": "Lifetime automated follow-ups for ALL their applications (3 emails each, 30-day cycle)",
    },
    {
        "id": "application-review",
        "name": "Application Quality Review",
        "price": 6,
        "description": "Review their last 5 applications and provide specific improvement feedback",
        "delivery": "24 hours",
        "features": ["Email quality analysis", "CV alignment check", "Cover letter critique", "Score and recommendations"],
        "what_they_get": "5 scored application reviews with specific fixes for each",
    },
    {
        "id": "networking-plan",
        "name": "Personalized Networking Plan",
        "price": 8,
        "description": "Custom networking strategy with target companies, events, and connection scripts",
        "delivery": "24 hours",
        "features": ["Target company list (20+)", "LinkedIn connection scripts", "Industry event calendar", "Referral request templates"],
        "what_they_get": "PDF networking plan with 20+ target companies, 5 connection scripts, event calendar",
    },
    {
        "id": "salary-benchmark",
        "name": "Salary Benchmark Report",
        "price": 7,
        "description": "Personalized salary benchmark report for their role, experience, and location (Gulf/MENA focus)",
        "delivery": "24 hours",
        "features": ["Role-specific salary data (10+ companies)", "Experience-adjusted range", "Location comparison (5+ cities)", "Benefits value analysis"],
        "what_they_get": "PDF salary report with range, percentiles, company comparison, and negotiation target number",
    },
    {
        "id": "linkedin-optimization",
        "name": "LinkedIn Profile Makeover",
        "price": 10,
        "description": "Full LinkedIn profile optimization — headline, about, experience, skills, recommendations",
        "delivery": "24 hours",
        "features": ["Headline rewrite (SEO)", "About section overhaul", "Experience bullets optimized", "Skill endorsements strategy", "Recommendation request templates"],
        "what_they_get": "Complete profile rewrite document + implementation guide they can copy-paste",
    },

    # ═══════════════════════════════════════════
    # TIER 3: PREMIUM ($12 - $20) — 48h delivery
    # ═══════════════════════════════════════════
    {
        "id": "interview-prep",
        "name": "AI Interview Coach",
        "price": 12,
        "description": "AI-powered mock interview with real questions tailored to their target role",
        "delivery": "instant",
        "features": ["Role-specific questions (20+)", "AI evaluates responses", "Score with improvement tips", "Behavioral + technical"],
        "what_they_get": "20+ practice questions with AI evaluation, personalized improvement plan, confidence score",
    },
    {
        "id": "career-consultation",
        "name": "Career Strategy Session",
        "price": 15,
        "description": "Comprehensive career roadmap with salary benchmarks, growth path, and action plan",
        "delivery": "48 hours",
        "features": ["5-year career roadmap", "Salary benchmarking (Gulf/MENA)", "Certification roadmap", "Action plan with timeline"],
        "what_they_get": "PDF career roadmap with salary data for 10+ roles, certification path, 90-day action plan",
    },
    {
        "id": "full-application-pack",
        "name": "Complete Application Pack",
        "price": 15,
        "description": "Everything: optimized CV, cover letter, email templates, follow-ups, company research",
        "delivery": "24 hours",
        "features": ["ATS-optimized CV", "Custom cover letter", "5 email templates", "Follow-up sequence", "3 company research reports"],
        "what_they_get": "Full application kit: CV + cover letter + templates + follow-ups + research — all in one zip",
    },
    {
        "id": "salary-negotiation",
        "name": "Salary Negotiation Playbook",
        "price": 15,
        "description": "Data-driven salary negotiation strategy with scripts for every stage",
        "delivery": "24 hours",
        "features": ["Market salary data (Gulf/MENA)", "Negotiation scripts (5 stages)", "Counter-offer strategies", "Benefits negotiation tips"],
        "what_they_get": "Complete negotiation playbook with scripts, salary data for 10+ roles, email templates",
    },
    {
        "id": "job-search-plan",
        "name": "90-Day Job Search Plan",
        "price": 15,
        "description": "Structured 90-day job search plan with weekly goals, targets, and tracking",
        "delivery": "24 hours",
        "features": ["Week-by-week action plan", "Application targets (100/day)", "Progress tracking template", "Milestone checkpoints"],
        "what_they_get": "PDF 90-day plan with weekly checklists, application tracker, accountability system",
    },
    {
        "id": "vip-support-month",
        "name": "VIP Support — 1 Month",
        "price": 20,
        "description": "30 days of priority support: daily applications, daily follow-ups, weekly reports",
        "delivery": "instant (30-day access)",
        "features": ["Daily automated applications (100+/day)", "Daily follow-up sending", "Weekly progress reports", "Priority email support", "Response tracking dashboard"],
        "what_they_get": "30 days of FULL automation: 3000+ applications sent, all follow-ups managed, weekly reports",
    },
]

# Bouquet packages (bundles for better value)
BOUQUET_CATALOG = [
    {
        "id": "starter-pack",
        "name": "Starter Pack",
        "price": 5,
        "services": ["cv-review", "cover-letter-basic", "email-template"],
        "savings": "33%",
        "description": "Everything to start: CV review + cover letter + email template",
    },
    {
        "id": "linkedin-pack",
        "name": "LinkedIn Optimization Pack",
        "price": 12,
        "services": ["linkedin-headline", "linkedin-optimization"],
        "savings": "15%",
        "description": "Full LinkedIn transformation: headline + complete profile makeover",
    },
    {
        "id": "application-pack",
        "name": "Complete Application Pack",
        "price": 18,
        "services": ["full-application-pack", "response-tracker", "followup-sequence"],
        "savings": "25%",
        "description": "Everything application-related: pack + tracker + follow-ups",
    },
    {
        "id": "premium-pack",
        "name": "Premium Career Pack",
        "price": 20,
        "services": ["full-application-pack", "linkedin-optimization", "career-consultation", "interview-prep"],
        "savings": "35%",
        "description": "Full career transformation: applications + LinkedIn + strategy + interview prep",
    },
    {
        "id": "vip-month",
        "name": "VIP Month",
        "price": 20,
        "services": ["vip-support-month"],
        "savings": "0% (already best price)",
        "description": "30 days of FULL automation — 3000+ applications, all follow-ups, weekly reports",
    },
]


def get_service(service_id: str) -> Optional[Dict[str, Any]]:
    """Get a service by its ID. Returns None if not found."""
    if not service_id or not isinstance(service_id, str):
        logger.warning(f"[catalog] get_service called with invalid ID: {service_id!r}")
        return None
    sid = service_id.strip().lower()
    for s in SERVICE_CATALOG:
        if s.get("id", "") == sid:
            return s.copy()
    logger.debug(f"[catalog] Service not found: {service_id!r}")
    return None


def get_bouquet(bouquet_id: str) -> Optional[Dict[str, Any]]:
    """Get a bouquet package by its ID. Returns None if not found."""
    if not bouquet_id or not isinstance(bouquet_id, str):
        logger.warning(f"[catalog] get_bouquet called with invalid ID: {bouquet_id!r}")
        return None
    bid = bouquet_id.strip().lower()
    for b in BOUQUET_CATALOG:
        if b.get("id", "") == bid:
            return b.copy()
    logger.debug(f"[catalog] Bouquet not found: {bouquet_id!r}")
    return None


def get_services_by_price_range(min_price: int, max_price: int) -> List[Dict[str, Any]]:
    """Get all services within a price range (inclusive)."""
    if min_price < 0 or max_price < min_price:
        logger.warning(f"[catalog] Invalid price range: {min_price}–{max_price}")
        return []
    return [s for s in SERVICE_CATALOG if min_price <= s.get("price", 0) <= max_price]


def get_all_service_ids() -> List[str]:
    """Return all valid service IDs for validation purposes."""
    return [s["id"] for s in SERVICE_CATALOG]


def validate_service_exists(service_id: str) -> bool:
    """Return True if the service_id exists in the catalog."""
    return get_service(service_id) is not None


def format_catalog_markdown() -> str:
    """Return the entire catalog as formatted markdown for display."""
    try:
        lines = ["# JobHunt Pro -- Service Catalog\n"]
        lines.append(f"**Total Services:** {len(SERVICE_CATALOG)} | **Bouquets:** {len(BOUQUET_CATALOG)}\n")
        lines.append(f"**Price Range:** $2 -- $20\n")
        lines.append("---\n")

        # Group by price range
        lines.append("## MICRO SERVICES ($2 - $5)\n")
        for s in get_services_by_price_range(2, 5):
            lines.append(f"### {s['name']} — **${s['price']}**")
            lines.append(f"_{s['description']}_")
            lines.append(f"- Delivery: {s.get('delivery', 'N/A')}")
            lines.append(f"- What you get: {s.get('what_they_get', 'N/A')}")
            lines.append("")

        lines.append("## STANDARD SERVICES ($6 - $10)\n")
        for s in get_services_by_price_range(6, 10):
            lines.append(f"### {s['name']} — **${s['price']}**")
            lines.append(f"_{s['description']}_")
            lines.append(f"- Delivery: {s.get('delivery', 'N/A')}")
            lines.append(f"- What you get: {s.get('what_they_get', 'N/A')}")
            lines.append("")

        lines.append("## PREMIUM SERVICES ($12 - $20)\n")
        for s in get_services_by_price_range(12, 20):
            lines.append(f"### {s['name']} — **${s['price']}**")
            lines.append(f"_{s['description']}_")
            lines.append(f"- Delivery: {s.get('delivery', 'N/A')}")
            lines.append(f"- What you get: {s.get('what_they_get', 'N/A')}")
            lines.append("")

        lines.append("## BOUQUET PACKAGES\n")
        for b in BOUQUET_CATALOG:
            lines.append(f"### {b['name']} — **${b['price']}** (Save {b.get('savings', '0%')})")
            lines.append(f"_{b['description']}_")
            lines.append("")

        lines.append("---\n")
        lines.append("**Payment:** Crypto (BTC/ETH/USDT/LTC) -- send exact amount to wallet address\n")
        lines.append("**Delivery:** Instant = automated within minutes | 24h/48h = within timeframe\n")

        return "\n".join(lines)
    except Exception as e:
        logger.error(f"[catalog] Error formatting catalog markdown: {e}", exc_info=True)
        return "# JobHunt Pro Service Catalog\n\n_Error loading catalog. Please try again._\n"
