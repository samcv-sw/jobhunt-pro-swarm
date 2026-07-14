"""
NEWSLETTER EMPIRE GENERATOR (APEX PREDATOR UPGRADE)
===================================================
Automatically curates the top 10 remote jobs of the day into a premium
Substack-style newsletter, injecting high-value sponsorships.
"""

import datetime
import logging
import os
from typing import Any

import core.pg_sqlite_shim as sqlite3

logger = logging.getLogger(__name__)

# Resolved relative to project root
from pathlib import Path

try:
    import config

    db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
except ImportError:
    db_name = "jobhunt_saas_v2.db"
DB_PATH = str(Path(__file__).resolve().parent.parent / db_name)
OUTPUT_DIR = "newsletters"
SPONSOR_TEXT = (
    "🔥 **SPONSORED BY CLOUDFLARE**: Fast, secure edge networks. Start for free today!"
)
SPONSOR_LINK = "https://cloudflare.com/affiliate"


def get_top_jobs_today(limit: int = 10) -> list[dict[str, Any]]:
    """Retrieve the top daily jobs from the database, falling back to mock data if empty."""
    jobs: list[dict[str, Any]] = []
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(
                "SELECT title, company, location, url FROM jobs ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            jobs = [dict(row) for row in cur.fetchall()]
            conn.close()
        except Exception as e:
            logger.error(f"DB Error: {e}", exc_info=True)

    if not jobs:
        # Mock data
        jobs = [
            {
                "title": "Senior AI Engineer",
                "company": "OpenAI",
                "location": "Remote",
                "url": "#",
            },
            {
                "title": "Lead Python Dev",
                "company": "Stripe",
                "location": "Remote",
                "url": "#",
            },
            {
                "title": "Cloud Architect",
                "company": "AWS",
                "location": "Remote",
                "url": "#",
            },
        ]
    return jobs


def generate_newsletter_html() -> str:
    """Generate daily premium newsletter curated with top remote jobs, saving it to a local HTML file."""
    jobs = get_top_jobs_today(10)
    date_str = datetime.datetime.now().strftime("%B %d, %Y")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f9fafb; color: #111827; line-height: 1.6; padding: 20px; }}
            .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            h1 {{ color: #111827; font-size: 24px; font-weight: 800; text-align: center; margin-bottom: 5px; }}
            .date {{ text-align: center; color: #6b7280; font-size: 14px; margin-bottom: 30px; }}
            .sponsor {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 30px; font-size: 14px; }}
            .sponsor a {{ color: #d97706; font-weight: bold; text-decoration: none; }}
            .job {{ border-bottom: 1px solid #e5e7eb; padding: 20px 0; }}
            .job:last-child {{ border-bottom: none; }}
            .job-title {{ font-size: 18px; font-weight: bold; color: #1f2937; margin: 0 0 5px 0; }}
            .job-company {{ color: #4b5563; font-size: 14px; margin: 0 0 10px 0; }}
            .apply-btn {{ display: inline-block; background-color: #2563eb; color: #ffffff; padding: 8px 16px; border-radius: 4px; text-decoration: none; font-size: 14px; font-weight: 600; }}
            .footer {{ margin-top: 40px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #e5e7eb; padding-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 JobHunt Pro Daily</h1>
            <div class="date">{date_str} • Top Remote Tech Jobs</div>

            <div class="sponsor">
                {SPONSOR_TEXT} <a href="{SPONSOR_LINK}">Learn More &rarr;</a>
            </div>

            <p>Good morning! Here are the top hand-picked remote opportunities for today. These are fresh and actively hiring.</p>
    """

    for job in jobs:
        html += f"""
            <div class="job">
                <h3 class="job-title">{job.get("title")}</h3>
                <p class="job-company">{job.get("company")} • {job.get("location")}</p>
                <a href="{job.get("url")}" class="apply-btn">Apply Now</a>
            </div>
        """

    html += """
            <div class="footer">
                You are receiving this because you subscribed via JobHunt Pro.<br>
                To sponsor this newsletter (100k+ tech talent reach), reply to this email.
            </div>
        </div>
    </body>
    </html>
    """

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    filename = os.path.join(
        OUTPUT_DIR, f"newsletter_{datetime.datetime.now().strftime('%Y%m%d')}.html"
    )
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info(f"Newsletter generated successfully: {filename}")
    return filename


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    generate_newsletter_html()
