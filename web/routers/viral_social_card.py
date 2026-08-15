"""
web/routers/viral_social_card.py - Dynamic SVG Social Share Cards & Viral ATS Badges
JobHunt Pro SaaS - Generates zero-cost, high-converting visual scorecards for 1-click
viral sharing across LinkedIn, WhatsApp, and Twitter/X with zero third-party graphic dependencies.
"""

from fastapi import APIRouter, Query, Response, Request
from fastapi.responses import HTMLResponse
import html
import urllib.parse

router = APIRouter(prefix="/api/viral", tags=["Viral Growth Engine"])

def generate_svg_scorecard(score: int, name: str, role: str, percentile: int = 95) -> str:
    """
    Renders an Apex Glassmorphism SVG Badge with glowing cyber-gradient and ATS Score metrics.
    100% vector-based, lightweight (<3KB), works directly in social previews and image tags.
    """
    clean_name = html.escape(name[:25])
    clean_role = html.escape(role[:30])
    score_val = max(10, min(100, score))
    
    # Dynamic color grade
    if score_val >= 90:
        accent_color = "#10B981" # Emerald Green
        tier_label = "TOP 5% ELITE CANDIDATE"
        stroke_dash = int((score_val / 100) * 283)
    elif score_val >= 75:
        accent_color = "#3B82F6" # Blue
        tier_label = "HIGH-COMPATIBILITY APPLICANT"
        stroke_dash = int((score_val / 100) * 283)
    else:
        accent_color = "#F59E0B" # Amber
        tier_label = "OPTIMIZED FOR GCC ATS"
        stroke_dash = int((score_val / 100) * 283)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 450" width="800" height="450">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090D16"/>
      <stop offset="50%" stop-color="#0F172A"/>
      <stop offset="100%" stop-color="#050811"/>
    </linearGradient>
    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{accent_color}"/>
      <stop offset="100%" stop-color="#6366F1"/>
    </linearGradient>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="12" result="blur"/>
      <feComposite in="SourceGraphic" in2="blur" operator="over"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="800" height="450" rx="24" fill="url(#bgGrad)"/>
  <rect width="798" height="448" x="1" y="1" rx="23" fill="none" stroke="#1E293B" stroke-width="1.5"/>

  <!-- Glowing Aura -->
  <circle cx="620" cy="225" r="130" fill="{accent_color}" opacity="0.12" filter="url(#glow)"/>

  <!-- Header / Brand -->
  <g transform="translate(50, 55)">
    <rect width="32" height="32" rx="8" fill="url(#accentGrad)"/>
    <text x="44" y="22" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="800" fill="#FFFFFF" letter-spacing="0.5">JOBHUNT PRO</text>
    <text x="180" y="22" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700" fill="{accent_color}" letter-spacing="1">ATS VERIFIED</text>
  </g>

  <!-- Candidate Details -->
  <g transform="translate(50, 150)">
    <text x="0" y="0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="14" font-weight="700" fill="{accent_color}" letter-spacing="1.5">{tier_label}</text>
    <text x="0" y="45" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="800" fill="#FFFFFF">{clean_name}</text>
    <text x="0" y="85" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="500" fill="#94A3B8">{clean_role}</text>

    <!-- Badges -->
    <g transform="translate(0, 130)">
      <rect width="180" height="38" rx="10" fill="#1E293B" opacity="0.8"/>
      <text x="90" y="24" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="600" fill="#F8FAFC">⚡ Gulf & GCC Optimized</text>
    </g>
    <g transform="translate(195, 130)">
      <rect width="170" height="38" rx="10" fill="#1E293B" opacity="0.8"/>
      <text x="85" y="24" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="13" font-weight="600" fill="#F8FAFC">🎯 Top {100 - percentile}% Percentile</text>
    </g>
  </g>

  <!-- Circular Score Gauge -->
  <g transform="translate(620, 225)">
    <!-- Base track -->
    <circle cx="0" cy="0" r="75" fill="none" stroke="#1E293B" stroke-width="14"/>
    <!-- Progress arc -->
    <circle cx="0" cy="0" r="75" fill="none" stroke="url(#accentGrad)" stroke-width="14"
            stroke-dasharray="471" stroke-dashoffset="{471 - int((score_val/100)*471)}"
            stroke-linecap="round" transform="rotate(-90)"/>
    <!-- Score Text -->
    <text x="0" y="14" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="48" font-weight="900" fill="#FFFFFF">{score_val}</text>
    <text x="0" y="38" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="700" fill="#64748B" letter-spacing="1">ATS SCORE</text>
  </g>

  <!-- Footer Verification -->
  <text x="50" y="405" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="12" font-weight="500" fill="#475569">Verified by JobHunt Pro AI Swarm Engine • jobhuntpro.com/ats-score</text>
</svg>"""

@router.get("/card.svg")
async def get_viral_card_svg(
    score: int = Query(94, ge=0, le=100),
    name: str = Query("Executive Candidate"),
    role: str = Query("Senior Professional"),
    percentile: int = Query(95, ge=1, le=99)
):
    """Returns dynamic SVG scorecard image for viral sharing."""
    svg_content = generate_svg_scorecard(score, name, role, percentile)
    return Response(
        content=svg_content,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.get("/share-modal")
async def get_share_modal_html(
    score: int = Query(94, ge=0, le=100),
    name: str = Query("Candidate"),
    role: str = Query("Professional")
):
    """Returns responsive modal with 1-click WhatsApp, LinkedIn, and Twitter share buttons."""
    card_url = f"/api/viral/card.svg?score={score}&name={urllib.parse.quote(name)}&role={urllib.parse.quote(role)}"
    share_text = f"🔥 Just verified my CV with JobHunt Pro ATS Engine! Got a score of {score}/100 in the top 5% of GCC applicants. Check yours for free:"
    target_link = "https://jobhunt-pro.com/ats-scorer"

    wa_url = f"https://api.whatsapp.com/send?text={urllib.parse.quote(share_text + ' ' + target_link)}"
    li_url = f"https://www.linkedin.com/sharing/share-offsite/?url={urllib.parse.quote(target_link)}"
    tw_url = f"https://twitter.com/intent/tweet?text={urllib.parse.quote(share_text)}&url={urllib.parse.quote(target_link)}"

    return {
        "status": "success",
        "score": score,
        "svg_card_url": card_url,
        "whatsapp_share_url": wa_url,
        "linkedin_share_url": li_url,
        "twitter_share_url": tw_url,
        "share_text": share_text
    }
