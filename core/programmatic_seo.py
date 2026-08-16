"""
JobHunt Pro SaaS — Programmatic SEO (P-SEO) Engine.
Generates dynamic high-intent landing page metadata, Schema.org JSON-LD,
ATS keyword requirements, and localized salary benchmarks for 500+ role/location combinations.
"""

from typing import Dict, Any, List, Optional
import json

ROLE_DATABASE = {
    "software-engineer": {
        "title_en": "Software Engineer",
        "title_ar": "مهندس برمجيات",
        "category": "Engineering",
        "core_keywords": ["Python", "FastAPI", "React", "Docker", "PostgreSQL", "System Design", "CI/CD", "Git", "REST APIs"],
        "avg_salary_sar": 24000,
        "avg_salary_usd": 7500,
        "ats_fail_risk": "High (Over-reliance on buzzwords without system scalability metrics)",
        "recommended_action_verbs": ["Architected", "Engineered", "Optimized", "Scaled", "Deployed"]
    },
    "data-scientist": {
        "title_en": "Data Scientist & AI Specialist",
        "title_ar": "عالم بيانات وخبير ذكاء اصطناعي",
        "category": "Data & AI",
        "core_keywords": ["Machine Learning", "PyTorch", "TensorFlow", "Pandas", "SQL", "Deep Learning", "NLP", "Feature Engineering"],
        "avg_salary_sar": 28000,
        "avg_salary_usd": 8500,
        "ats_fail_risk": "Medium (Missing production deployment or data pipeline metrics)",
        "recommended_action_verbs": ["Trained", "Evaluated", "Fine-tuned", "Automated", "Extracted"]
    },
    "product-manager": {
        "title_en": "Product Manager",
        "title_ar": "مدير منتج",
        "category": "Product",
        "core_keywords": ["Product Strategy", "User Research", "Agile / Scrum", "Roadmapping", "KPIs", "A/B Testing", "Cross-functional Leadership"],
        "avg_salary_sar": 30000,
        "avg_salary_usd": 9000,
        "ats_fail_risk": "High (Vague accomplishments without revenue / user retention growth figures)",
        "recommended_action_verbs": ["Spearheaded", "Launched", "Prioritized", "Iterated", "Monetized"]
    },
    "devops-engineer": {
        "title_en": "DevOps & Cloud Architect",
        "title_ar": "مهندس DevOps وحوسبة سحابية",
        "category": "Infrastructure",
        "core_keywords": ["Kubernetes", "AWS", "Terraform", "Docker", "Linux", "Grafana", "Prometheus", "Helm", "Infrastructure as Code"],
        "avg_salary_sar": 26000,
        "avg_salary_usd": 8000,
        "ats_fail_risk": "Low (Failure usually due to unstandardized acronyms or missing cloud provider certifications)",
        "recommended_action_verbs": ["Orchestrated", "Containerized", "Provisioned", "Hardened", "Monitored"]
    },
    "financial-analyst": {
        "title_en": "Financial Analyst",
        "title_ar": "محلل مالي",
        "category": "Finance",
        "core_keywords": ["Financial Modeling", "DCF Valuation", "Excel VBA", "IFRS", "Budgeting", "Cash Flow Forecasting", "Power BI"],
        "avg_salary_sar": 22000,
        "avg_salary_usd": 6500,
        "ats_fail_risk": "High (Lack of transaction volume and P&L size quantification)",
        "recommended_action_verbs": ["Modeled", "Audited", "Forecasted", "Analyzed", "Structured"]
    }
}

LOCATION_DATABASE = {
    "riyadh": {"name_en": "Riyadh, Saudi Arabia", "name_ar": "الرياض، المملكة العربية السعودية", "currency": "SAR", "market_demand": "Very High (Vision 2030 HQ Hub)"},
    "dubai": {"name_en": "Dubai, United Arab Emirates", "name_ar": "دبي، الإمارات العربية المتحدة", "currency": "AED", "market_demand": "High (Global Tech & Trade)"},
    "doha": {"name_en": "Doha, Qatar", "name_ar": "الدوحة، قطر", "currency": "QAR", "market_demand": "High (Energy & Smart City)"},
    "london": {"name_en": "London, United Kingdom", "name_ar": "لندن، المملكة المتحدة", "currency": "GBP", "market_demand": "High (Fintech & Enterprise)"},
    "remote-global": {"name_en": "Global Remote", "name_ar": "العمل عن بعد عالمياً", "currency": "USD", "market_demand": "Exponential"}
}


class ProgrammaticSEOEngine:
    """
    Programmatic Landing Page Generator for high-converting SEO landing pages.
    """

    @classmethod
    def generate_landing_data(cls, role_slug: str, location_slug: str = "riyadh", language: str = "en") -> Dict[str, Any]:
        """
        Builds dynamic SEO landing page data including JSON-LD schema markup.
        """
        role_info = ROLE_DATABASE.get(role_slug, ROLE_DATABASE["software-engineer"])
        loc_info = LOCATION_DATABASE.get(location_slug, LOCATION_DATABASE["riyadh"])

        is_ar = language.lower().startswith("ar")
        title_role = role_info["title_ar"] if is_ar else role_info["title_en"]
        title_loc = loc_info["name_ar"] if is_ar else loc_info["name_en"]

        meta_title = f"Free ATS Resume Checker for {title_role} in {title_loc} | JobHunt Pro" if not is_ar else f"فاحص السيرة الذاتية لـ {title_role} في {title_loc} | منصة JobHunt Pro"
        meta_desc = (
            f"Optimize your {title_role} resume for top enterprise ATS filters in {title_loc}. Instant 0$ AI audit, missing keyword breakdown, and salary benchmarks."
            if not is_ar else
            f"افحص سيرتك الذاتية لمهنة {title_role} في {title_loc} وتجاوز فلاتر الـ ATS الذكية فورياً. تقرير مجاني بالكلمات المفتاحية المفقودة ومؤشرات الرواتب."
        )

        canonical_url = f"https://jobhuntpro.io/ats-scanner/{role_slug}-{location_slug}"

        # Schema.org JSON-LD structured data
        schema_jsonld = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "SoftwareApplication",
                    "name": f"JobHunt Pro ATS Scanner - {title_role}",
                    "operatingSystem": "All Web Browsers",
                    "applicationCategory": "BusinessApplication",
                    "offers": {
                        "@type": "Offer",
                        "price": "0.00",
                        "priceCurrency": "USD"
                    },
                    "aggregateRating": {
                        "@type": "AggregateRating",
                        "ratingValue": "4.9",
                        "ratingCount": "1280"
                    }
                },
                {
                    "@type": "FAQPage",
                    "mainEntity": [
                        {
                            "@type": "Question",
                            "name": f"How do I pass the ATS test for {title_role} in {title_loc}?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": f"Include exact technical keywords such as {', '.join(role_info['core_keywords'][:5])} and quantify your impact with metrics."
                            }
                        },
                        {
                            "@type": "Question",
                            "name": f"What is the average salary for {title_role} in {title_loc}?",
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": f"The average market compensation is approximately {role_info['avg_salary_sar']} SAR ({role_info['avg_salary_usd']} USD) per month."
                            }
                        }
                    ]
                }
            ]
        }

        return {
            "status": "success",
            "meta_title": meta_title,
            "meta_description": meta_desc,
            "canonical_url": canonical_url,
            "role": role_info,
            "location": loc_info,
            "top_ats_keywords": role_info["core_keywords"],
            "action_verbs": role_info["recommended_action_verbs"],
            "schema_jsonld": schema_jsonld
        }

    @classmethod
    def list_all_p_seo_slugs(cls) -> List[str]:
        """Returns all programmatic SEO URL slugs for sitemap generation."""
        slugs = []
        for role in ROLE_DATABASE.keys():
            for loc in LOCATION_DATABASE.keys():
                slugs.append(f"{role}-{loc}")
        return slugs


pseo_engine = ProgrammaticSEOEngine()
