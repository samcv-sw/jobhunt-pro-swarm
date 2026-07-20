"""
Automated XML Sitemap Generator for JobHunt Pro SaaS
Builds Google-compliant sitemap.xml dynamically from system routes, blog posts, and active job listings.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any

DEFAULT_STATIC_ROUTES = [
    {"loc": "/", "changefreq": "daily", "priority": "1.0"},
    {"loc": "/dashboard", "changefreq": "daily", "priority": "0.9"},
    {"loc": "/blog", "changefreq": "daily", "priority": "0.8"},
    {"loc": "/privacy", "changefreq": "monthly", "priority": "0.3"},
    {"loc": "/terms", "changefreq": "monthly", "priority": "0.3"},
]

def generate_sitemap_xml(
    base_url: str = "https://jobhuntpro.app",
    extra_urls: List[Dict[str, str]] = None,
    blog_slugs: List[str] = None
) -> str:
    """
    Generates a valid XML sitemap string.
    """
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    now_iso = datetime.utcnow().strftime("%Y-%m-%d")

    # Add default static routes
    all_routes = list(DEFAULT_STATIC_ROUTES)
    if extra_urls:
        all_routes.extend(extra_urls)

    for route in all_routes:
        url_elem = ET.SubElement(urlset, "url")
        loc_elem = ET.SubElement(url_elem, "loc")
        loc_elem.text = f"{base_url.rstrip('/')}{route['loc']}"

        lastmod_elem = ET.SubElement(url_elem, "lastmod")
        lastmod_elem.text = route.get("lastmod", now_iso)

        changefreq_elem = ET.SubElement(url_elem, "changefreq")
        changefreq_elem.text = route.get("changefreq", "weekly")

        priority_elem = ET.SubElement(url_elem, "priority")
        priority_elem.text = route.get("priority", "0.5")

    # Add blog posts if provided
    if blog_slugs:
        for slug in blog_slugs:
            url_elem = ET.SubElement(urlset, "url")
            loc_elem = ET.SubElement(url_elem, "loc")
            loc_elem.text = f"{base_url.rstrip('/')}/blog/{slug}"
            lastmod_elem = ET.SubElement(url_elem, "lastmod")
            lastmod_elem.text = now_iso
            changefreq_elem = ET.SubElement(url_elem, "weekly")
            changefreq_elem.text = "weekly"
            priority_elem = ET.SubElement(url_elem, "priority")
            priority_elem.text = "0.7"

    xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
    raw_xml = ET.tostring(urlset, encoding="utf-8").decode("utf-8")
    return xml_declaration + raw_xml
