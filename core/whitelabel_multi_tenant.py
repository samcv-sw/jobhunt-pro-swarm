"""
B2B White-Label & Multi-Tenant Portal Engine
JobHunt Pro SaaS - Allows recruitment agencies and universities to launch branded portals.
"""
import time
from typing import Dict, List, Any, Optional


class WhitelabelMultiTenantEngine:
    """
    Manages custom-branded career acceleration portals for B2B staffing firms and universities.
    """

    DEFAULT_TENANTS = {
        "riyadh_tech_academy": {
            "tenant_id": "tnt_riyadh_01",
            "org_name": "Riyadh Tech Career Institute",
            "subdomain": "riyadh-tech",
            "custom_domain": "careers.riyadhtech.sa",
            "primary_color": "#00d4aa",
            "logo_url": "/static/img/tenants/riyadh_tech.png",
            "allocated_seats": 500,
            "used_seats": 142,
            "plan": "Enterprise Academic",
            "status": "active"
        },
        "gulf_talent_partners": {
            "tenant_id": "tnt_gulf_02",
            "org_name": "Gulf Executive Search Partners",
            "subdomain": "gulf-talent",
            "custom_domain": "portal.gulftalentpartners.com",
            "primary_color": "#f0c040",
            "logo_url": "/static/img/tenants/gulf_partners.png",
            "allocated_seats": 2500,
            "used_seats": 890,
            "plan": "Wholesale Staffing VIP",
            "status": "active"
        }
    }

    @classmethod
    def get_tenant_config(cls, tenant_slug: str) -> Dict[str, Any]:
        """Resolves tenant configuration by slug or custom domain."""
        slug = tenant_slug.lower().strip()
        if slug in cls.DEFAULT_TENANTS:
            return {
                "found": True,
                "tenant": cls.DEFAULT_TENANTS[slug]
            }

        # Dynamic fallback for new self-service agency onboarding
        return {
            "found": True,
            "tenant": {
                "tenant_id": f"tnt_{slug[:8]}",
                "org_name": f"{slug.replace('-', ' ').title()} Portal",
                "subdomain": slug,
                "custom_domain": f"{slug}.jobhunt-pro.com",
                "primary_color": "#3b82f6",
                "logo_url": "/static/img/default_logo.png",
                "allocated_seats": 100,
                "used_seats": 1,
                "plan": "Self-Serve White-Label",
                "status": "active"
            }
        }

    @classmethod
    def register_new_tenant(
        cls,
        org_name: str,
        admin_email: str,
        desired_subdomain: str,
        primary_color: str = "#00f0ff",
        seats_quota: int = 100
    ) -> Dict[str, Any]:
        """Provisions a new isolated white-label portal instance."""
        slug = desired_subdomain.lower().replace(" ", "-").replace(".", "-")
        tenant_record = {
            "tenant_id": f"tnt_{int(time.time())}",
            "org_name": org_name,
            "admin_email": admin_email,
            "subdomain": slug,
            "portal_url": f"https://{slug}.jobhunt-pro.com",
            "primary_color": primary_color,
            "allocated_seats": seats_quota,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "provisioned_active"
        }
        cls.DEFAULT_TENANTS[slug] = tenant_record
        return {
            "status": "success",
            "message": f"White-label portal for '{org_name}' successfully provisioned!",
            "portal_config": tenant_record
        }


# Global singleton instance
whitelabel_engine = WhitelabelMultiTenantEngine()
