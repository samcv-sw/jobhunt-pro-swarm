"""
Web Router for Dynamic Programmatic SEO Pages & Sitemap.
"""

from fastapi import APIRouter, Response, HTTPException, Request
from fastapi.responses import HTMLResponse
from core.autonomous_seo_generator import seo_generator

router = APIRouter(tags=["SEO"])

@router.get("/sitemap.xml")
async def get_sitemap():
    """Serves dynamic XML sitemap for search engine crawlers."""
    xml_content = seo_generator.generate_xml_sitemap()
    return Response(content=xml_content, media_type="application/xml")

@router.get("/ar/jobs/{slug}", response_class=HTMLResponse)
async def get_ar_seo_landing_page(slug: str):
    """Serves programmatic Arabic SEO landing page with RTL layout and Cairo font."""
    slug_clean = slug.replace("ar-", "")
    parts = slug_clean.split("-")
    if len(parts) < 2:
        raise HTTPException(status_code=404, detail="الصفحة غير موجودة")
        
    city = parts[-1].title()
    role = " ".join(parts[:-1]).title()

    meta = seo_generator.generate_page_metadata(role, city, lang="ar")

    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{meta['title']}</title>
    <meta name="description" content="{meta['description']}">
    <link rel="canonical" href="{meta['canonical_url']}">
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {{ font-family: 'Cairo', 'IBM Plex Arabic', sans-serif; background: #0b0f19; color: #f8fafc; margin: 0; padding: 2rem; line-height: 1.8; }}
        .container {{ max-width: 900px; margin: 0 auto; text-align: center; }}
        h1 {{ font-size: 2.5rem; color: #38bdf8; margin-block-end: 1rem; }}
        p {{ font-size: 1.25rem; color: #94a3b8; margin-block-end: 1.5rem; }}
        .cta-btn {{ display: inline-block; background: linear-gradient(135deg, #10b981, #059669); color: white; padding: 1rem 2.5rem; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 1.1rem; }}
        .badge {{ display: inline-block; background: rgba(56, 189, 248, 0.1); color: #38bdf8; padding: 0.4rem 1rem; border-radius: 20px; font-weight: 600; margin-block-end: 1rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="badge">🔥 أحدث وظائف {meta['city_localized']} (2026)</div>
        <h1>وظائف {meta['role_localized']} المتاحة في {meta['city_localized']}</h1>
        <p>اعثر على أفضل فرص العمل لـ {meta['role_localized']} في {meta['city_localized']}. حسن سيرتك الذاتية تلقائياً وتجاوز أنظمة الفحص الـ ATS بضغطة زر مع منصة JobHunt Pro.</p>
        <a href="/register?lang=ar" class="cta-btn">قدم الآن مجاناً بالذكاء الاصطناعي 🚀</a>
    </div>
</body>
</html>"""
    return HTMLResponse(content=html_content)


@router.get("/jobs/{slug}", response_class=HTMLResponse)
async def get_seo_landing_page(slug: str, request: Request):
    """Serves programmatic SEO landing page based on URL slug with Schema.org JSON-LD."""
    from web.routers.pseo_web_router import get_pseo_job_page
    
    # Handle slug formats: role-in-city or role/city
    if "-in-" in slug:
        parts = slug.split("-in-")
        role_slug = parts[0]
        city_slug = parts[1]
    else:
        parts = slug.split("-")
        if len(parts) >= 2:
            city_slug = parts[-1]
            role_slug = "-".join(parts[:-1])
        else:
            role_slug = slug
            city_slug = "riyadh"

    return get_pseo_job_page(role_slug=role_slug, city_slug=city_slug, request=request)




