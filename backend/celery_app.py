import os
from celery import Celery

# Use Redis as the message broker and result backend
# Defaulting to localhost for development
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "jobhunt_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
    # Route specific tasks to different queues if needed
    task_routes={
        "backend.tasks.scrape_jobs": {"queue": "scraping"},
        "backend.tasks.generate_cover_letter": {"queue": "ai_inference"},
        "backend.tasks.send_application_email": {"queue": "email_sender"},
    }
)
