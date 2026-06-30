import os
import io

app_file = "web/app_v2.py"
with io.open(app_file, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Inject Programmatic SEO Route
seo_route = """
# ==========================================
# PROGRAMMATIC SEO ROUTES
# ==========================================
@app.get("/tools/auto-apply/{job_title}", response_class=HTMLResponse)
async def seo_landing_page(request: Request, job_title: str):
    \"\"\"
    Programmatic SEO landing page generator.
    Captures traffic for specific long-tail keywords.
    \"\"\"
    title_clean = job_title.replace("-", " ").title()
    html_content = f\"\"\"
    <!DOCTYPE html>
    <html lang="en" dir="auto">
    <head>
        <meta charset="utf-8">
        <title>Auto Apply for {title_clean} Jobs | JobHunt Pro</title>
        <meta name="description" content="Automate your job applications for {title_clean} positions. JobHunt Pro uses AI to apply on your behalf 24/7.">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background: #0f172a; color: white; text-align: center; padding: 50px 20px; }}
            h1 {{ font-size: 3rem; margin-bottom: 20px; background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            p {{ font-size: 1.2rem; color: #94a3b8; max-width: 600px; margin: 0 auto 30px; line-height: 1.6; }}
            .cta {{ display: inline-block; padding: 15px 40px; background: #3b82f6; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 1.2rem; transition: background 0.3s; }}
            .cta:hover {{ background: #2563eb; }}
        </style>
    </head>
    <body>
        <h1>Automate {title_clean} Applications</h1>
        <p>Stop wasting hours applying manually. Our AI Agent acts as your personal recruiter, applying to hundreds of <strong>{title_clean}</strong> jobs while you sleep.</p>
        <a href="/register?ref=seo_{job_title}" class="cta">Start Your Free Agent Now 🚀</a>
    </body>
    </html>
    \"\"\"
    return HTMLResponse(html_content)
"""

if "PROGRAMMATIC SEO ROUTES" not in content:
    content = content.replace("# ==========================================\n# PYTHONANYWHERE WSGI BRIDGE (a2wsgi)\n# ==========================================", seo_route + "\n# ==========================================\n# PYTHONANYWHERE WSGI BRIDGE (a2wsgi)\n# ==========================================")

# 2. Inject Gamified Referral (Modify extension config)
config_target = """@app.get("/api/v1/extension/config")
async def extension_config():
    \"\"\"
    Kill-switch and algorithm updater for millions of extensions.
    \"\"\"
    return JSONResponse({
        "status": "active",
        "kill_switch": False,
        "human_jitter": {"min": 1500, "max": 3500},
        "latest_version": "2.0.0"
    })"""

config_replacement = """@app.get("/api/v1/extension/config")
async def extension_config(user_id: str = ""):
    \"\"\"
    Kill-switch and algorithm updater for millions of extensions.
    Implements Gamified Referral System (Unlocks 50/day if referred >= 3).
    \"\"\"
    daily_limit = 10
    if user_id:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                ref_count = conn.execute("SELECT COUNT(*) FROM referrals WHERE referrer_id = ? AND status='completed'", (user_id,)).fetchone()[0]
                if ref_count >= 3:
                    daily_limit = 50  # Gamified Growth Unlock!
        except Exception:
            pass

    return JSONResponse({
        "status": "active",
        "kill_switch": False,
        "human_jitter": {"min": 1500, "max": 3500},
        "latest_version": "2.0.0",
        "daily_limit": daily_limit
    })"""

if config_target in content:
    content = content.replace(config_target, config_replacement)

with io.open(app_file, "w", encoding="utf-8") as f:
    f.write(content)
print("Growth Hacks Injected into FastAPI!")
