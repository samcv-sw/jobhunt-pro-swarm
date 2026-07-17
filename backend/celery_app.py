import gc
import os

from celery import Celery

# Aggressive garbage collection tuning for the process
gc.set_threshold(50, 5, 5)

# Use RabbitMQ as the message broker for enterprise durability (Event-Driven Deliverability)
# Defaulting to localhost for development
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # Keep Redis for result backend
RABBITMQ_URL = os.getenv("RABBITMQ_URL")
if not RABBITMQ_URL:
    RABBITMQ_URL = REDIS_URL

celery_app = Celery(
    "jobhunt_tasks", broker=RABBITMQ_URL, backend=REDIS_URL, include=["backend.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,  # Recycle child worker after 10 tasks to reclaim memory
    worker_max_memory_per_child=150000,  # Recycle child worker if RSS exceeds 150MB (in KB)
    broker_connection_retry_on_startup=True,
    # Non-blocking / fail-fast configurations
    broker_connection_timeout=0.2,  # Fast timeout for establishing broker connection
    broker_transport_options={
        "max_connections": 10,  # Max connections in pool
        "pool_timeout": 0.05,  # Fast timeout for checking out connection from pool (50ms)
        "connect_timeout": 0.2,  # Transport-level connection timeout (200ms)
    },
    # Route specific tasks to different queues if needed
    task_routes={
        "backend.tasks.scrape_jobs": {"queue": "scraping"},
        "backend.tasks.generate_cover_letter": {"queue": "ai_inference"},
        "backend.tasks.send_application_email": {"queue": "email_sender"},
    },
    # Reliability: DLQ-equivalent behaviour and time limits
    result_expires=3600,  # Expire task results after 1 hour to prevent Redis bloat
    task_reject_on_worker_lost=True,  # Re-queue tasks if the worker process is killed unexpectedly
    task_acks_on_failure_or_timeout=True,  # Acknowledge (remove from queue) tasks that hard-fail or timeout
    task_soft_time_limit=300,  # Raise SoftTimeLimitExceeded after 5 min for graceful shutdown
    task_time_limit=360,  # Hard-kill the task process after 6 min to prevent zombies
)
