import os

from celery import Celery

# Use RabbitMQ as the message broker for enterprise durability (Event-Driven Deliverability)
# Defaulting to localhost for development
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://jobhunt:jobhunt_password@localhost:5672//")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0") # Keep Redis for result backend

celery_app = Celery(
    "jobhunt_tasks",
    broker=RABBITMQ_URL,
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
    # Non-blocking / fail-fast configurations
    broker_connection_timeout=0.2,            # Fast timeout for establishing broker connection
    broker_transport_options={
        "max_connections": 10,                 # Max connections in pool
        "pool_timeout": 0.05,                  # Fast timeout for checking out connection from pool (50ms)
        "connect_timeout": 0.2,                # Transport-level connection timeout (200ms)
    },
    # Route specific tasks to different queues if needed
    task_routes={
        "backend.tasks.scrape_jobs": {"queue": "scraping"},
        "backend.tasks.generate_cover_letter": {"queue": "ai_inference"},
        "backend.tasks.send_application_email": {"queue": "email_sender"},
    }
)
