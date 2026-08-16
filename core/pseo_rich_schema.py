"""
core/pseo_rich_schema.py
Enterprise pSEO & Google Jobs Rich Schema.org Engine
JobHunt Pro SaaS — 360° Organic Search Dominance & Google Jobs Indexing Automation

Features:
1. Google Jobs Schema.org/JobPosting with directApply, telecommute geo-fencing, and structured skills.
2. Real-time Multi-Currency Conversion & Parity Normalization (USD, EUR, GBP, SAR, AED, CNY, RUB).
3. Google Indexing API Direct Ping Webhook Payload Generator (URL_UPDATED / URL_DELETED).
4. Social OpenGraph & Twitter Card Metadata Generator for viral programmatic SEO pages.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("PSEORichSchema")

# Baseline Currency Conversion Rates to USD (for parity calculation)
CURRENCY_RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.28,
    "SAR": 0.27,
    "AED": 0.27,
    "CNY": 0.14,
    "RUB": 0.011,
    "CAD": 0.74,
    "AUD": 0.66,
    "QAR": 0.27,
    "KWD": 3.25,
}


class PSEORichSchemaEngine:
    """
    Programmatic SEO & Structured Data Powerhouse.
    """

    @staticmethod
    def normalize_salary(
        amount: float, source_currency: str = "USD", target_currency: str = "USD"
    ) -> float:
        """Converts salaries between supported international currencies."""
        src = source_currency.upper().strip()
        tgt = target_currency.upper().strip()
        
        rate_src = CURRENCY_RATES_TO_USD.get(src, 1.0)
        rate_tgt = CURRENCY_RATES_TO_USD.get(tgt, 1.0)

        usd_val = amount * rate_src
        return round(usd_val / rate_tgt, 2)

    @classmethod
    def generate_enterprise_job_posting_json_ld(
        cls, job: Dict[str, Any], site_url: str = "https://jobhuntpro.app"
    ) -> str:
        """
        Builds a Google Jobs Schema.org JSON-LD string with directApply and geo-fencing.
        """
        title = job.get("title") or job.get("job_title") or "Executive Professional"
        description = job.get("description") or job.get("job_description") or title
        company = job.get("company") or job.get("company_name") or "Global Enterprise"
        location = job.get("location") or "Remote"
        job_id = str(job.get("id") or job.get("job_id") or "101")
        apply_url = job.get("apply_url") or f"{site_url}/jobs/{job_id}/apply"
        
        date_posted = job.get("created_at") or job.get("date_posted")
        if not date_posted:
            date_posted = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        valid_through = job.get("valid_through")
        if not valid_through:
            # 60 days standard validity
            future = datetime.now(timezone.utc) + timedelta(days=60)
            valid_through = future.strftime("%Y-%m-%dT23:59:59Z")

        schema: Dict[str, Any] = {
            "@context": "https://schema.org/",
            "@type": "JobPosting",
            "title": title,
            "description": description,
            "identifier": {
                "@type": "PropertyValue",
                "name": company,
                "value": job_id
            },
            "datePosted": str(date_posted)[:10],
            "validThrough": str(valid_through),
            "employmentType": job.get("employment_type") or "FULL_TIME",
            "directApply": True,
            "hiringOrganization": {
                "@type": "Organization",
                "name": company,
                "sameAs": job.get("company_url") or site_url,
                "logo": job.get("company_logo") or f"{site_url}/static/images/logo.png"
            },
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": location,
                    "addressCountry": job.get("country") or "US"
                }
            },
            "url": apply_url,
        }

        # Telecommute / Remote Work handling
        if "remote" in location.lower() or job.get("is_remote"):
            schema["jobLocationType"] = "TELECOMMUTE"
            schema["applicantLocationRequirements"] = {
                "@type": "Country",
                "name": job.get("country") or "Worldwide"
            }

        # Structured Salary formatting
        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")
        currency = job.get("currency") or "USD"

        if salary_min is not None:
            min_val = float(salary_min)
            max_val = float(salary_max) if salary_max is not None else min_val
            schema["baseSalary"] = {
                "@type": "MonetaryAmount",
                "currency": currency.upper(),
                "value": {
                    "@type": "QuantitativeValue",
                    "minValue": min_val,
                    "maxValue": max_val,
                    "unitText": job.get("salary_unit") or "YEAR"
                }
            }

        return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'

    @classmethod
    def generate_google_indexing_api_payload(cls, url: str, action: str = "URL_UPDATED") -> Dict[str, Any]:
        """
        Creates a valid Google Indexing API v3 notification body.
        action: 'URL_UPDATED' or 'URL_DELETED'
        """
        return {
            "url": url,
            "type": action,
        }

    @classmethod
    def generate_social_meta_tags(
        cls, title: str, description: str, page_url: str, image_url: Optional[str] = None
    ) -> str:
        """
        Builds OpenGraph and Twitter Cards HTML meta tags for social viral growth.
        """
        img = image_url or "https://jobhuntpro.app/static/images/og-banner.png"
        tags = [
            f'<meta property="og:title" content="{title}">',
            f'<meta property="og:description" content="{description[:160]}">',
            f'<meta property="og:url" content="{page_url}">',
            f'<meta property="og:image" content="{img}">',
            '<meta property="og:type" content="website">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{title}">',
            f'<meta name="twitter:description" content="{description[:160]}">',
            f'<meta name="twitter:image" content="{img}">',
        ]
        return "\n".join(tags)


# Global singleton instance
global_pseo_rich_schema = PSEORichSchemaEngine()
