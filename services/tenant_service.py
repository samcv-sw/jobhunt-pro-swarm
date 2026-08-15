"""
Multi-Tenant White-Labeling & B2B SaaS Enterprise Service for JobHunt Pro.
Manages agency client profiles, domain mapping, custom CSS injection, and usage quotas.
"""

from typing import Dict, Any, List, Optional
import uuid

class TenantService:
    def __init__(self):
        self._tiers: Dict[str, Dict[str, Any]] = {
            "starter": {
                "name": "Starter",
                "price": "$149/mo",
                "price_usd": 149.0,
                "candidate_unlocks": 50,
                "sdr_credits": 100,
                "seats": 1,
                "features": ["50 candidate unlocks", "100 SDR credits", "ATS Match Score Access", "Standard Support"]
            },
            "agency_swarm": {
                "name": "Agency Swarm / Pro",
                "price": "$299/mo",
                "price_usd": 299.0,
                "candidate_unlocks": 250,
                "sdr_credits": 500,
                "seats": 3,
                "features": ["250 candidate unlocks", "500 SDR credits", "3 seats", "Priority Support"]
            },
            "enterprise_sovereign": {
                "name": "Enterprise Sovereign",
                "price": "$499/mo",
                "price_usd": 499.0,
                "candidate_unlocks": "Unlimited",
                "sdr_credits": 1500,
                "seats": "Unlimited",
                "features": ["Unlimited candidate unlocks", "1,500 SDR credits", "White-label", "Custom Domain", "24/7 SLA"]
            }
        }
        self._tenants: Dict[str, Dict[str, Any]] = {
            "jobhuntpro.io": {
                "tenant_id": "tenant_default",
                "agency_name": "JobHunt Pro Global",
                "custom_domain": "jobhuntpro.io",
                "primary_color": "#2563EB",
                "font_family": "Cairo",
                "logo_url": "/static/img/logo.png",
                "monthly_plan_price": 149.0,
                "active_candidates": 1420,
                "cvs_generated": 8900,
                "is_active": True
            }
        }

    def get_subscription_tiers(self) -> Dict[str, Any]:
        """Return standardized B2B recruiter tiers ($149, $299, $499)."""
        return {"status": "success", "tiers": list(self._tiers.values())}

    def register_tenant(
        self,
        agency_name: str,
        domain: str,
        primary_color: str = "#0D9488",
        font_family: str = "Cairo",
        logo_url: str = "",
        tier_name: str = "starter",
        monthly_plan_price: Optional[float] = None
    ) -> Dict[str, Any]:
        tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        tier = self._tiers.get(tier_name.lower(), self._tiers["starter"])
        price = monthly_plan_price if monthly_plan_price is not None else tier["price_usd"]
        data = {
            "tenant_id": tenant_id,
            "agency_name": agency_name,
            "custom_domain": domain.lower(),
            "primary_color": primary_color,
            "font_family": font_family,
            "logo_url": logo_url or "/static/img/logo.png",
            "monthly_plan_price": price,
            "plan_tier": tier["name"],
            "active_candidates": 0,
            "cvs_generated": 0,
            "is_active": True
        }
        self._tenants[domain.lower()] = data
        return data

    def resolve_tenant_by_host(self, host: str) -> Dict[str, Any]:
        clean_host = host.split(":")[0].lower().replace("www.", "")
        return self._tenants.get(clean_host) or self._tenants["jobhuntpro.io"]

    def list_all_tenants(self) -> List[Dict[str, Any]]:
        return list(self._tenants.values())

tenant_service = TenantService()
