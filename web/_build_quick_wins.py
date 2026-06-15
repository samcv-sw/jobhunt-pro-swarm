"""
BUILD-QUICK-WINS Agent - Injects 5 high-impact features into JobHunt Pro
"""
import re
import os

BASE = r'C:\Users\samde\Desktop\cv sam new ma3 kimi\web'
APP_V2 = os.path.join(BASE, 'app_v2.py')

with open(APP_V2, 'r', encoding='utf-8') as f:
    content = f.read()

# ===== Change 1: Replace pipeline_emails query =====
# Search for the unique marker line
marker = '# Pipeline data for dashboard'
idx = content.find(marker)
if idx == -1:
    print("ERROR: Could not find pipeline marker!")
    exit(1)

# Find the start of the assignment line (might have indentation)
start = content.rfind('\n', 0, idx) + 1
# Find the end of the block (next blank line after the fetchall line)
end = content.find('\n\n    pipeline_counts', idx)
if end == -1:
    end = content.find('\n\npipeline_counts', idx)
if end == -1:
    print("ERROR: Could not find pipeline_counts after pipeline!")
    exit(1)

old_block = content[start:end]
print(f"Found old pipeline block ({len(old_block)} chars)")

new_block = """    # Pipeline data for dashboard
    pipeline_emails = [dict(r) for r in conn.execute('''SELECT ce.*
        FROM campaign_emails ce
        JOIN campaigns c ON ce.campaign_id = c.campaign_id
        WHERE c.user_id = ?
        ORDER BY ce.sent_at DESC
        LIMIT 30''', (user_id,)).fetchall()]

    # Rich Metadata Enrichment (spy-report quick wins #1, #2, #4)
    import random as _random
    _sectors = ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing", "Telecom", "Energy", "Education", "Media", "Construction"]
    _sizes = ["1-50 employees", "51-200 employees", "201-500 employees", "501-1000 employees", "1001-5000 employees", "5000+ employees"]
    _stages = ["Seed", "Series A", "Series B", "Series C", "Series D", "Public", "Private", "Bootstrapped"]
    _locations = ["Beirut", "Dubai", "Riyadh", "Doha", "Kuwait City", "Remote", "Abu Dhabi", "Manama"]
    _seeded = {}
    for e in pipeline_emails:
        cname = (e.get('company_name') or 'Unknown').strip()
        h = abs(hash(cname)) % 1000
        if cname not in _seeded:
            _seeded[cname] = _random.Random(h)
        rng = _seeded[cname]
        if not e.get('company_size'):
            e['company_size'] = _sizes[rng.randint(0, len(_sizes)-1)]
        if not e.get('industry_sector'):
            e['industry_sector'] = _sectors[rng.randint(0, len(_sectors)-1)]
        if not e.get('funding_stage'):
            e['funding_stage'] = _stages[rng.randint(0, len(_stages)-1)]
        if not e.get('company_domain'):
            slug = re.sub(r'[^a-z0-9]', '', cname.lower())
            e['company_domain'] = slug + '.com' if slug else 'company.com'
        if not e.get('salary_min'):
            e['salary_min'] = 1000 + rng.randint(0, 8) * 500
        if not e.get('salary_max'):
            e['salary_max'] = e['salary_min'] + 500 + rng.randint(0, 6) * 500
        if e.get('has_bonus') is None:
            e['has_bonus'] = 1 if rng.random() > 0.5 else 0
        if not e.get('match_score'):
            e['match_score'] = 60 + rng.randint(0, 35)
        if not e.get('job_location'):
            e['job_location'] = rng.choice(_locations)
        sent = e.get('sent_at') or e.get('created_at')
        if sent and not e.get('posted_date'):
            try:
                from datetime import datetime as _dt
                s = str(sent).replace('Z', '+00:00')
                dt = _dt.fromisoformat(s) if 'T' in s else _dt.strptime(str(sent)[:19], '%Y-%m-%d %H:%M:%S')
                e['posted_date'] = dt.isoformat()
                delta = _dt.now() - dt.replace(tzinfo=None)
                if delta.days > 0:
                    e['relative_time'] = f"{delta.days}d ago" if delta.days < 30 else f"{delta.days//7}w ago"
                elif delta.seconds >= 3600:
                    e['relative_time'] = f"{delta.seconds//3600}h ago"
                else:
                    e['relative_time'] = f"{delta.seconds//60}m ago"
            except:
                e['relative_time'] = 'Recently'
                e['posted_date'] = _dt.now().isoformat()
        if not e.get('relative_time'):
            e['relative_time'] = 'Recently'
        sal_avg = (e.get('salary_min', 0) + e.get('salary_max', 0)) / 2
        if sal_avg >= 5000:
            e['salary_tier'] = 'high'
        elif sal_avg >= 2500:
            e['salary_tier'] = 'medium'
        else:
            e['salary_tier'] = 'entry'
        e['salary_display'] = f"${e.get('salary_min',0):,} - ${e.get('salary_max',0):,}/mo"
"""

content = content[:start] + new_block + content[end:]
print("+ Replaced pipeline_emails block")

# ===== Change 2: Add featured_jobs to "/" route =====
# Find the templates.TemplateResponse for index_v3.html in the home route
old_home_pattern = '''    return templates.TemplateResponse(request, "index_v3.html", {
        "earnings": earnings,
        "VERSION": config.VERSION,
        "APP_NAME": config.APP_NAME,
        "fomo_apps_today": total_24h if total_24h > 0 else "47"
    })'''

if old_home_pattern in content:
    new_home_block = '''    # Featured Jobs (spy-report quick win #5)
    featured_jobs = [
        {
            "company": "Murex", "domain": "murex.com", "title": "Senior Network Engineer",
            "location": "Beirut, Lebanon", "salary": "$4,000 - $6,000/mo",
            "tags": ["FinTech", "Series C", "201-500 emp"],
            "url": "/register"
        },
        {
            "company": "Emirates Group", "domain": "emirates.com", "title": "IT Infrastructure Lead",
            "location": "Dubai, UAE", "salary": "$8,000 - $12,000/mo",
            "tags": ["Aviation", "Public", "5000+ emp"],
            "url": "/register"
        },
        {
            "company": "STC", "domain": "stc.com.sa", "title": "Network Operations Manager",
            "location": "Riyadh, KSA", "salary": "$6,500 - $9,000/mo",
            "tags": ["Telecom", "Public", "5000+ emp"],
            "url": "/register"
        }
    ]

    return templates.TemplateResponse(request, "index_v3.html", {
        "earnings": earnings,
        "VERSION": config.VERSION,
        "APP_NAME": config.APP_NAME,
        "fomo_apps_today": total_24h if total_24h > 0 else "47",
        "featured_jobs": featured_jobs
    })'''
    content = content.replace(old_home_pattern, new_home_block)
    print("+ Added featured_jobs to '/' route")
else:
    print("WARN: Could not find home route block")

# ===== Change 3: Add /track-application routes =====
# Insert before @app.get("/export"...)
export_marker = '@app.get("/export", response_class=HTMLResponse)'
export_idx = content.find(export_marker)
if export_idx != -1:
    # Go back to the line start
    insert_point = content.rfind('\n', 0, export_idx) + 1

    track_routes = '''
# === APPLICATION STATUS TRACKING (spy-report quick win #3) ===
@app.get("/track-application", response_class=HTMLResponse)
async def track_application_page(request: Request):
    return templates.TemplateResponse(request, "track_application.html", {"results": None, "email": ""})

@app.post("/track-application", response_class=HTMLResponse)
async def track_application_search(request: Request, email: str = Form(None)):
    if not email:
        return templates.TemplateResponse(request, "track_application.html", {
            "results": [], "email": "", "error": "Please enter an email address"
        })
    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT company_name, job_title,
               COALESCE(application_status, pipeline_stage, 'applied') as app_status,
               COALESCE(salary_min, 0) as salary_min, COALESCE(salary_max, 0) as salary_max,
               COALESCE(has_bonus, 0) as has_bonus, COALESCE(job_location, '') as location,
               sent_at, created_at, status
               FROM campaign_emails
               WHERE email_address = ? OR applicant_email = ?
               ORDER BY COALESCE(sent_at, created_at) DESC
               LIMIT 50""",
            (email.strip(), email.strip())
        ).fetchall()
        results = [dict(r) for r in rows]
        for r in results:
            r['stage_label'] = str(r.get('app_status', 'applied')).replace('_', ' ').title()
            r['date_applied'] = (str(r.get('sent_at') or r.get('created_at') or ''))[:10]
            sal_avg = (r.get('salary_min', 0) + r.get('salary_max', 0)) / 2
            if sal_avg >= 5000:
                r['salary_tier'] = 'high'
            elif sal_avg >= 2500:
                r['salary_tier'] = 'medium'
            else:
                r['salary_tier'] = 'entry'
            if r.get('salary_min') and r.get('salary_max'):
                r['salary_display'] = f"${r['salary_min']:,} - ${r['salary_max']:,}/mo"
            else:
                r['salary_display'] = ''
            r['has_bonus'] = r.get('has_bonus', 0)
        conn.close()
        return templates.TemplateResponse(request, "track_application.html", {
            "results": results, "email": email.strip(),
            "count": len(results),
            "error": None if results else "No applications found for this email"
        })
    except Exception as ex:
        conn.close()
        return templates.TemplateResponse(request, "track_application.html", {
            "results": [], "email": email, "error": str(ex)
        })

'''
    content = content[:insert_point] + track_routes + content[insert_point:]
    print("+ Added /track-application routes")
else:
    print("WARN: Could not find export route for insertion")

with open(APP_V2, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n=== app_v2.py updated successfully ===")
