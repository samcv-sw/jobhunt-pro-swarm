"""
JobHunt Pro — Programmatic SEO (pSEO) Job Farm Engine
Generates thousands of Google-indexed, hyper-localized job landing pages with Schema.org JobPosting
JSON-LD structured data to drive free organic search engine traffic across GCC cities.
"""

from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger(__name__)

TOP_GCC_LOCATIONS = [
    {"city": "Riyadh", "country": "Saudi Arabia", "country_code": "SA", "currency": "SAR", "avg_salary": "25,000 - 45,000 SAR"},
    {"city": "Dubai", "country": "United Arab Emirates", "country_code": "AE", "currency": "AED", "avg_salary": "28,000 - 50,000 AED"},
    {"city": "Abu Dhabi", "country": "United Arab Emirates", "country_code": "AE", "currency": "AED", "avg_salary": "30,000 - 55,000 AED"},
    {"city": "Doha", "country": "Qatar", "country_code": "QA", "currency": "QAR", "avg_salary": "22,000 - 40,000 QAR"},
    {"city": "Jeddah", "country": "Saudi Arabia", "country_code": "SA", "currency": "SAR", "avg_salary": "20,000 - 38,000 SAR"},
    {"city": "Kuwait City", "country": "Kuwait", "country_code": "KW", "currency": "KWD", "avg_salary": "1,800 - 3,200 KWD"}
]

TOP_JOB_CATEGORIES = [
    "Software Engineer", "AI & ML Specialist", "Cloud Solutions Architect",
    "Product Manager", "Data Scientist", "Cybersecurity Lead", "Fintech Developer"
]


class PSEOJobFarm:
    """Automated Programmatic SEO Engine for High-Intent Job Searches."""

    def generate_job_posting_json_ld(
        self,
        job_title: str,
        city: str,
        country: str,
        company_name: str = "Premier Enterprise Partner",
        currency: str = "SAR",
        min_salary: int = 25000,
        max_salary: int = 45000
    ) -> Dict[str, Any]:
        """Generate Google Search Central compliant schema.org/JobPosting structured data."""
        return {
            "@context": "https://schema.org/",
            "@type": "JobPosting",
            "title": f"{job_title} in {city}, {country}",
            "description": f"<p>Exciting opportunity for a top-tier {job_title} to join an enterprise ecosystem in {city}, {country}. Autonomous application powered by JobHunt Pro.</p>",
            "identifier": {
                "@type": "PropertyValue",
                "name": company_name,
                "value": f"JOB-{city.upper()[:3]}-{job_title.replace(' ', '-').upper()}"
            },
            "datePosted": "2026-08-01",
            "validThrough": "2026-12-31",
            "employmentType": "FULL_TIME",
            "hiringOrganization": {
                "@type": "Organization",
                "name": company_name,
                "sameAs": "https://jobhuntpro.io"
            },
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": city,
                    "addressCountry": country
                }
            },
            "baseSalary": {
                "@type": "MonetaryAmount",
                "currency": currency,
                "value": {
                    "@type": "QuantitativeValue",
                    "minValue": min_salary,
                    "maxValue": max_salary,
                    "unitText": "MONTH"
                }
            }
        }

    def generate_seo_page_payload(self, role_slug: str, city_slug: str) -> Dict[str, Any]:
        """Generate complete SEO page metadata, content, and structured schema."""
        role_clean = role_slug.replace("-", " ").title()
        city_clean = city_slug.replace("-", " ").title()

        loc_match = next((l for l in TOP_GCC_LOCATIONS if l["city"].lower() == city_clean.lower()), TOP_GCC_LOCATIONS[0])
        country = loc_match["country"]
        currency = loc_match["currency"]

        schema_json = self.generate_job_posting_json_ld(role_clean, loc_match["city"], country, currency=currency)

        return {
            "slug": f"/jobs/{role_slug}/{city_slug}",
            "meta_title": f"Top {role_clean} Jobs in {loc_match['city']}, {country} (2026 Salary & Direct Apply)",
            "meta_description": f"Explore verified {role_clean} job vacancies in {loc_match['city']}. Average salary {loc_match['avg_salary']}. Apply automatically with AI in 1-click.",
            "h1_heading": f"{role_clean} Careers in {loc_match['city']}, {country}",
            "market_insights": {
                "average_salary_range": loc_match["avg_salary"],
                "active_hiring_companies": ["Saudi Aramco Ecosystem", "NEOM Digital", "DIFC Fintechs", "Emirates Group Partner"],
                "in_demand_skills": ["Cloud Scalability", "System Architecture", "Security Governance", "AI Integration"]
            },
            "schema_job_posting_json_ld": schema_json,
            "cta_text": f"Apply to 50+ {role_clean} Jobs in {loc_match['city']} with 1-Click AI"
        }

    def get_programmatic_sitemap_urls(self) -> List[str]:
        """Generate full list of programmatic SEO routes for sitemap.xml."""
        urls = []
        for role in TOP_JOB_CATEGORIES:
            role_slug = role.lower().replace("&", "and").replace(" ", "-")
            for loc in TOP_GCC_LOCATIONS:
                city_slug = loc["city"].lower().replace(" ", "-")
                urls.append(f"https://jobhuntpro.io/jobs/{role_slug}/{city_slug}")
        return urls


# Global singleton instance
pseo_job_farm = PSEOJobFarm()
