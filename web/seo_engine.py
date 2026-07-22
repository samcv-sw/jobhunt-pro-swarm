"""
JobHunt Pro - Enterprise Dynamic SEO, GEO & LLM Indexing Engine
Generates Schema.org JSON-LD microdata, OpenGraph tags, and llms.txt endpoints for 100+ platform pages.
"""

import json
from typing import Dict, Any, List

class SEOEngine:
    SITE_NAME = "JobHunt Pro"
    BASE_URL = "https://jobhunt-pro.com"

    @classmethod
    def generate_json_ld(cls, page_type: str, title: str, description: str, path: str, extra_data: Dict[str, Any] = None) -> str:
        """Generates dynamic Schema.org JSON-LD string."""
        url = f"{cls.BASE_URL}{path}"

        schema = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "description": description,
            "url": url,
            "isPartOf": {
                "@type": "WebSite",
                "name": cls.SITE_NAME,
                "url": cls.BASE_URL
            },
            "publisher": {
                "@type": "Organization",
                "name": cls.SITE_NAME,
                "url": cls.BASE_URL,
                "logo": {
                    "@type": "ImageObject",
                    "url": f"{cls.BASE_URL}/static/img/logo.png"
                }
            }
        }

        if page_type == "job_posting" and extra_data:
            schema["@type"] = "JobPosting"
            schema["title"] = extra_data.get("job_title", title)
            schema["hiringOrganization"] = {
                "@type": "Organization",
                "name": extra_data.get("company_name", cls.SITE_NAME)
            }
            schema["jobLocation"] = {
                "@type": "Place",
                "address": extra_data.get("location", "Remote")
            }

        elif page_type == "faq" and extra_data and "faqs" in extra_data:
            schema["@type"] = "FAQPage"
            schema["mainEntity"] = [
                {
                    "@type": "Question",
                    "name": q.get("question"),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": q.get("answer")
                    }
                }
                for q in extra_data["faqs"]
            ]

        return json.dumps(schema, ensure_ascii=False, indent=2)

    @classmethod
    def generate_llms_txt(cls, routes_manifest: List[Dict[str, str]]) -> str:
        """Generates AI-ready llms.txt format for LLM Crawlers (Perplexity, ChatGPT, Claude)."""
        content = [
            f"# {cls.SITE_NAME} - Dynamic Platform Manifest for AI Agents",
            f"> Base URL: {cls.BASE_URL}",
            "> Architecture: High-Performance Autonomous SaaS Empire & Career Engine",
            "",
            "## Primary Capabilities",
            "- AI Resume Tailoring & ATS Optimization",
            "- Autonomous Job Application Swarm",
            "- Live AI Interview Coaching & Salary Negotiation",
            "- B2B Recruiter & Employer Matching System",
            "",
            "## Available Platform Endpoints & Pages"
        ]

        for route in routes_manifest:
            title = route.get("title", "Page")
            path = route.get("path", "/")
            desc = route.get("description", "")
            content.append(f"- [{title}]({cls.BASE_URL}{path}): {desc}")

        return "\n".join(content)
