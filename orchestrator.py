"""
JobHunt Pro - Orchestrator v8
Coordinates: Search -> Score -> AI Tailor -> Apply -> Follow-up -> Dashboard
Enhanced with Groq AI Personalization, Anti-Ban, Stealth, and Response Prediction
"""
import sys, os
if not os.getenv("FORCE_SQLITE"):
    try:
        from core import pg_sqlite_shim
        sys.modules['sqlite3'] = pg_sqlite_shim
    except Exception:
        pass

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict

from core.whatsapp_notifier import notify_application_submitted, notify_campaign_started
import config
from core.database import Database
from core.job_search import MultiSourceSearch
from core.curated_contacts import get_curated_contacts
from core.email_engine import EmailEngine
from core.cover_letter import CoverLetterWriter
from core.ai_tailor import ai_tailor
from core.company_research import CompanyResearch
from core.smart_scheduler import SmartScheduler
from core.analytics import Analytics
from core.anti_ban import anti_ban
from core.stealth import stealth
from core.personalizer import personalizer
from core.predictor import predictor
from core.email_warmup import warmup
from core.followup_sequence import followup_sequence

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("sam_max.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self):
        self.db = Database()
        self.search = MultiSourceSearch()
        self.email = EmailEngine()
        self.research = CompanyResearch()
        self.scheduler = SmartScheduler()
        self.analytics = Analytics()
        self.warmup = warmup
        self.healer = None
        # Lazy import healing engine
        try:
            from core.healing_engine import healing_engine
            self.healer = healing_engine
        except Exception:
            pass
        logger.info("Orchestrator v8 initialized (AI Tailoring + Anti-Ban + Personalization + Email Warmup)")

    async def run_search(self, max_results=50):
        """Search for jobs using curated contacts (guaranteed results)
        + optional live search as bonus"""
        logger.info("=" * 50)
        logger.info("JOB SEARCH PHASE")
        logger.info("=" * 50)

        all_jobs = []
        locations = config.LOCATIONS[:5]

        # Phase 1: Curated contacts (GUARANTEED results)
        for location in locations:
            curated = get_curated_contacts(location, limit=20)
            all_jobs.extend(curated)
        
        # Add all curated contacts
        all_curated = get_curated_contacts("", limit=100)
        all_jobs.extend(all_curated)
        logger.info(f"Curated contacts loaded: {len(all_jobs)}")

        # Phase 2: Quick live search (1 query only, as bonus)
        try:
            loop = asyncio.get_event_loop()
            live_jobs = await loop.run_in_executor(
                None, self.search.search_all_sources, "network engineer", "Lebanon", 10
            )
            all_jobs.extend(live_jobs)
            logger.info(f"Live search bonus: {len(live_jobs)} jobs")
        except Exception as e:
            logger.debug(f"Live search skipped: {e}")

        # Deduplicate by email
        seen_emails = set()
        unique_jobs = []
        for job in all_jobs:
            email = job.get("email", "")
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_jobs.append(job)

        logger.info(f"Total unique jobs with emails: {len(unique_jobs)}")

        # Save to DB
        saved = 0
        for job in unique_jobs:
            try:
                if await self.db.save_job(job):
                    saved += 1
            except Exception as e:
                logger.error(f"Failed to save job {job.get('company','?')}: {e}")

        logger.info(f"Search complete: {len(unique_jobs)} found, {saved} new saved")
        return saved

    async def run_apply(self, limit=None, include_failed=False):
        """Send application emails with AI tailoring, anti-ban protection and personalization"""
        limit = limit or min(config.DAILY_SEND_LIMIT, 200)
        logger.info("=" * 50)
        logger.info("APPLICATION PHASE (AI Tailoring + Anti-Ban Protection)")
        logger.info("=" * 50)

        # Get new jobs
        jobs = await self.db.get_jobs_by_status("new", limit)
        
        # Optionally retry failed jobs
        if include_failed:
            reset_count = await self.db.reset_failed_jobs(limit)
            if reset_count > 0:
                logger.info(f"Reset {reset_count} failed jobs to 'new' for retry")
                # Re-fetch to include newly reset jobs
                jobs = await self.db.get_jobs_by_status("new", limit)
        
        if not jobs:
            logger.info("No new jobs to apply to")
            return 0

        # Filter: must have email
        valid_jobs = [j for j in jobs if j.get("email")]
        if not valid_jobs:
            logger.info("No jobs with valid emails")
            return 0

        logger.info(f"Processing {len(valid_jobs)} applications...")
        applied = 0
        skipped = 0
        failed = 0

        # Get active providers (those with valid credentials registered in scheduler)
        active_providers = list(self.scheduler._active_providers) if self.scheduler._active_providers else ['gmail1']

        # Check email warmup limit - check ALL active providers
        warmup_ok = False
        for prov_name in active_providers:
            if warmup.can_send(prov_name):
                warmup_ok = True
                warmup_status = warmup.get_status(prov_name)
                logger.info(f"Warmup status ({prov_name}): {warmup_status['sent_today']}/{warmup_status['daily_limit']} sent today (day {warmup_status['warmup_day']})")
                break
        if not warmup_ok:
            logger.warning("All providers at warmup limit - stopping sends")
            return 0

        for i, job in enumerate(valid_jobs):
            try:
                company = job.get("company", "Unknown")
                title = job.get("title", "Position")
                email_addr = job.get("email", "")
                snippet = job.get("snippet", "")

                logger.info(f"[{i+1}/{len(valid_jobs)}] -> {company} ({email_addr})")

                # Anti-ban checks
                # 1. Check if honeypot
                if anti_ban.is_honeypot(email_addr, company, snippet):
                    logger.warning(f"  HONEYPOT detected: {company} - SKIPPING")
                    await self.db.update_job_status(job["job_id"], "failed", "honeypot")
                    skipped += 1
                    continue

                # 2. Check company rate limits
                can_apply, reason = anti_ban.can_apply_to_company(company)
                if not can_apply:
                    logger.info(f"  Rate limited: {company} - {reason}")
                    skipped += 1
                    continue

                # 3. Check if should blacklist
                if anti_ban.should_blacklist_company(company):
                    logger.warning(f"  Blacklisted: {company}")
                    await self.db.update_job_status(job["job_id"], "failed", "blacklisted")
                    skipped += 1
                    continue

                # 4. Wait for safe timing
                await anti_ban.wait_for_safe_timing()

                # 4b. Check warmup limit before each send - check any available provider
                any_provider_ok = any(warmup.can_send(p) for p in active_providers)
                if not any_provider_ok:
                    logger.warning(f"  All providers at warmup limit, stopping batch")
                    break

                # 5. Use stealth headers for any web requests
                headers = stealth.get_headers()

                # Personalize email
                company_info = {
                    "company": company,
                    "title": title,
                    "industry": "",
                    "contact_name": "",
                }

                # ── AI-Powered Job Scoring ──────────────────────────────
                # Score job relevance before investing time in tailoring
                relevance = await ai_tailor.score_job_relevance(title, snippet, company)
                job_score = relevance.get("score", 50)
                recommendation = relevance.get("recommendation", "maybe")
                logger.info(f"  AI Relevance Score: {job_score}/100 - {recommendation}")

                if recommendation == "skip" and job_score < 40:
                    logger.info(f"  Low relevance ({job_score}%) for {company} — SKIPPING")
                    await self.db.update_job_status(job["job_id"], "skipped", f"low_relevance_{job_score}")
                    skipped += 1
                    continue

                # ── AI-Powered Cover Letter Generation ────────────────────
                # Generate AI-tailored cover letter (with template fallback)
                try:
                    ai_letter_text = await CoverLetterWriter.write_ai(
                        company=company,
                        title=title,
                        description=snippet,
                        company_info={},  # Could add company research here
                    )
                    cover_html = CoverLetterWriter.write_html(
                        company=company,
                        title=title,
                        company_info={},
                        description=snippet,
                        ai_letter=ai_letter_text,
                    )
                    logger.info(f"  Cover letter: AI-generated")
                except Exception as e:
                    logger.warning(f"  AI cover letter failed, using template: {e}")
                    cover_html = CoverLetterWriter.write_html(company, title, {})

                # Personalize cover letter
                cover_html = personalizer.personalize_email(cover_html, company_info)

                # Predict response rate
                subject = f"Application: {title} - Sam Salameh"
                prediction = predictor.predict_response_rate(subject, cover_html, company)

                if not prediction["should_send"]:
                    reason = prediction.get("reason", "low_confidence")
                    logger.info(f"  Predictor block ({reason}) for {company} - SKIPPING")
                    await self.db.update_job_status(job["job_id"], "skipped", reason)
                    skipped += 1
                    continue

                # Send email
                success, result = await self.email.send_application(
                    email_addr, company, title, cover_html, config.CV_PATH
                )

                if success:
                    await self.db.update_job_status(job["job_id"], "applied")
                    anti_ban.record_application(company)
                    predictor.record_sent_email(company, email_addr, subject, cover_html)
                    # Track warmup - result is now the provider name (fixed in email_engine.py)
                    provider_used = result if result in active_providers else (active_providers[0] if active_providers else 'gmail1')
                    warmup.record_send(provider_used)
                    followup_sequence.register_application(company, email_addr, title)  # Register for follow-up
                    applied += 1
                    logger.info(f"  OK SENT via {provider_used} (confidence: {prediction['confidence']}%)")
                else:
                    await self.db.update_job_status(job["job_id"], "failed", result)
                    anti_ban.record_failure(company)
                    failed += 1
                    logger.warning(f"  FAILED: {result}")

                # Use scheduler's delay instead of hardcoded 2s
                delay = self.scheduler.calculate_delay()
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"  Error: {e}")
                failed += 1

        logger.info(f"Applications sent: {applied}/{len(valid_jobs)}")
        logger.info(f"Skipped: {skipped}, Failed: {failed}")
        logger.info(f"Anti-ban stats: {anti_ban.get_stats()}")
        logger.info(f"Prediction stats: {predictor.get_stats()}")
        for prov in active_providers:
            logger.info(f"Warmup status ({prov}): {warmup.get_status(prov)}")
        logger.info(f"Follow-up tracking: {followup_sequence.get_stats()}")
        return applied

    async def retry_failed(self, limit=50):
        """Retry failed jobs by resetting them to 'new' status."""
        logger.info("=" * 50)
        logger.info("RETRY FAILED JOBS")
        logger.info("=" * 50)
        reset = await self.db.reset_failed_jobs(limit)
        if reset > 0:
            logger.info(f"Reset {reset} failed jobs for retry")
            # Run apply with include_failed=False (already reset)
            applied = await self.run_apply(limit=reset)
            return applied
        logger.info("No failed jobs to retry")
        return 0

    async def run_followups(self, limit=10):
        """Send follow-up emails"""
        logger.info("Running follow-ups...")
        sent = 0
        try:
            jobs = await self.db.get_jobs_needing_followup(followup_level=1)
            for job in jobs[:limit]:
                try:
                    email_addr = job.get("email")
                    if not email_addr:
                        continue
                    success, result = await self.email.send_followup(
                        email_addr, job["company"], job["title"],
                        job.get("applied_at", ""), followup_num=1
                    )
                    if success:
                        await self.db.mark_followed_up(job["job_id"], level=1)
                        sent += 1
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Follow-up error: {e}")
        except Exception as e:
            logger.warning(f"Follow-ups failed: {e}")
        return sent

    def start_web_server(self):
        """Start the dashboard web server (skip if already running)"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', 8080))
            sock.close()
            if result == 0:
                logger.info(f"Web dashboard already running: {config.SITE_URL}")
                return
        except Exception:
            pass
        try:
            import uvicorn
            from web.app_v2 import app
            config_data = uvicorn.Config(
                app, host="0.0.0.0", port=8080,
                log_level="warning", access_log=False
            )
            server = uvicorn.Server(config_data)
            loop = asyncio.get_event_loop()
            loop.create_task(server.serve())
            logger.info(f"Web dashboard: {config.SITE_URL}")
        except Exception as e:
            logger.warning(f"Web server failed to start: {e}")

    async def run_hyper_cycle(self):
        """Run one Turbo Hyper Mode cycle (zero AI, 2000+/hour)."""
        logger.info("=" * 60)
        logger.info("  [TURBO] JOBHUNT PRO - HYPER MODE TURBO")
        logger.info("=" * 60)
        try:
            from core.hyper_mode import HyperMode
            hyper = HyperMode()
            try:
                result = hyper.run(scrape=True)
                logger.info(f"[HYPER] Sent {result.get('sent', 0)} at {result.get('emails_per_hour', 0):.0f}/hour")
                return result
            finally:
                hyper.close()
        except Exception as e:
            logger.error(f"[HYPER] Cycle failed: {e}")
            return {"sent": 0, "failed": 0}

    async def run_full_cycle(self):
        """Run one complete cycle: Search -> Apply -> Follow-up"""
        logger.info("=" * 60)
        logger.info("  JOBHUNT PRO v8 - FULL CYCLE")
        logger.info("=" * 60)

        # Run healing check at start of each cycle
        if self.healer:
            try:
                report = await self.healer.diagnose_and_heal(force=True)
                if report.get("issues_detected", 0) > 0:
                    logger.info(f"[OK] Healing at cycle start: {report['auto_fixed']} auto-fixed, {report['need_attention']} need attention")
                    if report.get("need_attention", 0) > 0 and report.get("issues_detected", 0) > 0:
                        # Try to notify via telegram if available
                        try:
                            from core.healing_engine import _telegram_notify
                            await _telegram_notify(report["summary_text"][:1500])
                        except Exception:
                            pass
            except Exception as heal_err:
                logger.debug(f"Healing check at cycle start: {heal_err}")

        # Create DB tables if they don't exist
        try:
            await self.db.create_tables()
            logger.info("DB tables verified")
        except Exception as e:
            logger.warning(f"DB table creation: {e}")

        # Start web server in background
        self.start_web_server()

        # Phase 1: Search (Scout Mode)
        found = await self.run_search()

        # Phase 2: Apply
        # DELEGATED TO CLOUD WORKER SWARM (worker_node.py)
        # The orchestrator no longer applies directly to save resources and prevent IP bans.
        # It simply feeds the Neon PostgreSQL queue.
        applied = 0
        retried = 0

        # Phase 3: Follow-ups
        followed = await self.run_followups()

        # Phase 4: Stats
        logger.info("=" * 60)
        logger.info("  CYCLE COMPLETE")
        logger.info(f"  Jobs found:    {found}")
        logger.info(f"  Queued:        {found} jobs sent to worker swarm")
        logger.info(f"  Follow-ups:    {followed}")
        logger.info(f"  Anti-ban:      {anti_ban.get_stats()}")
        logger.info(f"  Predictions:   {predictor.get_stats()}")
        active_providers = list(self.scheduler._active_providers) if self.scheduler._active_providers else ['gmail1']
        for prov in active_providers:
            logger.info(f"  Warmup ({prov}): {warmup.get_status(prov)}")
        logger.info(f"  Follow-ups:    {followup_sequence.get_stats()}")
        # Phase 4.5: Resume any PENDING or RUNNING campaigns
        try:
            logger.info("=" * 60)
            logger.info("  RESUMING CAMPAIGNS")
            logger.info("=" * 60)
            from core.campaign_runner import run_campaign
            import sqlite3
            import os
            def local_get_db():
                c = sqlite3.connect(os.environ.get('DB_PATH', 'jobhunt_saas_v2.db'), timeout=30)
                c.row_factory = sqlite3.Row
                return c
            import config
            
            conn = local_get_db()
            try:
                import pa_fix
                pa_fix.run_fix()
            except Exception as fix_e:
                logger.error(f"Failed to run pa_fix: {fix_e}")
                
            active_camps = conn.execute("SELECT campaign_id FROM campaigns WHERE status IN ('pending', 'running')").fetchall()
            for c_row in active_camps:
                cid = c_row["campaign_id"]
                logger.info(f"  [CAMPAIGN] Resuming {cid}...")
                await run_campaign(cid, local_get_db, config)
        except Exception as camp_err:
            logger.exception("Campaign resume failed: %s", camp_err)
            
        logger.info("=" * 60)
        # Phase 5: Hyper Mode (turbo) if configured
        if config.HYPER_MODE_ENABLED:
            try:
                logger.info("=" * 60)
                logger.info("  PHASE 5: HYPER MODE (Turbo - Zero AI)")
                logger.info("=" * 60)
                from core.hyper_mode import HyperMode
                hyper = HyperMode()
                try:
                    hyper_result = hyper.run(scrape=False)  # Don't rescrape, use existing
                    logger.info(f"  [HYPER] Sent: {hyper_result.get('sent', 0)}  |  "
                                f"Speed: {hyper_result.get('emails_per_hour', 0):.0f}/hour")
                    
                    # Add to results
                    results_hyper = hyper_result
                finally:
                    hyper.close()
                
                return {
                    "found": found, "applied": applied, "retried": retried, "followups": followed,
                    "hyper_sent": results_hyper.get("sent", 0),
                    "hyper_speed": results_hyper.get("emails_per_hour", 0),
                }
            except Exception as e:
                logger.warning(f"[HYPER] Phase 5 skipped: {e}")
        
        return {"found": found, "applied": applied, "retried": retried, "followups": followed}


async def main():
    """Main entry point"""
    orch = Orchestrator()
    
    # Run first cycle immediately
    result = await orch.run_full_cycle()
    
    # Keep running cycles every 30 minutes
    while True:
        logger.info("Next cycle in 30 minutes...")
        await asyncio.sleep(1800)
        try:
            await orch.run_full_cycle()
        except Exception as e:
            logger.error(f"Cycle failed: {e}")
            await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
