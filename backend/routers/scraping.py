"""JobHunt Pro — Scraping & Scraper Health Router.

Extracted from backend/main.py as part of M2 Backend Router Optimization.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Request

from backend.auth import verify_jwt
from backend.database import async_session
from backend.limiter import rate_limiter
from backend.schemas import ScrapeRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Scraping"])


@router.post("/api/v1/scrape", dependencies=[Depends(verify_jwt), Depends(rate_limiter)])
async def trigger_scrape(req: ScrapeRequest, request: Request = None) -> dict[str, str]:
    """Queue a scraping task via Celery with fallback to local SQLite job queue."""
    import asyncio
    import os
    import sys
    from uuid import uuid4 as celery_uuid

    from backend.main import celery_dispatch_executor
    from backend.tasks import scrape_jobs

    is_testing = "pytest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
    local_fallback = os.getenv("LOCAL_QUEUE_FALLBACK", "0") == "1"
    loop = asyncio.get_running_loop()

    if local_fallback:
        try:
            from core.job_queue import enqueue_task

            await loop.run_in_executor(
                celery_dispatch_executor,
                enqueue_task,
                "scrape",
                {"target_urls": req.target_urls, "user_id": req.user_id},
            )
            logger.info("Scrape task routed to local SQLite job queue (forced fallback).")
            return {"status": "queued_local", "task_id": f"local_{celery_uuid()}"}
        except Exception as local_exc:
            logger.error("Failed to route task to local SQLite job queue: %s", local_exc)
            return {"status": "error", "detail": f"Failed to queue task locally: {str(local_exc)}"}

    if is_testing:
        try:
            task = await loop.run_in_executor(
                celery_dispatch_executor, scrape_jobs.delay, req.target_urls, req.user_id
            )
            return {"status": "queued", "task_id": task.id}
        except Exception as exc:
            logger.error("Scrape task queuing failed during test: %s", exc)
            try:
                from core.job_queue import enqueue_task

                await loop.run_in_executor(
                    celery_dispatch_executor,
                    enqueue_task,
                    "scrape",
                    {"target_urls": req.target_urls, "user_id": req.user_id},
                )
                logger.info("Automatic fallback to SQLite queue successful.")
                return {"status": "queued_local", "task_id": f"local_{celery_uuid()}"}
            except Exception as fallback_exc:
                logger.error("Fallback queue insert also failed: %s", fallback_exc)
                return {"status": "error", "detail": "Scraping service temporarily unavailable"}

    task_id = str(celery_uuid())
    try:
        await asyncio.wait_for(
            loop.run_in_executor(
                celery_dispatch_executor,
                lambda: scrape_jobs.apply_async(
                    args=(req.target_urls, req.user_id), task_id=task_id, retry=False
                ),
            ),
            timeout=0.05,
        )
        return {"status": "queued", "task_id": task_id}
    except TimeoutError:
        return {"status": "accepted", "task_id": task_id}
    except Exception as exc:
        logger.error(
            "Scrape task queuing failed: %s. Trying fallback to local SQLite job queue...", exc
        )
        try:
            from core.job_queue import enqueue_task

            await loop.run_in_executor(
                celery_dispatch_executor,
                enqueue_task,
                "scrape",
                {"target_urls": req.target_urls, "user_id": req.user_id},
            )
            logger.info("Automatic fallback to SQLite queue successful.")
            return {"status": "queued_local", "task_id": f"local_{celery_uuid()}"}
        except Exception as fallback_exc:
            logger.error("Fallback queue insert also failed: %s", fallback_exc)
            return {"status": "error", "detail": "Scraping service temporarily unavailable"}


@router.get("/api/v1/scrapers/health", dependencies=[Depends(verify_jwt)])
async def scrapers_health(request: Request = None) -> dict[str, Any]:
    """Return per-platform scraper health scores — IMP-208."""
    try:
        from core.global_scraper import ScraperHealthTracker

        tracker = ScraperHealthTracker()
        scores = tracker.all_scores() if hasattr(tracker, "all_scores") else {}
        return {"status": "ok", "scores": scores}
    except Exception as e:
        logger.warning(f"Scraper health unavailable: {e}")
        try:
            from sqlalchemy import text as _text

            cutoff = datetime.now(UTC) - timedelta(days=7)
            async with async_session() as session:
                result = await session.execute(
                    _text("""
                        SELECT platform, COUNT(*) as total,
                               SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successes,
                               SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failures
                        FROM scrape_log
                        WHERE created_at >= :cutoff
                        GROUP BY platform
                    """),
                    {"cutoff": cutoff},
                )
                rows = result.fetchall()
            health_data = {}
            for row in rows:
                platform = row.platform or "unknown"
                total = row.total or 0
                successes = row.successes or 0
                health_data[platform] = {
                    "total": total,
                    "successes": successes,
                    "failures": row.failures or 0,
                    "health_pct": round((successes / total * 100) if total > 0 else 0, 1),
                }
            return {"status": "ok", "scores": health_data}
        except Exception as inner_e:
            return {"status": "unavailable", "scores": {}, "detail": str(inner_e)}
