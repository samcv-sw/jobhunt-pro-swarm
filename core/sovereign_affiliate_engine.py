"""
Sovereign Affiliate & Viral Growth Engine.
Enables user-driven viral loops with automated 20% recurring revenue share for referrers ($0 CAC).
"""

import time
import hashlib
from typing import Dict, List, Any, Optional

class SovereignAffiliateEngine:
    def __init__(self, commission_rate: float = 0.20):
        self.commission_rate = commission_rate

    def generate_affiliate_link(self, user_id: str) -> Dict[str, Any]:
        ref_code = f"ref_{hashlib.md5(f'{user_id}:salt'.encode()).hexdigest()[:8]}"
        return {
            "user_id": user_id,
            "referral_code": ref_code,
            "referral_url": f"https://jobhunt-pro-frontend.vercel.app/?ref={ref_code}",
            "commission_rate": self.commission_rate,
            "payout_threshold_usd": 50.0
        }

    def process_referral_payout(self, ref_code: str, sale_amount_usd: float) -> Dict[str, Any]:
        payout = round(sale_amount_usd * self.commission_rate, 2)
        return {
            "referral_code": ref_code,
            "sale_amount_usd": sale_amount_usd,
            "payout_amount_usd": payout,
            "timestamp": time.time(),
            "status": "credited"
        }
