"""
Dynamic OpenGraph Card Generator — GOD-MODE Module
Renders dynamic, high-converting SVG share cards for candidates, jobs, and referral badges.
"""

import html
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def generate_og_card_svg(
    title: str,
    subtitle: str,
    score: int = 98,
    badge: str = "VERIFIED CANDIDATE",
    theme: str = "dark"
) -> str:
    """
    Generates a crisp 1200x630 OpenGraph SVG image string with modern typography,
    luxurious gradients, and glassmorphism badges.
    """
    clean_title = html.escape(title[:45])
    clean_subtitle = html.escape(subtitle[:60])
    clean_badge = html.escape(badge[:25])
    
    bg_gradient = "url(#dark-grad)" if theme == "dark" else "url(#light-grad)"
    text_color = "#FFFFFF" if theme == "dark" else "#0F172A"

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" fill="none">
    <defs>
        <linearGradient id="dark-grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#090D16" />
            <stop offset="50%" stop-color="#0F172A" />
            <stop offset="100%" stop-color="#1E1B4B" />
        </linearGradient>
        <linearGradient id="accent-grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#6366F1" />
            <stop offset="50%" stop-color="#8B5CF6" />
            <stop offset="100%" stop-color="#EC4899" />
        </linearGradient>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="30" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
    </defs>

    <!-- Background -->
    <rect width="1200" height="630" fill="{bg_gradient}" />

    <!-- Ambient Glow Spheres -->
    <circle cx="1050" cy="150" r="250" fill="#6366F1" opacity="0.15" filter="url(#glow)" />
    <circle cx="150" cy="500" r="200" fill="#EC4899" opacity="0.1" filter="url(#glow)" />

    <!-- Glassmorphic Card Container -->
    <rect x="80" y="80" width="1040" height="470" rx="24" fill="#FFFFFF" fill-opacity="0.04" stroke="#FFFFFF" stroke-opacity="0.12" stroke-width="1.5" />

    <!-- Badge -->
    <rect x="130" y="140" width="220" height="42" rx="21" fill="url(#accent-grad)" />
    <text x="240" y="167" fill="#FFFFFF" font-family="'Inter', sans-serif" font-size="14" font-weight="700" text-anchor="middle" letter-spacing="1.5">{clean_badge}</text>

    <!-- Match Score Dial -->
    <circle cx="970" cy="190" r="50" stroke="#334155" stroke-width="8" fill="none" />
    <circle cx="970" cy="190" r="50" stroke="url(#accent-grad)" stroke-width="8" fill="none" stroke-dasharray="314" stroke-dashoffset="{314 - (314 * score / 100)}" stroke-linecap="round" />
    <text x="970" y="198" fill="#FFFFFF" font-family="'Inter', sans-serif" font-size="28" font-weight="800" text-anchor="middle">{score}%</text>

    <!-- Main Title -->
    <text x="130" y="270" fill="{text_color}" font-family="'Inter', sans-serif" font-size="48" font-weight="800" line-height="1.2">{clean_title}</text>

    <!-- Subtitle -->
    <text x="130" y="340" fill="#94A3B8" font-family="'Inter', sans-serif" font-size="24" font-weight="400">{clean_subtitle}</text>

    <!-- Footer Branding -->
    <line x1="130" y1="440" x2="1010" y2="440" stroke="#FFFFFF" stroke-opacity="0.08" stroke-width="1" />
    <text x="130" y="485" fill="#64748B" font-family="'Inter', sans-serif" font-size="18" font-weight="600">JobHunt Pro Sovereign SaaS Empire</text>
    <text x="1010" y="485" fill="#8B5CF6" font-family="'Inter', sans-serif" font-size="18" font-weight="700" text-anchor="end">jobhuntpro.io</text>
</svg>"""
    return svg_content
