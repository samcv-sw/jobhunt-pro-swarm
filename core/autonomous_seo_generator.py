"""
Autonomous SEO & Dynamic Landing Generator.
Generates programmatic GCC-targeted landing pages, meta tags, schema.org microdata, and dynamic sitemaps for 100% organic Google traffic.
"""

from typing import Dict, List, Any
import datetime

class AutonomousSEOGenerator:
    """
    Programmatic SEO engine for JobHunt Pro.
    Generates localized job search landing pages and dynamic XML sitemap.
    """

    GCC_CITIES = [
        "Dubai", "Riyadh", "Abu Dhabi", "Doha", "Kuwait City", "Manama", "Muscat", "Beirut",
        "Jeddah", "Sharjah", "Dammam", "Khobar", "Amman", "Cairo", "Riyadh Front", "NEOM"
    ]
    GCC_CITIES_AR = {
        "Dubai": "دبي", "Riyadh": "الرياض", "Abu Dhabi": "أبوظبي", "Doha": "الدوحة",
        "Kuwait City": "الكويت", "Manama": "المنامة", "Muscat": "مسقط", "Beirut": "بيروت",
        "Jeddah": "جدة", "Sharjah": "الشارقة", "Dammam": "الدمام", "Khobar": "الخبر",
        "Amman": "عمان", "Cairo": "القاهرة", "NEOM": "نيوم"
    }
    GLOBAL_CITIES = [
        "London", "New York", "San Francisco", "Berlin", "Toronto", "Singapore", "Sydney", "Amsterdam",
        "Tokyo", "Paris", "Hong Kong", "Moscow", "Shanghai", "Beijing", "Sao Paulo", "Mumbai", "Seoul"
    ]
    JOB_TITLES = [
        "Software Engineer", "Data Scientist", "DevOps Engineer", "Backend Developer", "Frontend Developer",
        "Product Manager", "Project Manager", "Accountant", "Financial Analyst",
        "Marketing Specialist", "Sales Manager", "HR Specialist", "Graphic Designer",
        "AI Research Engineer", "Cybersecurity Specialist", "Cloud Architect", "Fullstack Developer",
        "Prompt Engineer", "MLOps Engineer", "Blockchain Developer", "Mobile Developer"
    ]
    JOB_TITLES_AR = {
        "Software Engineer": "مهندس برمجيات",
        "Data Scientist": "عالم بيانات",
        "DevOps Engineer": "مهندس DevOps",
        "Backend Developer": "مطور خلفية Backend",
        "Frontend Developer": "مطور واجهات Frontend",
        "Product Manager": "مدير منتج",
        "Project Manager": "مدير مشاريع",
        "Accountant": "محاسب",
        "Financial Analyst": "محلل مالي",
        "Marketing Specialist": "أخصائي تسويق",
        "Sales Manager": "مدير مبيعات",
        "HR Specialist": "أخصائي موارد بشرية",
        "AI Research Engineer": "مهندس أبحاث ذكاء اصطناعي",
        "Cybersecurity Specialist": "أخصائي أمن سيبراني",
        "Cloud Architect": "مهندس سحابي Cloud Architect",
        "Fullstack Developer": "مطور Fullstack"
    }


    def generate_page_metadata(self, role: str, city: str, lang: str = "en") -> Dict[str, Any]:
        """Generates SEO title, meta description, schema.org microdata, and RTL tags for a given role, city & language."""
        role_clean = role.strip().title()
        city_clean = city.strip().title()
        is_ar = lang.lower() == "ar"

        role_localized = self.JOB_TITLES_AR.get(role_clean, role_clean) if is_ar else role_clean
        city_localized = self.GCC_CITIES_AR.get(city_clean, city_clean) if is_ar else city_clean

        if is_ar:
            title = f"وظائف {role_localized} في {city_localized} (2026) | قدم الآن مجاناً بالذكاء الاصطناعي"
            description = f"اعثر على أفضل وظائف {role_localized} المتاحة في {city_localized}. حسن سيرتك الذاتية تلقائياً وتجاوز فحص الـ ATS بضغطة زر عبر JobHunt Pro."
            slug = f"ar-{role_clean.lower().replace(' ', '-')}-{city_clean.lower().replace(' ', '-')}"
            canonical_url = f"https://jobhuntpro.io/ar/jobs/{slug}"
        else:
            title = f"Top {role_clean} Jobs in {city_clean} (2026) | Apply Instantly with AI"
            description = f"Find the highest-paying {role_clean} vacancies in {city_clean}. Auto-tailor your CV, beat ATS screening, and apply with 1-click via JobHunt Pro."
            slug = f"{role_clean.lower().replace(' ', '-')}-{city_clean.lower().replace(' ', '-')}"
            canonical_url = f"https://jobhuntpro.io/jobs/{slug}"

        schema = {
            "@context": "https://schema.org",
            "@type": "JobPosting",
            "title": f"{role_localized} Positions in {city_localized}",
            "description": description,
            "inLanguage": "ar" if is_ar else "en",
            "jobLocation": {
                "@type": "Place",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": city_localized,
                    "addressCountry": "GCC"
                }
            },
            "employmentType": "FULL_TIME",
            "hiringOrganization": {
                "@type": "Organization",
                "name": "JobHunt Pro Partner Companies"
            }
        }

        return {
            "title": title,
            "description": description,
            "slug": slug,
            "role": role_clean,
            "city": city_clean,
            "role_localized": role_localized,
            "city_localized": city_localized,
            "lang": "ar" if is_ar else "en",
            "dir": "rtl" if is_ar else "ltr",
            "schema_json": schema,
            "canonical_url": canonical_url
        }

    def generate_all_landing_routes(self) -> List[Dict[str, Any]]:
        """Generates metadata list for all role + city combinations in English and Arabic."""
        routes = []
        for role in self.JOB_TITLES:
            for city in self.GCC_CITIES:
                routes.append(self.generate_page_metadata(role, city, lang="en"))
                routes.append(self.generate_page_metadata(role, city, lang="ar"))
        return routes

    def generate_xml_sitemap(self, base_url: str = "https://jobhuntpro.io") -> str:
        """Generates dynamic sitemap.xml containing all English & Arabic SEO landing pages."""
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        urls = [
            f"<url><loc>{base_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>",
            f"<url><loc>{base_url}/ar/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>"
        ]

        for route in self.generate_all_landing_routes():
            loc_path = f"/ar/jobs/{route['slug']}" if route["lang"] == "ar" else f"/jobs/{route['slug']}"
            urls.append(
                f"<url><loc>{base_url}{loc_path}</loc><lastmod>{now}</lastmod><priority>0.8</priority></url>"
            )

        sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{"".join(urls)}
</urlset>"""
        return sitemap_content

    def generate_bulk_sitemap_xml(self, base_url: str = "https://jobhuntpro.io") -> Dict[str, Any]:
        """Generates dynamic sitemap for global + GCC city combinations."""
        all_cities = self.GCC_CITIES + self.GLOBAL_CITIES
        total_routes = len(all_cities) * len(self.JOB_TITLES) * 2
        xml_content = self.generate_xml_sitemap(base_url)
        return {
            "total_routes": total_routes,
            "cities_count": len(all_cities),
            "roles_count": len(self.JOB_TITLES),
            "languages": ["en", "ar"],
            "sitemap_xml_length": len(xml_content),
            "status": "generated"
        }

seo_generator = AutonomousSEOGenerator()


