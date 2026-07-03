import asyncio
import logging
import sys
import os

# Add the parent directory to sys.path so we can import internal modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .celery_app import celery_app
from scrapers.stealth_ingest import stealth_scrape_jobs
from .ai_engine import generate_smart_cover_letter
from .email_engine import RotatingEmailSender

logger = logging.getLogger(__name__)

# Initialize the global email sender inside the worker process
email_sender = RotatingEmailSender()

@celery_app.task(bind=True, max_retries=3)
def scrape_jobs(self, target_urls: list, user_id: str):
    """
    Background task to scrape jobs stealthily.
    Returns structured dicts {title, url, company, description_snippet}.
    """
    logger.info(f"Starting stealth scrape for user {user_id} on {len(target_urls)} URLs.")
    try:
        structured_jobs: list = asyncio.run(stealth_scrape_jobs(target_urls))
        logger.info(
            f"Scrape complete for {user_id}: {len(structured_jobs)} structured jobs found "
            f"out of {len(target_urls)} URLs."
        )
        return {"status": "success", "jobs_found": len(structured_jobs), "jobs": structured_jobs}
    except Exception as exc:
        logger.error(f"Scraping failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True, max_retries=3)
def generate_cover_letter(self, job_description: str, user_cv: str):
    """
    Background task to generate cover letter via Groq Llama 3 (LPU).
    """
    logger.info("Generating cover letter using Groq LPU...")
    try:
        # Run the async AI generation within the synchronous Celery worker
        result = asyncio.run(generate_smart_cover_letter(job_description, user_cv))
        return {"status": "success", "subject": result.get("subject"), "body": result.get("body")}
    except Exception as exc:
        logger.error(f"AI Generation failed: {exc}")
        raise self.retry(exc=exc, countdown=10)

@celery_app.task(
    bind=True, 
    max_retries=5, 
    autoretry_for=(Exception,), 
    retry_backoff=True, 
    retry_jitter=True
)
def send_application_email(self, cover_letter_subject: str, cover_letter_body: str, recipient: str):
    """
    Background task to send email leveraging native Celery retries with exponential backoff and rotation.
    """
    logger.info(f"Sending application email to {recipient}...")
    asyncio.run(email_sender.send_email(
        to_email=recipient, 
        subject=cover_letter_subject, 
        body=cover_letter_body
    ))
    return {"status": "success"}
