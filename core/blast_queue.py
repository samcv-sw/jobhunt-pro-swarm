"""
BLAST QUEUE: API queues → cron picks up → Graph API sends
Works on PA $0 tier. No blocking. No timeouts.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

QUEUE_DIR = None


def init(data_dir: str = None):
    global QUEUE_DIR
    if data_dir:
        QUEUE_DIR = Path(data_dir) / "blast_queue"
    else:
        QUEUE_DIR = Path(__file__).parent.parent / "data" / "blast_queue"
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)


def enqueue(
    recipients_file: str,
    max_sends: int,
    campaign: str = "blast",
    subject: str = None,
    body: str = None,
) -> dict:
    """Queue a blast. Returns immediately."""
    job_id = f"blast_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{campaign}"

    job = {
        "id": job_id,
        "recipients_file": recipients_file,
        "max_sends": max_sends,
        "campaign": campaign,
        "subject": subject,
        "body": body,
        "created": datetime.utcnow().isoformat(),
        "status": "queued",
        "sent": 0,
        "failed": 0,
    }

    job_file = QUEUE_DIR / f"{job_id}.json"
    with open(job_file, "w", encoding="utf-8") as f:
        json.dump(job, f, indent=2)
    logger.info(f"Job queued: {job_id} ({max_sends} emails)")
    return job


def get_status() -> dict:
    """Get status of all queued/running blasts."""
    if not QUEUE_DIR or not QUEUE_DIR.exists():
        return {"queue_size": 0, "jobs": []}
    jobs = []
    sent_total = 0
    failed_total = 0
    for f in sorted(QUEUE_DIR.glob("blast_*.json")):
        try:
            with open(f, encoding="utf-8") as file_obj:
                job = json.load(file_obj)
            jobs.append(
                {
                    "id": job["id"],
                    "campaign": job["campaign"],
                    "status": job.get("status", "unknown"),
                    "max_sends": job.get("max_sends", 0),
                    "sent": job.get("sent", 0),
                    "failed": job.get("failed", 0),
                    "created": job.get("created", ""),
                }
            )
            sent_total += job.get("sent", 0)
            failed_total += job.get("failed", 0)
        except Exception:
            pass
    return {
        "queue_size": len(jobs),
        "sent_total": sent_total,
        "failed_total": failed_total,
        "jobs": jobs[-10:],  # last 10
    }


def process_queue(limit: int = 50) -> dict:
    """Process queued blast jobs. Called by cron."""
    if not QUEUE_DIR or not QUEUE_DIR.exists():
        return {"status": "ok", "processed": 0}

    total_sent = 0
    total_failed = 0
    processed = 0

    for job_file in sorted(QUEUE_DIR.glob("blast_*.json")):
        try:
            with open(job_file, encoding="utf-8") as f:
                job = json.load(f)
        except Exception:
            continue

        if job.get("status") not in ("queued", "running"):
            continue

        # Mark as running
        job["status"] = "running"
        with open(job_file, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=2)

        try:
            # Load recipients (chunked for memory)
            recip_file = Path(__file__).parent.parent / "data" / job["recipients_file"]
            if not recip_file.exists():
                job["status"] = "failed"
                job["error"] = f"File not found: {job['recipients_file']}"
                with open(job_file, "w", encoding="utf-8") as f:
                    json.dump(job, f, indent=2)
                continue

            with open(recip_file, encoding="utf-8") as f:
                recipients = json.load(f)
            max_sends = min(job.get("max_sends", 100), limit)

            from core.graph_sender import init as gs_init
            from core.graph_sender import send_bulk

            gs_init()

            result = send_bulk(
                recipients,
                subject=job.get("subject"),
                body_html=job.get("body"),
                campaign_name=job.get("campaign", "blast"),
                max_sends=max_sends,
            )

            job["sent"] = result.get("sent", 0)
            job["failed"] = result.get("failed", 0)
            job["tokens_expired"] = result.get("tokens_expired", 0)
            job["status"] = "completed"
            job["completed"] = datetime.utcnow().isoformat()

            total_sent += result.get("sent", 0)
            total_failed += result.get("failed", 0)
            processed += 1

        except Exception as e:
            job["status"] = "failed"
            job["error"] = str(e)[:500]
            logger.error(f"Blast job failed: {e}")

        with open(job_file, "w", encoding="utf-8") as f:
            json.dump(job, f, indent=2)

        if total_sent >= limit:
            break  # respect batch limit

    return {
        "status": "ok",
        "processed": processed,
        "sent": total_sent,
        "failed": total_failed,
    }
