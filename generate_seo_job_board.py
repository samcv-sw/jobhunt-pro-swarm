import sqlite3
import os
import json
from datetime import datetime

DB_PATH = "jobhunt_saas_v2.db"
OUTPUT_DIR = "docs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

def generate_job_board():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    jobs = []
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # Check if jobs table exists
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
            if cur.fetchone():
                cur.execute("SELECT title, company, location, url, posted_date FROM jobs ORDER BY id DESC LIMIT 500")
                jobs = [dict(row) for row in cur.fetchall()]
            conn.close()
        except Exception as e:
            print(f"Database error: {e}")

    # Fallback mock data if DB empty or missing locally (to ensure SEO page always exists)
    if not jobs:
        jobs = [
            {"title": "Senior Remote Python Developer", "company": "TechGlobal", "location": "Remote", "url": "#", "posted_date": str(datetime.now().date())},
            {"title": "AI Prompt Engineer", "company": "FutureAI", "location": "Remote", "url": "#", "posted_date": str(datetime.now().date())},
            {"title": "Full Stack Engineer", "company": "StartupX", "location": "Remote", "url": "#", "posted_date": str(datetime.now().date())}
        ]

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Find the best remote tech jobs worldwide. Updated daily. AI, Python, Full Stack, and more.">
    <title>JobHunt Pro - Remote Job Board</title>
    <style>
        body {{ font-family: 'Inter', sans-serif; background: #0f0f17; color: #fff; margin: 0; padding: 0; }}
        header {{ padding: 40px 20px; text-align: center; background: linear-gradient(135deg, #1e1e2f 0%, #12121c 100%); }}
        h1 {{ margin: 0; color: #00ff88; font-size: 2.5em; }}
        .container {{ max-width: 800px; margin: 40px auto; padding: 20px; }}
        .job-card {{ background: #1a1a2e; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #2a2a3e; transition: transform 0.2s; }}
        .job-card:hover {{ transform: translateY(-5px); border-color: #00ff88; }}
        .job-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #fff; }}
        .job-company {{ color: #94a3b8; font-size: 0.9em; margin-bottom: 15px; }}
        .apply-btn {{ display: inline-block; padding: 8px 16px; background: #00ff88; color: #000; text-decoration: none; border-radius: 4px; font-weight: bold; }}
        .ad-container {{ text-align: center; margin: 40px 0; padding: 20px; background: #1e1e2f; border: 1px dashed #444; color: #888; }}
    </style>
    <!-- GOOGLE ADSENSE (PASSIVE INCOME) -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1234567890123456" crossorigin="anonymous"></script>
</head>
<body>
    <header>
        <h1>JobHunt Pro Job Board</h1>
        <p>100% Remote Tech Jobs - Updated Daily by AI Swarm</p>
    </header>

    <div class="container">
        <!-- Top Ad Unit -->
        <div class="ad-container">
            <!-- AdSense Unit Placeholder -->
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="ca-pub-1234567890123456"
                 data-ad-slot="1234567890"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
        </div>

        <div id="job-list">
"""
    for job in jobs:
        html += f"""
            <div class="job-card">
                <div class="job-title">{job.get('title', 'Unknown Title')}</div>
                <div class="job-company">{job.get('company', 'Unknown')} • {job.get('location', 'Remote')} • {job.get('posted_date', '')}</div>
                <a href="{job.get('url', '#')}" class="apply-btn" target="_blank">Apply Now</a>
            </div>
"""

    html += """
        </div>
        
        <!-- Bottom Ad Unit -->
        <div class="ad-container">
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="ca-pub-1234567890123456"
                 data-ad-slot="0987654321"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
        </div>
    </div>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Generated SEO Job Board at {OUTPUT_FILE} with {len(jobs)} jobs.")

if __name__ == "__main__":
    generate_job_board()
