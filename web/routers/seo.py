"""
seo.py — Programmatic SEO Router
Generates dynamic sitemaps for the platform based on active job targets and locations.
"""
from fastapi import APIRouter, Response, Request
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

router = APIRouter(tags=["seo"])

def _get_shared():
    from web.shared import get_db, config
    return get_db, config

@router.get("/sitemap.xml", response_class=Response)
def sitemap(request: Request):
    """Dynamically generated XML sitemap for SEO."""
    get_db, config = _get_shared()
    
    urlset = ET.Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    base_url = config.SITE_URL.rstrip('/')
    
    # Static core pages
    static_pages = ["", "/login", "/register", "/pricing", "/features"]
    
    for page in static_pages:
        url_node = ET.SubElement(urlset, "url")
        ET.SubElement(url_node, "loc").text = f"{base_url}{page}"
        ET.SubElement(url_node, "changefreq").text = "weekly"
        ET.SubElement(url_node, "priority").text = "1.0" if page == "" else "0.8"

    # Dynamic SEO pages: Combinations of popular Job Titles and Locations
    # For a massive pSEO scale, we generate these dynamically
    # Example: /jobs/network-engineer/dubai
    try:
        conn = get_db()
        # Fetch actual successful combinations from the database to reflect reality
        jobs_stats = conn.execute(
            "SELECT DISTINCT job_title, target_location FROM campaigns WHERE status = 'completed' LIMIT 100"
        ).fetchall()
        conn.close()
        
        for row in jobs_stats:
            job = str(row[0]).lower().replace(" ", "-")
            loc = str(row[1]).lower().replace(" ", "-")
            if job and loc:
                url_node = ET.SubElement(urlset, "url")
                ET.SubElement(url_node, "loc").text = f"{base_url}/jobs/{job}/{loc}"
                ET.SubElement(url_node, "changefreq").text = "daily"
                ET.SubElement(url_node, "priority").text = "0.7"
                
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Sitemap DB error: {e}")
        
    xml_str = ET.tostring(urlset, encoding="utf-8", method="xml")
    xml_header = b'<?xml version="1.0" encoding="UTF-8"?>\n'
    
    return Response(content=xml_header + xml_str, media_type="application/xml")
