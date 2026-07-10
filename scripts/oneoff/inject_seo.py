import os

base_dir = r"c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\web\templates"

files = [
    os.path.join(base_dir, "_public_shell.html"),
    os.path.join(base_dir, "en", "_public_shell.html"),
    os.path.join(base_dir, "_base_tailwind.html"),
    os.path.join(base_dir, "en", "_base_tailwind.html"),
]

seo_block = """
    <!-- Global SEO & Hreflang Tags -->
    <link rel="canonical" href="https://jhfguf.pythonanywhere.com{{ request.url.path if request else '' }}">
    <link rel="alternate" hreflang="ar" href="https://jhfguf.pythonanywhere.com{{ request.url.path if request else '' }}">
    <link rel="alternate" hreflang="en" href="https://jhfguf.pythonanywhere.com/en{{ request.url.path if request else '' }}">
    <link rel="alternate" hreflang="x-default" href="https://jhfguf.pythonanywhere.com{{ request.url.path if request else '' }}">
    
    <!-- JSON-LD Structured Data for Organization -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "JobHunt Pro",
      "url": "https://jhfguf.pythonanywhere.com",
      "logo": "https://jhfguf.pythonanywhere.com/static/img/icon-192.png",
      "description": "AI-Powered Job Hunting Platform",
      "sameAs": [
        "https://www.linkedin.com/company/jobhunt-pro"
      ]
    }
    </script>
"""

preload_block = """
    <!-- Resource Hints & Preloads -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="preload" href="/static/css/premium-ui.css" as="style">
"""

for filepath in files:
    if not os.path.exists(filepath):
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "<!-- Global SEO & Hreflang Tags -->" not in content:
        # Inject right before <title>
        content = content.replace("<title>", seo_block + preload_block + "\n    <title>")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.debug(f"Injected SEO & Preload into {filepath}")
    else:
        logger.debug(f"Already injected in {filepath}")
