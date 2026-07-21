"""
Multi-Tenant White-Labeling & B2B SaaS Enterprise Service for JobHunt Pro.
Manages agency client profiles, domain mapping, custom CSS injection, and usage quotas.
"""

from typing import Dict, Any, List, Optional
import uuid

class TenantService:
    def __init__(self):
        self._tenants: Dict[str, Dict[str, Any]] = {
            "jobhuntpro.io": {
                "tenant_id": "tenant_default",
                "agency_name": "JobHunt Pro Global",
                "custom_domain": "jobhuntpro.io",
                "primary_color": "#2563EB",
                "font_family": "Cairo",
                "logo_url": "/static/img/logo.png",
                "monthly_plan_price": 49.0,
                "active_candidates": 1420,
                "cvs_generated": 8900,
                "is_active": True
            }
        }

    def register_tenant(self, agency_name: str, domain: str, primary_color: str = "#0D9488", font_family: str = "Cairo", logo_url: str = "") -> Dict[str, Any]:
        tenant_id = f"tenant_{uuid.uuid4().hex[:8]}"
        data = {
            "tenant_id": tenant_id,
            "agency_name": agency_name,
            "custom_domain": domain.lower(),
            "primary_color": primary_color,
            "font_family": font_family,
            "logo_url": logo_url or "/static/img/logo.png",
            "monthly_plan_price": 99.0,
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
