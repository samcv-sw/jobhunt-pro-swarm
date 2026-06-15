"""Run follow-up sequence for all tracked applications."""
import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("followup_run_output.txt", "w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

log_file = open("followup_run_output.txt", "a", encoding="utf-8")

def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

async def main():
    log("=" * 60)
    log(f"JOBHUNT PRO v{config.VERSION} - FOLLOW-UP SEQUENCE")
    log("=" * 60)

    # Import follow-up sequence (uses JSON tracker with 105 tracked apps)
    from core.followup_sequence import followup_sequence
    from core.email_engine import EmailEngine
    from core.smart_scheduler import SmartScheduler

    log("\n[1] Checking for due follow-ups...")
    due = followup_sequence.get_due_followups()
    log(f"    Found {len(due)} applications needing follow-up")

    if not due:
        log("    No follow-ups due yet. First follow-up is at day 3.")
        stats = followup_sequence.get_stats()
        log(f"    Stats: {stats}")
        log_file.close()
        return

    # Initialize email engine
    log("\n[2] Initializing email engine...")
    scheduler = SmartScheduler()
    email_engine = EmailEngine(scheduler)

    sent = 0
    failed = 0

    log(f"\n[3] Sending {len(due)} follow-ups...")
    for i, app in enumerate(due):
        try:
            company = app["company"]
            email = app["email"]
            role = app["role"]
            stage = app["stage"]
            followup_day = app["followup_day"]
            days_since = app["days_since"]

            log(f"    [{i+1}/{len(due)}] {company} - {role} (day {days_since}, stage: {stage})")

            # Get follow-up body (AI-generated if available, else template)
            body = followup_sequence.get_followup_body(
                company, role, followup_day, days_since
            )

            # Build email
            import uuid
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            import config

            tracking_id = str(uuid.uuid4())[:12]
            msg = MIMEMultipart()
            msg["From"] = f"Sam Salameh <{config.CANDIDATE_EMAIL}>"
            msg["To"] = email
            msg["Subject"] = app["subject"].format(company=company, role=role)
            msg["Reply-To"] = f"Sam Salameh <{config.CANDIDATE_EMAIL}>"
            msg["Message-ID"] = f"<{tracking_id}.followup@jobhuntpro.com>"
            msg.attach(MIMEText(body, "html", "utf-8"))

            # Send via scheduler
            provider = await scheduler.wait_for_send_slot()
            if not provider:
                log(f"    SKIPPED: No provider available")
                failed += 1
                continue

            success, result = await email_engine.send_with_retry(provider, msg)
            if success:
                followup_sequence.mark_followup_sent(app["key"])
                sent += 1
                log(f"    OK SENT via {provider}")
            else:
                failed += 1
                log(f"    FAILED: {result}")

            # Delay between sends
            delay = scheduler.calculate_delay()
            await asyncio.sleep(delay)

        except Exception as e:
            failed += 1
            log(f"    ERROR: {e}")

    log("\n" + "=" * 60)
    log(f"FOLLOW-UP RUN COMPLETE")
    log(f"  Sent:   {sent}")
    log(f"  Failed: {failed}")
    stats = followup_sequence.get_stats()
    log(f"  Stats:  {stats}")
    log("=" * 60)
    log_file.close()

if __name__ == "__main__":
    asyncio.run(main())
