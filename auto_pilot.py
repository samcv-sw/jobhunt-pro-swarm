"""
JOBHUNT PRO v16.7 - AUTO-PILOT MODE (MEGA SWARM EDITION)
==========================================================
Runs 24/7 with 20,000 hierarchical swarm agents:
  - 18,000 Workers + 1,500 Squad Leaders + 500 Team Managers
  - Original apply/retry/followup cycle (kept for backward compat)
  - MEGA SWARM cycle: 7-phase hiring blitz across 20,000 agents
  - Schedule: Every 30 minutes during working hours (8AM-8PM Beirut time)
  - Logs everything to auto_pilot_log.txt
"""
import sys
import os
import asyncio
import logging
import config
from datetime import datetime, time, timedelta
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("auto_pilot_log.txt", "a", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Beirut timezone offset (UTC+3)
BEIRUT_OFFSET = 3 * 3600  # 3 hours in seconds

def beirut_now():
    """Get current time in Beirut timezone."""
    utc_now = datetime.utcnow()
    return datetime.fromtimestamp(utc_now.timestamp() + BEIRUT_OFFSET)

def is_working_hours():
    """Check if current time in Beirut is within working hours (8AM-8PM)."""
    now = beirut_now()
    return 8 <= now.hour < 20

class AutoPilot:
    """Autonomous job application engine - runs 24/7 with 20,000 mega swarm."""

    def __init__(self):
        self.cycle_count = 0
        self.total_applied = 0
        self.total_followups = 0
        self.total_retried = 0
        self.start_time = datetime.now()
        self.mega_master = None
        self.mega_enabled = True  # Set to False to disable mega swarm

    async def run_cycle(self):
        """Run one complete cycle: Apply -> Retry -> Follow-ups."""
        self.cycle_count += 1
        now = beirut_now()

        logger.info("=" * 60)
        logger.info(f"  AUTO-PILOT CYCLE #{self.cycle_count} - {now.strftime('%Y-%m-%d %H:%M:%S')} Beirut")
        logger.info("=" * 60)

        try:
            from orchestrator import Orchestrator

            orch = Orchestrator()
            await orch.db.create_tables()

            # Phase 1: Apply to new jobs + retry failed
            logger.info("\n[PHASE 1] Applying to jobs...")
            applied = await orch.run_apply(limit=200, include_failed=True)
            self.total_applied += applied
            logger.info(f"  -> Applied: {applied} (total: {self.total_applied})")

            # Phase 2: Retry any remaining failed jobs
            logger.info("\n[PHASE 2] Retrying failed jobs...")
            retried = await orch.retry_failed(limit=50)
            self.total_retried += retried
            logger.info(f"  -> Retried: {retried} (total: {self.total_retried})")

            # Phase 3: Send follow-ups
            logger.info("\n[PHASE 3] Sending follow-ups...")
            from core.followup_sequence import followup_sequence
            due = followup_sequence.get_due_followups()
            logger.info(f"  -> Due follow-ups: {len(due)}")

            sent = 0  # Initialize before conditional block
            if due:
                from core.email_engine import EmailEngine
                from core.smart_scheduler import SmartScheduler
                scheduler = SmartScheduler()
                email_engine = EmailEngine(scheduler)
                import config
                import uuid
                from email.mime.multipart import MIMEMultipart
                from email.mime.text import MIMEText

                sent = 0
                for app in due[:20]:  # Max 20 follow-ups per cycle
                    try:
                        body = followup_sequence.get_followup_body(
                            app["company"], app["role"], app["followup_day"], app["days_since"]
                        )
                        msg = MIMEMultipart()
                        msg["From"] = f"Sam Salameh <{config.CANDIDATE_EMAIL}>"
                        msg["To"] = app["email"]
                        msg["Subject"] = app["subject"].format(company=app["company"], role=app["role"])
                        msg["Reply-To"] = f"Sam Salameh <{config.CANDIDATE_EMAIL}>"
                        msg["Message-ID"] = f"<{str(uuid.uuid4())[:12]}.followup@jobhuntpro.com>"
                        msg.attach(MIMEText(body, "html", "utf-8"))

                        provider = await scheduler.wait_for_send_slot()
                        if not provider:
                            break

                        success, _ = await email_engine.send_with_retry(provider, msg)
                        if success:
                            followup_sequence.mark_followup_sent(app["key"])
                            sent += 1

                        await asyncio.sleep(scheduler.calculate_delay())
                    except Exception as e:
                        logger.error(f"  Follow-up error: {e}")

                self.total_followups += sent
                logger.info(f"  -> Follow-ups sent: {sent} (total: {self.total_followups})")

            # Phase 4: MEGA SWARM (20,000 agents) — run in parallel
            if self.mega_enabled:
                logger.info("\n[PHASE 4] Mega Swarm — deploying 20,000 agents...")
                try:
                    if self.mega_master is None:
                        from core.mega_swarm import MegaSwarmMaster
                        self.mega_master = MegaSwarmMaster()
                        await self.mega_master.initialize(orchestrator=orch)
                        logger.info("Mega Swarm initialized (20,000 agents)")

                    mega_results = await self.mega_master.full_job_cycle()
                    mega_total = sum(mega_results.values()) if mega_results else 0
                    logger.info(f"  -> Mega Swarm dispatched {mega_total} tasks across 20,000 agents")
                    for phase, count in (mega_results or {}).items():
                        logger.info(f"       {phase}: {count}")
                except Exception as e:
                    logger.error(f"  Mega Swarm phase failed: {e}")
                    traceback.print_exc()
            else:
                logger.info("\n[PHASE 4] Mega Swarm disabled — skipping")

            # Phase 5: Print stats
            stats = await orch.db.get_stats()
            warmup_stats = {}
            active_providers = list(orch.scheduler._active_providers) if orch.scheduler._active_providers else ['gmail1']
            for p in active_providers:
                warmup_stats[p] = orch.warmup.get_status(p)

            logger.info("\n" + "=" * 60)
            logger.info("  CYCLE COMPLETE - SUMMARY")
            logger.info(f"  DB Stats:      {stats}")
            logger.info(f"  This cycle:    {applied} applied, {retried} retried, {sent} follow-ups")
            logger.info(f"  Totals:        {self.total_applied} applied, {self.total_retried} retried, {self.total_followups} follow-ups")

            if self.mega_master:
                ms = await self.mega_master.get_swarm_status()
                logger.info(f"  Mega Swarm:    {ms.get('cycles_completed', 0)} cycles, "
                            f"{ms.get('total_agents', 0):,} agents, "
                            f"uptime {ms.get('uptime_seconds', 0):.0f}s")

            for p, ws in warmup_stats.items():
                logger.info(f"  Warmup {p}:    {ws['sent_today']}/{ws['daily_limit']} (day {ws['warmup_day']})")
            logger.info("=" * 60)
            
            # --- APEX PREDATOR UPGRADE (PHASE 8 & 9) ---
            logger.info("\n[PHASE 8] Executing Shadow HR (B2B Proactive Sales)...")
            try:
                from core.shadow_hr import run_shadow_hr_campaign
                await run_shadow_hr_campaign()
            except Exception as e:
                logger.error(f"[PHASE 8 ERROR] {e}")
                
            logger.info("\n[PHASE 9] Generating Automated Media Newsletter...")
            try:
                from core.generate_newsletter import generate_newsletter_html
                generate_newsletter_html()
            except Exception as e:
                logger.error(f"[PHASE 9 ERROR] {e}")

            return True

        except Exception as e:
            logger.error(f"Error in auto-pilot cycle: {e}")
            logger.error(traceback.format_exc())
            return False

    async def run_forever(self):
        """Run auto-pilot indefinitely."""
        logger.info("=" * 60)
        logger.info(f"  JOBHUNT PRO v{config.VERSION} - AUTO-PILOT MODE")
        logger.info("  Started at: " + self.start_time.strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("  Working hours: 8:00 - 20:00 Beirut time")
        logger.info("  Cycle interval: 30 minutes")
        logger.info("=" * 60)

        # Run first cycle immediately
        await self.run_cycle()

        while True:
            # Check if within working hours
            if not is_working_hours():
                next_check = beirut_now().replace(hour=8, minute=0, second=0)
                if next_check < beirut_now():
                    # Past 8PM today, next check is tomorrow 8AM
                    from datetime import timedelta
                    next_check = next_check + timedelta(days=1)
                sleep_seconds = (next_check - beirut_now()).total_seconds()
                logger.info(f"Outside working hours. Sleeping until {next_check.strftime('%H:%M')} Beirut time ({sleep_seconds/3600:.1f}h)...")
                await asyncio.sleep(sleep_seconds)
                continue

            # Wait 30 minutes between cycles
            logger.info("Next cycle in 30 minutes...")
            await asyncio.sleep(1800)  # 30 minutes

            try:
                await self.run_cycle()
            except Exception as e:
                logger.error(f"Cycle failed: {e}")
                traceback.print_exc()
                await asyncio.sleep(60)


async def main():
    pilot = AutoPilot()
    try:
        await pilot.run_forever()
    finally:
        # Shut down mega swarm gracefully
        if pilot.mega_master:
            logger.info("Shutting down Mega Swarm...")
            await pilot.mega_master.shutdown()
            logger.info("Mega Swarm shut down.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Auto-pilot stopped by user.")
    except Exception as e:
        logger.error(f"Auto-pilot crashed: {e}")
        traceback.print_exc()
