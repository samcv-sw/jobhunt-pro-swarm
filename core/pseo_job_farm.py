"""
JobHunt Pro — Programmatic SEO (pSEO) Job Farm Engine
Generates thousands of Google-indexed, hyper-localized job landing pages with Schema.org JobPosting
JSON-LD structured data and dynamic XML Sitemaps to drive high-intent organic search engine traffic.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

TOP_GCC_LOCATIONS = [
    {"city": "Riyadh", "country": "Saudi Arabia", "country_code": "SA", "currency": "SAR", "avg_salary": "25,000 - 45,000 SAR", "city_ar": "الرياض", "country_ar": "المملكة العربية السعودية"},
    {"city": "Dubai", "country": "United Arab Emirates", "country_code": "AE", "currency": "AED", "avg_salary": "28,000 - 50,000 AED", "city_ar": "دبي", "country_ar": "الإمارات العربية المتحدة"},
    {"city": "Abu Dhabi", "country": "United Arab Emirates", "country_code": "AE", "currency": "AED", "avg_salary": "30,000 - 55,000 AED", "city_ar": "أبو ظبي", "country_ar": "الإمارات العربية المتحدة"},
    {"city": "Doha", "country": "Qatar", "country_code": "QA", "currency": "QAR", "avg_salary": "22,000 - 40,000 QAR", "city_ar": "الدوحة", "country_ar": "قطر"},
    {"city": "Jeddah", "country": "Saudi Arabia", "country_code": "SA", "currency": "SAR", "avg_salary": "20,000 - 38,000 SAR", "city_ar": "جدة", "country_ar": "المملكة العربية السعودية"},
    {"city": "Kuwait City", "country": "Kuwait", "country_code": "KW", "currency": "KWD", "avg_salary": "1,800 - 3,200 KWD", "city_ar": "الكويت", "country_ar": "الكويت"},
    {"city": "Cairo", "country": "Egypt", "country_code": "EG", "currency": "EGP", "avg_salary": "45,000 - 90,000 EGP", "city_ar": "القاهرة", "country_ar": "مصر"}
]

TOP_JOB_CATEGORIES = [
    {"title": "Software Engineer", "title_ar": "مهندس برمجيات", "category": "Tech"},
    {"title": "AI & ML Specialist", "title_ar": "أخصائي ذكاء اصطناعي وتعلم آلة", "category": "AI"},
    {"title": "Cloud Solutions Architect", "title_ar": "مهندس حلول سحابية", "category": "Cloud"},
    {"title": "Product Manager", "title_ar": "مدير منتج تقني", "category": "Product"},
    {"title": "Data Scientist", "title_ar": "عالم بيانات", "category": "Data"},
    {"title": "Cybersecurity Lead", "title_ar": "قائد أمن سيبراني", "category": "Security"},
    {"title": "Fintech Developer", "title_ar": "مطور تقنيات مالية Fintech", "category": "Fintech"},
    {"title": "DevOps Engineer", "title_ar": "مهندس DevOps وبنية تحتية", "category": "Infrastructure"},
    {"title": "Full Stack Developer", "title_ar": "مطور Full Stack متكامل", "category": "Tech"}
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
            "datePosted": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
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
        role_match = next((r for r in TOP_JOB_CATEGORIES if r["title"].lower() == role_clean.lower()), {"title": role_clean, "title_ar": role_clean})

        country = loc_match["country"]
        currency = loc_match["currency"]

        schema_json = self.generate_job_posting_json_ld(role_clean, loc_match["city"], country, currency=currency)

        return {
            "slug": f"/jobs/{role_slug}/{city_slug}",
            "meta_title": f"Top {role_clean} Jobs in {loc_match['city']}, {country} (2026 Salary & Direct Apply)",
            "meta_title_ar": f"أفضل وظائف {role_match['title_ar']} في {loc_match['city_ar']}، {loc_match['country_ar']} (رواتب 2026 والتقديم المباشر)",
            "meta_description": f"Explore verified {role_clean} job vacancies in {loc_match['city']}. Average salary {loc_match['avg_salary']}. Apply automatically with AI in 1-click.",
            "meta_description_ar": f"اكتشف أحدث شواغر {role_match['title_ar']} في {loc_match['city_ar']}. متوسط الراتب {loc_match['avg_salary']}. تقديم فوري ذكي عبر الذكاء الاصطناعي.",
            "h1_heading": f"{role_clean} Careers in {loc_match['city']}, {country}",
            "h1_heading_ar": f"فرص عمل {role_match['title_ar']} في {loc_match['city_ar']}",
            "market_insights": {
                "average_salary_range": loc_match["avg_salary"],
                "active_hiring_companies": ["Saudi Aramco Ecosystem", "NEOM Digital", "DIFC Fintechs", "Emirates Group Partner", "STC Digital Hub"],
                "in_demand_skills": ["Cloud Scalability", "System Architecture", "Security Governance", "AI Integration", "FastAPI / Next.js"]
            },
            "schema_job_posting_json_ld": schema_json,
            "cta_text": f"Apply to 50+ {role_clean} Jobs in {loc_match['city']} with 1-Click AI",
            "cta_text_ar": f"قدّم على 50+ وظيفة {role_match['title_ar']} في {loc_match['city_ar']} بنقرة واحدة عبر الذكاء الاصطناعي"
        }

    def get_programmatic_sitemap_urls(self) -> List[str]:
        """Generate full list of programmatic SEO routes for sitemap.xml."""
        urls = []
        for role_item in TOP_JOB_CATEGORIES:
            role = role_item["title"]
            role_slug = role.lower().replace("&", "and").replace(" ", "-")
            for loc in TOP_GCC_LOCATIONS:
                city_slug = loc["city"].lower().replace(" ", "-")
                urls.append(f"https://jobhuntpro.io/jobs/{role_slug}/{city_slug}")
        return urls

    def generate_dynamic_xml_sitemap(self, base_url: str = "https://jobhuntpro.io") -> str:
        """
        Generates standard XML sitemap compliant with Google Search Central specifications.
        """
        urls = self.get_programmatic_sitemap_urls()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        ]

        # Core landing pages
        core_routes = ["/", "/ats-score", "/for-employers", "/telegram-app", "/pricing"]
        for route in core_routes:
            xml_lines.append("  <url>")
            xml_lines.append(f"    <loc>{base_url}{route}</loc>")
            xml_lines.append(f"    <lastmod>{today}</lastmod>")
            xml_lines.append("    <changefreq>daily</changefreq>")
            xml_lines.append("    <priority>1.0</priority>")
            xml_lines.append("  </url>")

        # Programmatic Job URLs
        for url in urls:
            xml_lines.append("  <url>")
            xml_lines.append(f"    <loc>{url}</loc>")
            xml_lines.append(f"    <lastmod>{today}</lastmod>")
            xml_lines.append("    <changefreq>weekly</changefreq>")
            xml_lines.append("    <priority>0.8</priority>")
            xml_lines.append("  </url>")

        xml_lines.append("</urlset>")
        return "\n".join(xml_lines)


# Global singleton instance
pseo_job_farm = PSEOJobFarm()
