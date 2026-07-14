import asyncio
import logging
import os
import sys

# Add the parent directory to sys.path so we can import internal modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from functools import wraps

from core.edge_cache import edge_cache
from core.llm_provider_pool import LLMRateLimitError
from scrapers.stealth_ingest import stealth_scrape_jobs

from .ai_engine import generate_smart_cover_letter
from .celery_app import celery_app
from .email_engine import RotatingEmailSender

logger = logging.getLogger(__name__)

# Initialize the global email sender inside the worker process
email_sender = RotatingEmailSender()

import threading

_thread_local = threading.local()

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    except RuntimeError:
        pass

    loop = getattr(_thread_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _thread_local.loop = loop
    return loop.run_until_complete(coro)

@celery_app.task(bind=True, max_retries=3)
def scrape_jobs(self, target_urls: list, user_id: str):
    """
    Background task to scrape jobs stealthily.
    Returns structured dicts {title, url, company, description_snippet}.
    """
    logger.info(f"Starting stealth scrape for user {user_id} on {len(target_urls)} URLs.")
    try:
        structured_jobs: list = run_async(stealth_scrape_jobs(target_urls))
        logger.info(
            f"Scrape complete for {user_id}: {len(structured_jobs)} structured jobs found "
            f"out of {len(target_urls)} URLs."
        )
        return {"status": "success", "jobs_found": len(structured_jobs), "jobs": structured_jobs}
    except Exception as exc:
        logger.error(f"Scraping failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

def groq_rate_limit_retry(max_retries=3, default_countdown=10):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Proactive check before starting the task
            proactive_retry = False
            countdown = default_countdown
            if edge_cache.enabled:
                try:
                    reset_at_str = run_async(edge_cache.get("groq_rate_limit_reset"))
                    if reset_at_str:
                        reset_at = float(reset_at_str)
                        now = time.time()
                        if reset_at > now:
                            countdown = int(reset_at - now) + 1
                            proactive_retry = True
                except Exception as cache_err:
                    logger.error(f"Error checking rate limit cache: {cache_err}")

            if proactive_retry:
                logger.warning(
                    f"Groq rate limit is active (resets in {countdown}s). "
                    f"Proactively retrying Celery task..."
                )
                raise self.retry(countdown=countdown)

            try:
                return func(self, *args, **kwargs)
            except LLMRateLimitError as exc:
                # Capture rate limit exceptions from the pool
                countdown = getattr(exc, "reset_time", default_countdown)
                logger.warning(
                    f"LLM Provider {exc.provider} rate limited. Retrying Celery task in {countdown}s..."
                )
                raise self.retry(exc=exc, countdown=int(countdown) + 1)
            except Exception as exc:
                from celery.exceptions import Retry
                if isinstance(exc, Retry):
                    raise
                # Standard fallback retry
                logger.error(f"Task failed: {exc}. Retrying...")
                raise self.retry(exc=exc, countdown=default_countdown)
        return wrapper
    return decorator


@celery_app.task(bind=True, max_retries=3)
@groq_rate_limit_retry(max_retries=3, default_countdown=10)
def generate_cover_letter(self, job_description: str, user_cv: str):
    """
    Background task to generate cover letter via Groq Llama 3 (LPU).
    """
    logger.info("Generating cover letter using Groq LPU...")
    # Run the async AI generation within the synchronous Celery worker
    result = run_async(generate_smart_cover_letter(job_description, user_cv))
    return {"status": "success", "subject": result.get("subject"), "body": result.get("body")}

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
    run_async(email_sender.send_email(
        to_email=recipient,
        subject=cover_letter_subject,
        body=cover_letter_body
    ))
    return {"status": "success"}


@celery_app.task
def send_bulk_emails_task(email_list: list[dict]):
    """
    IMP-039: Celery group for parallel batch email dispatch.
    Takes a list of {"subject": str, "body": str, "recipient": str} dicts,
    and runs them in parallel using Celery group.
    """
    from celery import group
    logger.info(f"Dispatching bulk parallel Celery tasks for {len(email_list)} emails.")
    job = group(
        send_application_email.s(item["subject"], item["body"], item["recipient"])
        for item in email_list
    )
    result = job.apply_async()
    return {"status": "dispatched", "group_id": result.id}

