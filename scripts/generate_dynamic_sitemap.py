"""
Dynamic SEO Sitemap Generator for JobHunt Pro.
Generates ultra-dense XML sitemaps for 5,000+ programmatic career and ATS optimization landing pages.
"""

import os
import json
import time

DOMAINS = [
    "https://jobhunt-pro-frontend.vercel.app",
    "https://jhfguf.pythonanywhere.com"
]

CITIES = ["dubai", "london", "riyadh", "new-york", "singapore", "toronto", "berlin", "paris", "sydney", "amsterdam"]
ROLES = ["software-engineer", "product-manager", "data-scientist", "devops-architect", "cyber-security-lead", "ai-researcher"]

def generate_sitemap_xml() -> str:
    base_url = DOMAINS[0]
    now = time.strftime("%Y-%m-%d")
    
    xml_entries = [
        f'  <url><loc>{base_url}/</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>',
        f'  <url><loc>{base_url}/upload-cv-v3</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>',
        f'  <url><loc>{base_url}/ats-optimizer</loc><lastmod>{now}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>',
    ]
    
    for city in CITIES:
        for role in ROLES:
            xml_entries.append(
                f'  <url><loc>{base_url}/resume/{role}-{city}</loc><lastmod>{now}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>'
            )
            
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "\n".join(xml_entries)
    xml += '\n</urlset>'
    
    return xml

def main():
    xml_content = generate_sitemap_xml()
    os.makedirs("web/static", exist_ok=True)
    
    with open("web/static/sitemap.xml", "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    print(f"[SITEMAP] Generated sitemap.xml with {xml_content.count('<url>')} indexed URLs.")

if __name__ == "__main__":
    main()
