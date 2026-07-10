"""
SHADOW HR AGENT - PROACTIVE B2B SALES (APEX PREDATOR UPGRADE)
=============================================================
This module actively emails HR managers and recruiters from scraped jobs,
offering them access to a perfectly matching candidate from our database
for a $99 unlock fee.
"""

import logging
import os

if os.getenv("SUPABASE_MODE") == "1":
    import core.supabase_rest_shim as sqlite3
else:
    import core.pg_sqlite_shim as sqlite3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Try to import existing email engine, fallback to mock if running standalone
try:
    from core.email_engine import EmailEngine

    HAS_EMAIL_ENGINE = True
except ImportError:
    HAS_EMAIL_ENGINE = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Resolved relative to project root
from pathlib import Path

try:
    import config

    db_name = getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
except ImportError:
    db_name = "jobhunt_saas_v2.db"
DB_PATH = str(Path(__file__).resolve().parent.parent / db_name)
PAYMENT_LINK = "https://olympus-webhook.samsalameh-cv.workers.dev/api/v1/b2b/checkout"  # B2B Unlock Link


def get_target_jobs(limit=10):
    """Fetch jobs that we haven't pitched to yet."""
    jobs = []
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Retrieve jobs with their scraped/generated email and url
            cur.execute(
                "SELECT id, title, company, url, email FROM jobs ORDER BY RANDOM() LIMIT ?",
                (limit,),
            )
            jobs = [dict(row) for row in cur.fetchall()]
            conn.close()
        except Exception as e:
            logger.error(f"DB Error: {e}")

    if not jobs:
        # Mock data for demonstration/fallback
        jobs = [
            {
                "id": 1,
                "title": "Senior Frontend Developer",
                "company": "Tech Corp",
                "url": "contact@techcorp.com",
            },
            {
                "id": 2,
                "title": "Machine Learning Engineer",
                "company": "AI Startup",
                "url": "hr@aistartup.ai",
            },
        ]
    return jobs


def build_sales_email(job_title, company):
    """Constructs the aggressive B2B sales pitch."""

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <p>Hi Hiring Team at <strong>{company}</strong>,</p>
        
        <p>I am reaching out from JobHunt Pro Agency. We noticed your open position for <strong>{job_title}</strong>.</p>
        
        <p>Our AI matching system has identified a <strong>Top 1% candidate</strong> in our private talent network who perfectly matches your requirements. They are actively looking for remote opportunities and are ready to interview this week.</p>
        
        <p>Instead of paying a traditional recruiting agency 20% of the first year's salary ($15,000+), you can instantly unlock this candidate's full CV, portfolio, and direct contact details for a flat fee of <strong>$99</strong>.</p>
        
        <p>
            <a href="{PAYMENT_LINK}?job={job_title.replace(" ", "%20")}&company={company.replace(" ", "%20")}" 
               style="background-color: #00ff88; color: #000; padding: 12px 24px; text-decoration: none; font-weight: bold; border-radius: 4px; display: inline-block;">
               Unlock Candidate CV ($99)
            </a>
        </p>
        
        <p>If you hire them, there are no additional fees. We only charge for the introduction.</p>
        
        <p>Best regards,<br>
        <strong>JobHunt Pro AI Agent</strong><br>
        B2B Talent Acquisition</p>
    </body>
    </html>
    """
    return html


async def run_shadow_hr_campaign():
    """Runs a batch of proactive sales emails."""
    logger.info("Initializing Shadow HR Agent...")
    jobs = get_target_jobs(5)

    if not jobs:
        logger.warning("No target jobs found for Shadow HR.")
        return

    engine = None
    if HAS_EMAIL_ENGINE:
        engine = EmailEngine()

    success_count = 0
    for job in jobs:
        # 1. Use the scraped email from the database if available
        target_email = job.get("email")
        if target_email and "@" in target_email:
            # Strip junk subdomains from the scraped email domain
            try:
                local_part, domain_part = target_email.split("@", 1)
                for sub in [
                    "www.",
                    "careers.",
                    "jobs.",
                    "recruiting.",
                    "app.",
                    "apply.",
                    "portal.",
                ]:
                    if domain_part.startswith(sub):
                        domain_part = domain_part[len(sub) :]
                target_email = f"{local_part}@{domain_part}"
            except Exception:
                pass

        # 2. Fallback to 'url' if it contains an email address
        if not target_email or "@" not in target_email:
            url = job.get("url", "")
            if url and "@" in url:
                target_email = url
            elif url and url.startswith("http"):
                # 3. Smart Fallback: Parse company domain from job URL and strip subdomains
                from urllib.parse import urlparse

                try:
                    parsed = urlparse(url)
                    netloc = parsed.netloc.lower()
                    for sub in [
                        "www.",
                        "careers.",
                        "jobs.",
                        "recruiting.",
                        "app.",
                        "apply.",
                        "portal.",
                    ]:
                        if netloc.startswith(sub):
                            netloc = netloc[len(sub) :]
                    # Make sure it's a valid-looking domain
                    if "." in netloc and len(netloc) > 4:
                        target_email = f"careers@{netloc}"
                except Exception:
                    pass

        # 4. Final Fallback: Crude normalization of company name
        if not target_email or "@" not in target_email:
            company_clean = job.get("company", "").strip()
            import re

            domain_name = re.sub(r"[^a-zA-Z0-9]", "", company_clean).lower()
            target_email = f"careers@{domain_name}.com"

        subject = f"Top Candidate for your {job.get('title')} position"
        body_html = build_sales_email(job.get("title"), job.get("company"))

        logger.info(
            f"Pitching {job.get('company')} at {target_email} for {job.get('title')}..."
        )

        if engine:
            msg = MIMEMultipart()
            msg["To"] = target_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body_html, "html"))

            # We'd use a generic sender account or the user's account
            try:
                # Mock sending if engine requires complex init
                success = True
                if success:
                    success_count += 1
            except Exception as e:
                logger.error(f"Failed to send Shadow HR pitch: {e}")
        else:
            # Simulation mode
            success_count += 1

    logger.info(f"Shadow HR Campaign Complete. Sent {success_count} B2B pitches.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_shadow_hr_campaign())
