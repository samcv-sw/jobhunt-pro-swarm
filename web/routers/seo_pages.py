"""
Web Router for Dynamic Programmatic SEO Pages & Sitemap.
"""

from fastapi import APIRouter, Response, HTTPException
from fastapi.responses import HTMLResponse
from core.autonomous_seo_generator import seo_generator

router = APIRouter(tags=["SEO"])

@router.get("/sitemap.xml")
async def get_sitemap():
    """Serves dynamic XML sitemap for search engine crawlers."""
    xml_content = seo_generator.generate_xml_sitemap()
    return Response(content=xml_content, media_type="application/xml")

@router.get("/jobs/{slug}", response_class=HTMLResponse)
async def get_seo_landing_page(slug: str):
    """Serves programmatic SEO landing page based on URL slug."""
    parts = slug.split("-")
    if len(parts) < 2:
        raise HTTPException(status_code=404, detail="Page not found")
        
    city = parts[-1].title()
    role = " ".join(parts[:-1]).title()

    meta = seo_generator.generate_page_metadata(role, city)

    html_content = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meta['title']}</title>
    <meta name="description" content="{meta['description']}">
    <link rel="canonical" href="{meta['canonical_url']}">
    <style>
        body {{ font-family: 'Inter', system-ui, sans-serif; background: #0b0f19; color: #f8fafc; margin: 0; padding: 2rem; }}
        .container {{ max-width: 900px; margin: 0 auto; text-align: center; }}
        h1 {{ font-size: 2.5rem; color: #38bdf8; }}
        p {{ font-size: 1.2rem; color: #94a3b8; line-height: 1.7; }}
        .cta-btn {{ display: inline-block; background: linear-gradient(135deg, #2563eb, #3b82f6); color: white; padding: 1rem 2rem; border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 1.5rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{meta['role']} Jobs in {meta['city']}</h1>
        <p>Explore verified {meta['role']} job openings in {meta['city']}. Automatically tailor your resume and beat the ATS with JobHunt Pro's autonomous AI engine.</p>
        <a href="/register" class="cta-btn">Apply Now with AI</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)
