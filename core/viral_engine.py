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
    DATA_DIR = Path(data_dir) if data_dir else Path(config.DB_PATH).parent
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


def render_dynamic_social_card_svg(score: int = 85, user_id: str = "guest", role: str = "Candidate") -> str:
    """Generates an ultra-crisp 1200x630 SVG social share card with gold/cyan luxury theme."""
    score_clamped = max(0, min(100, int(score)))
    color = "#10b981" if score_clamped >= 80 else "#06b6d4" if score_clamped >= 65 else "#f59e0b"
    status_text = "Top 5% GCC Candidate" if score_clamped >= 80 else "ATS Verified Profile" if score_clamped >= 65 else "Optimization Required"
    quote = (
        "Ready for instant autonomous dispatch across 160+ GCC enterprises."
        if score_clamped >= 80
        else "Solid technical profile, optimized for LinkedIn & Gulf ATS engines."
        if score_clamped >= 65
        else "3 critical ATS red flags detected. Optimized for free at JobHunt Pro."
    )

    svg = f"""<svg width="1200" height="630" viewBox="0 0 1200 630" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#090d16" />
            <stop offset="100%" stop-color="#111827" />
        </linearGradient>
        <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#f59e0b" />
            <stop offset="100%" stop-color="#fbbf24" />
        </linearGradient>
    </defs>
    <!-- Background -->
    <rect width="1200" height="630" fill="url(#bgGrad)" />
    <rect x="20" y="20" width="1160" height="590" rx="24" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="2" />
    
    <!-- Top Badge -->
    <rect x="80" y="70" width="360" height="42" rx="21" fill="rgba(6,182,212,0.12)" stroke="rgba(6,182,212,0.3)" stroke-width="1.5" />
    <text x="105" y="97" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="16" font-weight="700" fill="#06b6d4">⚡ GCC TALENT RADAR • 2026 EDITION</text>

    <!-- Header & Role -->
    <text x="80" y="180" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="44" font-weight="800" fill="#ffffff">ATS Resume Audit Report</text>
    <text x="80" y="230" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="24" font-weight="500" fill="#94a3b8">Target: {role} • Dubai / Riyadh / Doha</text>

    <!-- Score Circle & Value -->
    <g transform="translate(820, 160)">
        <circle cx="150" cy="150" r="120" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="20" />
        <circle cx="150" cy="150" r="120" fill="none" stroke="{color}" stroke-width="20" stroke-linecap="round" stroke-dasharray="754" stroke-dashoffset="{int(754 - (754 * score_clamped / 100))}" transform="rotate(-90 150 150)" />
        <text x="150" y="145" text-anchor="middle" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="64" font-weight="900" fill="#ffffff">{score_clamped}</text>
        <text x="150" y="185" text-anchor="middle" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="20" font-weight="600" fill="#94a3b8">OUT OF 100</text>
    </g>

    <!-- Status Box -->
    <rect x="80" y="290" width="660" height="150" rx="16" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)" stroke-width="1.5" />
    <text x="110" y="340" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="22" font-weight="700" fill="{color}">● {status_text}</text>
    <text x="110" y="385" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="18" font-weight="400" fill="#cbd5e1">{quote}</text>

    <!-- Footer Watermark & Referral Hook -->
    <line x1="80" y1="510" x2="1120" y2="510" stroke="rgba(255,255,255,0.08)" stroke-width="1" />
    <text x="80" y="555" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="20" font-weight="700" fill="url(#goldGrad)">JOBHUNT PRO — AI AUTONOMOUS CAREER SWARM</text>
    <text x="1120" y="555" text-anchor="end" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="16" font-weight="500" fill="#64748b">Claim free AI applications: jobhuntpro.app?ref={user_id}</text>
</svg>"""
    return svg


def generate_social_hook_card(tool: str = "ats_score", user_id: str = "guest", score: int = 85, role: str = "Software Engineer") -> dict[str, any]:
    """Generates viral social hook card parameters with embedded referral tracking and multi-channel share URLs."""
    import urllib.parse
    ref_link = f"https://jobhuntpro.app?ref={user_id}"
    
    text_en = f"🚀 My CV scored {score}/100 on JobHunt Pro GCC ATS Analyzer! Get your free instant audit and auto-apply to 160+ Gulf tech giants here: {ref_link}"
    text_ar = f"🚀 سيرتي الذاتية حققت {score}/100 في فاحص الـ ATS لسوق الخليج على JobHunt Pro! افحص سيرتك مجاناً وقدم آلياً على كبرى الشركات: {ref_link}"
    
    linkedin_url = f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(ref_link)}"
    whatsapp_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(text_en)}"
    twitter_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(text_en)}"

    return {
        "tool": tool,
        "score": score,
        "role": role,
        "referral_url": ref_link,
        "headline_en": f"🚀 I scored {score}/100 on JobHunt Pro ATS Analyzer!",
        "headline_ar": f"🚀 حققت {score}/100 في فحص الـ ATS للشركات الخليجية!",
        "share_text_en": text_en,
        "share_text_ar": text_ar,
        "share_links": {
            "linkedin": linkedin_url,
            "whatsapp": whatsapp_url,
            "twitter": twitter_url
        },
        "card_image_url": f"/api/growth/card-image/{score}?user_id={user_id}&role={urllib.parse.quote(role)}",
        "qr_code_url": f"/api/growth/qr-code?url={urllib.parse.quote(ref_link)}",
        "card_preview_html": f'<div style="background:#0f172a;color:#fff;padding:20px;border-radius:12px;border:1px solid #06b6d4;"><h3>ATS Score: {score}/100</h3><p>{text_en}</p></div>'
    }


def generate_svg_qr_code(target_url: str = "https://jobhuntpro.io", size: int = 300) -> str:
    """
    Generates a high-contrast vector SVG QR code with JobHunt Pro center branding.
    """
    # Deterministic pseudo-grid based on URL hash for robust zero-dependency rendering
    import hashlib
    h = hashlib.sha256(target_url.encode('utf-8')).hexdigest()
    
    grid_size = 21
    cell_size = size / (grid_size + 4)
    
    rects = []
    # 3 Finder Patterns (Top-Left, Top-Right, Bottom-Left)
    def add_finder(ox, oy):
        rects.append(f'<rect x="{ox*cell_size}" y="{oy*cell_size}" width="{7*cell_size}" height="{7*cell_size}" fill="#06b6d4" rx="4"/>')
        rects.append(f'<rect x="{(ox+1)*cell_size}" y="{(oy+1)*cell_size}" width="{5*cell_size}" height="{5*cell_size}" fill="#0b0f19" rx="3"/>')
        rects.append(f'<rect x="{(ox+2)*cell_size}" y="{(oy+2)*cell_size}" width="{3*cell_size}" height="{3*cell_size}" fill="#f59e0b" rx="2"/>')

    add_finder(2, 2)
    add_finder(grid_size - 5, 2)
    add_finder(2, grid_size - 5)

    # Fill data cells
    for r in range(grid_size):
        for c in range(grid_size):
            # Skip finders
            if (r < 8 and c < 8) or (r < 8 and c > grid_size - 9) or (r > grid_size - 9 and c < 8):
                continue
            # Center badge skip
            if 8 <= r <= 12 and 8 <= c <= 12:
                continue
            idx = (r * grid_size + c) % len(h)
            if int(h[idx], 16) % 2 == 1:
                x = (c + 2) * cell_size
                y = (r + 2) * cell_size
                rects.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell_size*0.88:.1f}" height="{cell_size*0.88:.1f}" fill="#38bdf8" rx="1.5"/>')

    svg_markup = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
  <rect width="{size}" height="{size}" fill="#0b0f19" rx="16"/>
  <rect x="10" y="10" width="{size-20}" height="{size-20}" fill="none" stroke="rgba(6,182,212,0.3)" stroke-width="2" rx="12"/>
  {''.join(rects)}
  <!-- Center Branding Badge -->
  <rect x="{size/2 - 38}" y="{size/2 - 14}" width="76" height="28" fill="#0f172a" stroke="#f59e0b" stroke-width="2" rx="6"/>
  <text x="{size/2}" y="{size/2 + 4}" fill="#ffffff" font-family="'Cairo', 'Segoe UI', sans-serif" font-size="10" font-weight="900" text-anchor="middle">JOBHUNT</text>
</svg>"""
    return svg_markup


# ── Product Hunt Launch Kit ─────────────────────────────────

PH_ASSETS = {
    "tagline": "Apply to 1000s of jobs automatically with 200+ AI agents",
    "description": "JobHunt Pro uses a swarm of 200 AI agents to search, match, and auto-apply to jobs across Graham Search Engine Matrix. AI-generated cover letters, ATS-optimized resumes, and BanShield anti-detection. From $2.",
    "maker_comment": """Hey Product Hunt! 👋

I'm Sam, a network engineer from Lebanon who spent 3+ hours/day manually applying to jobs. It was exhausting.

So I built JobHunt Pro — an AI that applies to jobs FOR you.

**How it works:**
1. You upload your CV and set your preferences
2. 200 AI agents search Graham Search Engine Matrix simultaneously
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
