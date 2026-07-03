import os
import sys
import logging

import procrastinate

# Add root to pythonpath so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

# Parse database URL
DATABASE_URL = (
    os.getenv("NEON_URL")
    or os.getenv("DATABASE_URL")
    or os.getenv("DATABASE_URL_SYNC")
    or "sqlite:///jobhunt.db"
)
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

# Bifurcate connection: background workers must bypass the transaction pooler to use LISTEN/NOTIFY
# Often indicated by removing '-pooler' from the host in Neon/Supabase environments.
if "-pooler" in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("-pooler", "")

# Initialize Procrastinate App
if "sqlite" in DATABASE_URL:
    app = procrastinate.App(connector=procrastinate.testing.InMemoryConnector())
else:
    # Aggressive garbage collection: delete_jobs="always" ensures queue remains at absolute zero-state
    app = procrastinate.App(
        connector=procrastinate.PsycopgConnector(conninfo=DATABASE_URL),
        worker_defaults={"delete_jobs": "always"}
    )


@app.task(queue="emails")
def send_marketing_email_task(email_data: dict):
    from core.email_marketing import send_marketing_email_sync

    logger.info(f"Sending email task: {email_data.get('to_email')}")
    send_marketing_email_sync(email_data)


@app.task(queue="scraping")
def run_scraper_job_task(job_data: dict):
    from core.pa_job_scraper import run_scraper_sync

    logger.info("Running scraper task")
    run_scraper_sync(job_data)


if __name__ == "__main__":
    if "sqlite" not in DATABASE_URL:
        # Create schema if it doesn't exist
        logger.info("Applying Procrastinate DB schema...")
        with app.connector.open_connection() as connection:
            app.schema_manager.apply_schema()

    # Run the worker
    logger.info("Starting Procrastinate worker on queues: ['emails', 'scraping']")
    app.run_worker(
        queues=["emails", "scraping"],
        listen_notify=False,
        fetch_job_polling_interval=0.5
    )
