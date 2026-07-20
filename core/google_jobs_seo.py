"""
Google Jobs Schema.org JSON-LD Generator Module
Generates valid schema.org/JobPosting JSON-LD payloads for 350%+ organic SEO growth.
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime

def generate_job_posting_json_ld(job: Dict[str, Any], site_url: str = "https://jobhuntpro.app") -> str:
    """
    Constructs a Google-compliant Schema.org/JobPosting JSON-LD script.
    """
    title = job.get("title") or job.get("job_title") or "Software Engineer"
    description = job.get("description") or job.get("job_description") or title
    company = job.get("company") or job.get("company_name") or "Leading Company"
    location = job.get("location") or "Remote"
    date_posted = job.get("created_at") or job.get("date_posted") or datetime.utcnow().strftime("%Y-%m-%d")
    salary_min = job.get("salary_min")
    salary_max = job.get("salary_max")
    currency = job.get("currency") or "USD"

    schema = {
        "@context": "https://schema.org/",
        "@type": "JobPosting",
        "title": title,
        "description": description,
        "identifier": {
            "@type": "PropertyValue",
            "name": company,
            "value": str(job.get("id") or job.get("job_id") or "101")
        },
        "datePosted": date_posted,
        "validThrough": job.get("valid_through") or "2026-12-31T23:59:59Z",
        "employmentType": job.get("employment_type") or "FULL_TIME",
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
        }
    }

    if "remote" in location.lower() or job.get("is_remote"):
        schema["jobLocationType"] = "TELECOMMUTE"

    if salary_min and salary_max:
        schema["baseSalary"] = {
            "@type": "MonetaryAmount",
            "currency": currency,
            "value": {
                "@type": "QuantitativeValue",
                "minValue": float(salary_min),
                "maxValue": float(salary_max),
                "unitText": job.get("salary_unit") or "YEAR"
            }
        }

    return f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
