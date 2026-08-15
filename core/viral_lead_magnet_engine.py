"""
Viral Lead Magnet Engine & Recruiter ROI Arbitrage Hub
Embeddable ATS lead magnet widget generator, Golden Ticket referral tiers,
and B2B recruitment cost savings arbitrage calculator.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

logger = logging.getLogger("viral_lead_magnet_engine")

class ViralLeadMagnetEngine:
    """
    Generates embeddable widget snippets, manages viral Golden Ticket incentives,
    and computes recruiter cost-per-hire ROI arbitrage.
    """

    REFERRAL_TIERS = [
        {"tier": "Bronze Pioneer", "min_invites": 1, "tokens_reward": 50, "badge": "🥉"},
        {"tier": "Silver Hunter", "min_invites": 5, "tokens_reward": 300, "badge": "🥈"},
        {"tier": "Gold Rainmaker", "min_invites": 15, "tokens_reward": 1000, "badge": "🥇"},
        {"tier": "Platinum Sovereign", "min_invites": 50, "tokens_reward": 5000, "badge": "👑"}
    ]

    def generate_embeddable_widget(self, affiliate_code: str = "PARTNER_PRO", primary_color: str = "#0ea5e9", lang: str = "ar") -> Dict[str, Any]:
        """
        Generates embeddable responsive HTML & JS snippet with CSS logical properties and RTL support.
        """
        dir_attr = "rtl" if lang == "ar" else "ltr"
        font = "Cairo, Tajawal, sans-serif" if lang == "ar" else "Inter, system-ui, sans-serif"
        cta_text = "افحص سيرتك الذاتية مجاناً عبر الذكاء الاصطناعي" if lang == "ar" else "Audit Your CV Free with AI"

        widget_html = f"""<!-- JobHunt Pro Free ATS Widget -->
<div id="jobhunt-ats-widget" dir="{dir_attr}" style="inline-size: 100%; max-inline-size: 480px; font-family: {font}; background: rgba(15, 23, 42, 0.95); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px; color: #fff; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);">
  <h3 style="margin-block-end: 8px; font-size: 20px; font-weight: 700;">{cta_text}</h3>
  <p style="font-size: 14px; opacity: 0.8; margin-block-end: 16px;">{ 'احصل على تقرير فوري مجاني بنسبة مطابقة الـ ATS لنظام الخليج' if lang == 'ar' else 'Get an instant ATS matching score report for GCC tech roles' }</p>
  <textarea id="cv-input-field" dir="auto" placeholder="{ 'الصق سيرتك الذاتية هنا...' if lang == 'ar' else 'Paste your CV here...' }" style="inline-size: 100%; min-block-size: 100px; background: rgba(0,0,0,0.4); border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; padding: 12px; font-size: 14px;"></textarea>
  <button onclick="window.jobhuntAudit('{affiliate_code}')" style="margin-block-start: 12px; inline-size: 100%; background: {primary_color}; color: #fff; font-weight: 600; padding: 12px; border: none; border-radius: 8px; cursor: pointer;">
    { 'تحليل فوري الآن (0$ مجاناً)' if lang == 'ar' else 'Run Instant AI Audit (Free)' }
  </button>
</div>
<script src="https://jobhuntpro.io/widget/ats-embed.js" async></script>"""

        return {
            "affiliate_code": affiliate_code,
            "language": lang,
            "direction": dir_attr,
            "embed_code": widget_html,
            "conversion_multiplier": "3.5x Inbound Lead Velocity"
        }

    def generate_golden_ticket(self, user_id: str) -> Dict[str, Any]:
        """
        Creates a high-conversion viral golden ticket link with instant token bonus.
        """
        ticket_id = f"GT-{uuid.uuid4().hex[:8].upper()}"
        return {
            "user_id": user_id,
            "ticket_id": ticket_id,
            "viral_url": f"https://jobhuntpro.io/join?ticket={ticket_id}&ref={user_id}",
            "bonus_tokens_on_signup": 100,
            "sharer_reward_tokens": 50,
            "social_share_text": "حصلت على بطاقة ذهبية للدخول إلى منصة JobHunt Pro للتوظيف الذاتي بالذكاء الاصطناعي مع 100 توكن مجاناً 🚀!"
        }

    def calculate_recruiter_roi(self, hires_per_year: int = 10, avg_annual_salary_usd: float = 80000.0) -> Dict[str, Any]:
        """
        Calculates annual cost savings comparing traditional headhunter agencies (20% fee)
        against JobHunt Pro SaaS autonomous outreach.
        """
        agency_cost_per_hire = avg_annual_salary_usd * 0.20
        total_agency_cost = hires_per_year * agency_cost_per_hire
        
        jobhunt_annual_subscription = 2400.0  # $200/mo enterprise tier
        total_savings = total_agency_cost - jobhunt_annual_subscription
        roi_percentage = (total_savings / jobhunt_annual_subscription) * 100.0

        return {
            "hires_per_year": hires_per_year,
            "avg_salary_usd": avg_annual_salary_usd,
            "traditional_agency_cost_usd": total_agency_cost,
            "jobhunt_pro_cost_usd": jobhunt_annual_subscription,
            "net_annual_savings_usd": total_savings,
            "roi_multiplier": f"{round(roi_percentage / 100.0, 1)}x",
            "savings_percentage": f"{round((total_savings / total_agency_cost) * 100.0, 1)}%"
        }

    def generate_shareable_ats_card(
        self,
        candidate_name: str,
        target_role: str,
        ats_score: int = 94,
        user_id: Optional[str] = None,
        lang: str = "ar"
    ) -> Dict[str, Any]:
        """
        Generates dynamic viral ATS score shareable cards with social media deep-links
        and Golden Ticket referral bounties.
        """
        score = max(0, min(100, ats_score))
        uid = user_id or f"u_{uuid.uuid4().hex[:6]}"
        ticket = self.generate_golden_ticket(uid)
        
        # Determine percentile & tier badge
        if score >= 90:
            tier_title = "Elite 1% GCC Talent" if lang == "en" else "نخبة الكفاءات الخليجية (أعلى 1%)"
            badge_color = "#10b981" # Emerald Green
            status_tag = "READY_FOR_DIRECT_HIRE"
        elif score >= 75:
            tier_title = "Top Tier GCC Candidate" if lang == "en" else "مرشح متقدم للشركات الرائدة (أعلى 10%)"
            badge_color = "#0ea5e9" # Blue
            status_tag = "HIGH_MATCH"
        else:
            tier_title = "Developing Professional" if lang == "en" else "مرشح مؤهل للتطوير السريع"
            badge_color = "#f59e0b" # Amber
            status_tag = "GROWTH_MATCH"

        share_url = ticket["viral_url"]
        
        # Social share text hooks
        if lang == "ar":
            headline = f"حققت نسبة مطابقة ATS بلغت {score}% لوظائف {target_role} في الخليج عبر JobHunt Pro!"
            share_text = f"🎯 حققت {score}% في فحص الـ ATS بالذكاء الاصطناعي لوظائف {target_role}!\nجرّب فحص سيرتك الذاتية مجاناً واحصل على 100 توكن إهداء 🎁:\n{share_url}"
        else:
            headline = f"I scored {score}% on JobHunt Pro's AI ATS Match for {target_role} in the GCC!"
            share_text = f"🚀 Just scored {score}/100 on JobHunt Pro's Autonomous ATS Auditor for {target_role} roles in the GCC!\nAudit your CV free with 100 bonus tokens:\n{share_url}"

        # URL-encoded social sharing channels
        import urllib.parse
        encoded_text = urllib.parse.quote(share_text)
        encoded_url = urllib.parse.quote(share_url)

        social_links = {
            "whatsapp": f"https://api.whatsapp.com/send?text={encoded_text}",
            "telegram": f"https://t.me/share/url?url={encoded_url}&text={encoded_text}",
            "linkedin": f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}",
            "twitter": f"https://twitter.com/intent/tweet?text={encoded_text}"
        }

        # Embeddable High-Converting HTML Card
        dir_attr = "rtl" if lang == "ar" else "ltr"
        font = "Cairo, Tajawal, sans-serif" if lang == "ar" else "Inter, system-ui, sans-serif"
        
        html_card = f"""<div class="ats-shareable-card" dir="{dir_attr}" style="inline-size: 100%; max-inline-size: 520px; font-family: {font}; background: linear-gradient(145deg, #0b1329, #111e38); border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; padding: 28px; color: #fff; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); position: relative; overflow: hidden;">
  <div style="display: flex; justify-content: space-between; align-items: center; margin-block-end: 20px;">
    <div>
      <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: {badge_color}; font-weight: 700;">JobHunt Pro • AI Verified</span>
      <h3 style="margin: 4px 0 0 0; font-size: 22px; font-weight: 700;">{candidate_name}</h3>
      <p style="margin: 2px 0 0 0; font-size: 14px; opacity: 0.75;">{target_role}</p>
    </div>
    <div style="inline-size: 72px; block-size: 72px; border-radius: 50%; background: radial-gradient(circle, rgba(16,185,129,0.2) 0%, rgba(0,0,0,0) 70%); border: 2px solid {badge_color}; display: flex; flex-direction: column; align-items: center; justify-content: center;">
      <span style="font-size: 24px; font-weight: 900; color: #fff; line-height: 1;">{score}</span>
      <span style="font-size: 10px; color: {badge_color}; font-weight: 600;">ATS SCORE</span>
    </div>
  </div>
  <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 14px 18px; margin-block-end: 20px; border-inline-start: 4px solid {badge_color};">
    <div style="font-size: 14px; font-weight: 600; color: #f8fafc;">{tier_title}</div>
    <div style="font-size: 12px; opacity: 0.8; margin-block-start: 4px;">{ 'السيرة الذاتية متوافقة بالكامل مع خوارزميات التوظيف في أسواق السعودية والإمارات وقطر.' if lang == 'ar' else 'Profile fully optimized for GCC enterprise ATS filters and recruiter algorithms.' }</div>
  </div>
  <div style="display: flex; gap: 10px; justify-content: stretch;">
    <a href="{social_links['linkedin']}" target="_blank" rel="noopener noreferrer" style="flex: 1; text-align: center; background: #0a66c2; color: #fff; text-decoration: none; padding: 10px 14px; border-radius: 10px; font-size: 13px; font-weight: 600;">LinkedIn</a>
    <a href="{social_links['whatsapp']}" target="_blank" rel="noopener noreferrer" style="flex: 1; text-align: center; background: #25d366; color: #fff; text-decoration: none; padding: 10px 14px; border-radius: 10px; font-size: 13px; font-weight: 600;">WhatsApp</a>
    <a href="{social_links['telegram']}" target="_blank" rel="noopener noreferrer" style="flex: 1; text-align: center; background: #229ed9; color: #fff; text-decoration: none; padding: 10px 14px; border-radius: 10px; font-size: 13px; font-weight: 600;">Telegram</a>
  </div>
</div>"""

        return {
            "candidate_name": candidate_name,
            "target_role": target_role,
            "ats_score": score,
            "tier_title": tier_title,
            "badge_color": badge_color,
            "status_tag": status_tag,
            "golden_ticket": ticket,
            "headline": headline,
            "social_links": social_links,
            "html_card": html_card
        }


# Singleton instance
viral_lead_magnet_engine = ViralLeadMagnetEngine()
