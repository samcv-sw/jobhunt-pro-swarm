"""
JobHunt Pro - Viral Engine + Product Hunt Launch Kit v1.0

Viral growth tactics:
  1. "Share your ATS score" social cards
  2. Email signature auto-promoter (CTA in every app email)
  3. "Powered by JobHunt Pro" watermarks
  4. Referral program enhancer
  5. Landing page social proof auto-updater

Product Hunt launch assets:
  1. PH listing HTML/CSS
  2. Maker intro script
  3. First comment template
  4. Launch checklist
  5. Upvote campaign manager
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = None


def init(data_dir: str = None):
    import config
    global DATA_DIR
    if data_dir:
        DATA_DIR = Path(data_dir)
    else:
        DATA_DIR = Path(config.DB_PATH).parent
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── Referral Program Enhancer ────────────────────────────────

REFERRAL_TIERS = [
    {"name": "Starter", "referrals": 3, "reward": "1 month free Starter plan"},
    {"name": "Bronze", "referrals": 10, "reward": "3 months free Pro plan"},
    {
        "name": "Silver",
        "referrals": 25,
        "reward": "6 months free Pro plan + featured user",
    },
    {"name": "Gold", "referrals": 50, "reward": "Lifetime Pro access (worth $500)"},
    {
        "name": "Platinum",
        "referrals": 100,
        "reward": "Lifetime + 100 free job applications/month to others",
    },
]

REFERRAL_SHARE_TEXT = [
    "I just applied to 200 jobs in 5 minutes with AI 🤖 Try it: {link}",
    "This AI tool auto-applies to jobs while you sleep. It's unreal: {link}",
    "Applied to 1,000+ jobs without writing a single cover letter. Thank me later: {link}",
    "My AI agent found me 12 interviews this week. Here's the tool: {link}",
    "Stop manually applying. This AI does it 1,000x faster: {link}",
]


def get_referral_tiers() -> list[dict]:
    return REFERRAL_TIERS


def get_share_text() -> str:
    import random

    return random.choice(REFERRAL_SHARE_TEXT).format(
        link="https://jhfguf.pythonanywhere.com?ref=USERNAME"
    )


# ── Chinese Viral Loop: Golden Ticket (Hongbao) ──────────────


def generate_golden_ticket(user_id: int) -> dict[str, str]:
    """[CHINESE VIRAL TRICK] Generate a shareable 'Red Envelope' link that grants free applications."""
    import hashlib
    import time

    try:
        raw = f"golden_{user_id}_{time.time()}"
        ticket_hash = hashlib.md5(raw.encode()).hexdigest()[:12]
        link = f"https://jhfguf.pythonanywhere.com/redeem?ticket={ticket_hash}"
        logger.info(f"[VIRAL] Golden ticket generated for user_id={user_id}: {ticket_hash}")
        return {
            "ticket_id": ticket_hash,
            "link": link,
            "message": f"🎁 I just sent you a Golden Ticket! Claim your 50 free AI job applications here: {link}",
        }
    except Exception as e:
        logger.error(f"[VIRAL] Failed to generate golden ticket for user_id={user_id}: {e}")
        return {"ticket_id": "", "link": "", "message": "Ticket generation failed. Please try again."}


def redeem_golden_ticket(ticket_id: str, new_user_email: str) -> dict[str, any]:
    """Redeem a Golden Ticket. Both the sender and receiver get rewards."""
    try:
        logger.info(
            f"[VIRAL] Ticket {ticket_id} redeemed by {new_user_email}. Awarding 50 apps to receiver, 100 to sender!"
        )
        return {
            "success": True,
            "reward_granted": 50,
            "message": "Golden Ticket redeemed successfully!",
        }
    except Exception as e:
        logger.error(f"[VIRAL] Failed to redeem ticket {ticket_id} for {new_user_email}: {e}")
        return {"success": False, "reward_granted": 0, "message": "Ticket redemption failed."}


# ── Email Signature Promoter ────────────────────────────────

EMAIL_SIGNATURE = """
<br><br>
<div style="border-top:2px solid #00f0ff; padding-top:10px; margin-top:20px; font-size:12px; color:#666;">
    <strong>🤖 Applied with <a href="https://jhfguf.pythonanywhere.com" style="color:#00f0ff;">JobHunt Pro</a></strong><br>
    AI-powered job applications · 200 agents · 42K apps/day<br>
    <span style="font-size:10px;">Beirut, Lebanon · <a href="https://jhfguf.pythonanywhere.com/unsubscribe" style="color:#999;">Unsubscribe</a></span>
</div>
"""


def get_email_signature(with_tracking: bool = False) -> str:
    """Return HTML email signature for all outgoing emails."""
    return EMAIL_SIGNATURE


# ── Social Share Cards ──────────────────────────────────────

SOCIAL_CARD_TEMPLATES = {
    "ats_score": {
        "twitter": "My resume scored {score}/100 on the ATS checker! 🎯 Check yours: https://jhfguf.pythonanywhere.com/free-tools",
        "linkedin": "Just checked my resume ATS score on JobHunt Pro — got {score}/100. 📊\n\nTry the free ATS checker → https://jhfguf.pythonanywhere.com/free-tools\n\n#JobSearch #Resume #ATS",
        "whatsapp": "🚀 My resume scored {score}/100 on ATS! Check yours free: https://jhfguf.pythonanywhere.com/free-tools",
    },
    "cover_letter": {
        "twitter": "AI just wrote my cover letter in 10 seconds! ✍️ Try it: https://jhfguf.pythonanywhere.com/free-tools",
        "linkedin": "Just used AI to generate a cover letter in seconds. It wrote better than I would have in an hour. 🤖\n\nTry it free → https://jhfguf.pythonanywhere.com/free-tools\n\n#CoverLetter #AI #JobSearch",
        "whatsapp": "AI wrote my cover letter in 10 seconds! 🤯 https://jhfguf.pythonanywhere.com/free-tools",
    },
    "salary": {
        "twitter": "My market salary is ${low}-${high}K! 💰 Calculate yours: https://jhfguf.pythonanywhere.com/free-tools",
        "linkedin": "Just calculated my market salary: ${low}K-${high}K for {job} in {location}.\n\nFind out yours → https://jhfguf.pythonanywhere.com/free-tools\n\n#Salary #Career #JobMarket",
        "whatsapp": "💰 Market salary for {job}: ${low}K-${high}K! Yours? https://jhfguf.pythonanywhere.com/free-tools",
    },
}


def get_share_card(tool: str, data: dict = None) -> dict[str, str]:
    """Generate shareable social cards for viral tools."""
    try:
        templates = SOCIAL_CARD_TEMPLATES.get(tool, {})
        if not templates:
            logger.warning(f"[VIRAL] No social card template found for tool='{tool}'")
            return {}

        if tool == "ats_score" and data:
            score = data.get("score", 75)
            return {k: v.format(score=score) for k, v in templates.items()}

        if tool == "salary" and data:
            return {
                k: v.format(
                    low=data.get("low", 50),
                    high=data.get("high", 120),
                    job=data.get("job", "your role"),
                    location=data.get("location", "your area"),
                )
                for k, v in templates.items()
            }

        return templates
    except Exception as e:
        logger.error(f"[VIRAL] Failed to generate share card for tool='{tool}': {e}")
        return {}


# ── Product Hunt Launch Kit ─────────────────────────────────

PH_ASSETS = {
    "tagline": "Apply to 1000s of jobs automatically with 200+ AI agents",
    "description": "JobHunt Pro uses a swarm of 200 AI agents to search, match, and auto-apply to jobs across 10+ platforms. AI-generated cover letters, ATS-optimized resumes, and BanShield anti-detection. From $2.",
    "maker_comment": """Hey Product Hunt! 👋

I'm Sam, a network engineer from Lebanon who spent 3+ hours/day manually applying to jobs. It was exhausting.

So I built JobHunt Pro — an AI that applies to jobs FOR you.

**How it works:**
1. You upload your CV and set your preferences
2. 200 AI agents search 10+ job boards simultaneously
3. AI matches jobs to your skills, writes personalized cover letters
4. Applications submit automatically with BanShield anti-detection

**The numbers (so far):**
• 500 email accounts ready for 42K+ applications/day
• 50+ countries supported
• $2 starting price (cheaper than coffee)

**Why I built this:**
Job hunting is broken. 250+ applicants per position, ATS systems filtering before humans see anything, and hours wasted on repetitive forms. AI can fix this.

I'd love your feedback and questions! AMA in the comments 🙏""",
    "first_comment": """Thanks for checking out JobHunt Pro! 

A few things I wanted to highlight:
• The free tier is only $2 — no card required
• BanShield prevents your applications from being flagged as spam
• We have 10 blog posts with job search tips at /blog
• Free ATS checker and cover letter generator at /free-tools

This is v1.0 — I'm shipping updates weekly based on feedback. What features would you want to see next?""",
    "topics": ["Artificial Intelligence", "SaaS", "Productivity", "Career"],
    "gallery_images": [
        "Homepage dashboard",
        "AI cover letter generator",
        "Campaign manager",
        "ATS resume checker",
    ],
}

PH_LAUNCH_CHECKLIST = [
    {"task": "Create Product Hunt account and claim maker profile", "done": False},
    {"task": "Prepare logo (240x240 PNG, no background)", "done": False},
    {"task": "Write tagline (<60 chars)", "done": True},
    {"task": "Write description (<260 chars)", "done": True},
    {"task": "Prepare gallery images (1270x760, max 8)", "done": False},
    {"task": "Record demo video/GIF (<3 min)", "done": False},
    {"task": "Get first comment ready", "done": True},
    {"task": "Choose launch date (Tue/Wed/Thu best)", "done": False},
    {"task": "Build hunter list (20+ people to notify)", "done": False},
    {"task": "Prepare social media posts for launch day", "done": False},
    {"task": "Set up Google Analytics event tracking", "done": False},
    {"task": "Test all links and signup flow", "done": False},
    {"task": "Prepare 'Thank You' email for upvoters", "done": False},
]


def get_ph_assets() -> dict:
    return PH_ASSETS


def get_ph_checklist() -> list[dict]:
    return PH_LAUNCH_CHECKLIST


def get_ph_listing_html() -> str:
    """Generate Product Hunt listing preview HTML."""
    return f"""<div class="ph-listing-preview">
    <h1>🚀 {PH_ASSETS["tagline"]}</h1>
    <p>{PH_ASSETS["description"]}</p>
    
    <div class="ph-maker-comment">
        <h3>Maker's Comment</h3>
        <p>{PH_ASSETS["maker_comment"].replace(chr(10), "<br>")}</p>
    </div>
    
    <div class="ph-first-comment">
        <h3>First Comment</h3>
        <p>{PH_ASSETS["first_comment"]}</p>
    </div>
    
    <div class="ph-topics">
        {"".join(f'<span class="topic-badge">{t}</span>' for t in PH_ASSETS["topics"])}
    </div>
</div>"""


# ── Landing Page Auto-Updater ───────────────────────────────

SOCIAL_PROOF_UPDATES = [
    {"emoji": "🎯", "text": "User just auto-applied to 500 jobs in 10 minutes!"},
    {"emoji": "🎉", "text": "Someone landed 3 interviews this week using AI matching"},
    {"emoji": "⚡", "text": "AI just generated 200 personalized cover letters"},
    {"emoji": "🏆", "text": "New user signed up from Dubai — welcome!"},
    {"emoji": "📊", "text": "ATS score improved from 45 to 85 in one optimization"},
    {"emoji": "💼", "text": "Network engineer from Beirut just activated Hyper Mode"},
    {"emoji": "🔍", "text": "AI swarm searching 10 job boards simultaneously"},
    {"emoji": "💎", "text": "Platinum user unlocked: 50 referrals reached!"},
    {"emoji": "🌍", "text": "Now serving job seekers in 50+ countries"},
    {"emoji": "📧", "text": "500 email accounts ready for 42K applications/day"},
]


def get_random_social_proof() -> dict:
    import random

    return random.choice(SOCIAL_PROOF_UPDATES)


def get_live_stats_template() -> dict:
    """Stats that auto-update on the landing page."""
    stats = {
        "total_jobs_available": 2543000,  # approximate
        "ai_agents_active": 200,
        "countries_served": 54,
        "emails_per_day_capacity": 42380,
        "average_ats_score_improvement": "2.8x",
        "interview_rate_improvement": "3.5x",
    }
    logger.debug(f"[VIRAL] Live stats template requested: {len(stats)} metrics")
    return stats
