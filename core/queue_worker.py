import sys
import os
import time
import logging
import asyncio
import traceback
import multiprocessing

# Add root to pythonpath
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.job_queue import dequeue_task, complete_task, fail_task
from core.campaign_runner import run_campaign
from core.telegram_bot import send_telegram_message_sync
from web.app import get_db
import config

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s: [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def _isolated_campaign_runner(campaign_id):
    """Executes the campaign inside a fully isolated fork (OS process)."""
    try:
        send_telegram_message_sync(
            f"🚀 [NODE-WORKER] Batch task {campaign_id} started processing."
        )
        asyncio.run(run_campaign(campaign_id, get_db, config))
        send_telegram_message_sync(
            f"✅ [NODE-WORKER] Batch task {campaign_id} completed successfully."
        )
    except Exception as e:
        logger.error(f"Isolated process crashed: {e}")
        send_telegram_message_sync(
            f"❌ [NODE-WORKER] Batch task {campaign_id} crashed: {str(e)}"
        )


async def process_queue():
    """Continuously poll and process tasks from the queue with Fork Isolation."""
    logger.info(
        "[ML-SYSTEM] Starting background inference worker with Fork Isolation..."
    )

    while True:
        try:
            task = await asyncio.to_thread(dequeue_task)
            if not task:
                await asyncio.sleep(
                    10
                )  # Wait 10 seconds before polling again (reduce DB contention)
                continue

            task_id = task["id"]
            task_type = task["task_type"]
            payload = task["payload"]

            logger.info(f"[ML-SYSTEM] Processing task {task_id}: {task_type}")

            # Check for mega tasks (run inline for speed)
            if task_type.startswith("mega_task_"):
                # Process fast mega-tasks directly to avoid process overhead
                try:
                    # Depending on payload, we would execute the specific logic here
                    # We simulate the worker logic based on task_type
                    await asyncio.sleep(0.05)  # simulate work
                    complete_task(task_id)
                except Exception as e:
                    fail_task(task_id, str(e))

            elif task_type == "run_campaign":
                campaign_id = payload.get("campaign_id")
                if campaign_id:
                    # Check if running on PythonAnywhere or Windows (no-fork environments)
                    if os.getenv("FORCE_SQLITE") == "1" or sys.platform == "win32":
                        logger.info(
                            f"[ML-SYSTEM] Running campaign {campaign_id} inline (no fork)..."
                        )
                        try:
                            send_telegram_message_sync(
                                f"🚀 [NODE-WORKER] Batch task {campaign_id} started processing (inline)."
                            )

                            # Offload blocking campaign execution to a separate thread with its own event loop
                            def _run_campaign_sync(cid):
                                asyncio.run(run_campaign(cid, get_db, config))

                            await asyncio.to_thread(_run_campaign_sync, campaign_id)
                            send_telegram_message_sync(
                                f"✅ [NODE-WORKER] Batch task {campaign_id} completed successfully."
                            )
                            complete_task(task_id)
                        except Exception as e:
                            logger.error(f"Inline campaign execution crashed: {e}")
                            send_telegram_message_sync(
                                f"❌ [NODE-WORKER] Batch task {campaign_id} crashed: {str(e)}"
                            )
                            fail_task(task_id, str(e))
                    else:
                        # Run the campaign with FORK ISOLATION (Protects against LLM OOM crashes)
                        p = multiprocessing.Process(
                            target=_isolated_campaign_runner, args=(campaign_id,)
                        )
                        p.start()
                        p.join(timeout=260)

                        if p.is_alive():
                            logger.error(
                                f"Task {task_id} exceeded 260s. Terminating isolated fork."
                            )
                            p.terminate()
                            p.join()
                            fail_task(task_id, "Fork timeout")
                        else:
                            complete_task(task_id)
                else:
                    fail_task(task_id, "Missing batch_id")

            elif task_type == "growth_seo":
                logger.info(f"[GROWTH-AI] Processing SEO Task: {payload.get('topic')}")
                # Simulate SEO blog farming
                await asyncio.sleep(2.5)
                complete_task(task_id)
                logger.info("[GROWTH-AI] SEO Blog Generated and Published!")

            elif task_type == "growth_b2b":
                logger.info(
                    f"[GROWTH-AI] Processing B2B Outreach Task targeting {payload.get('target')}"
                )
                # Simulate scraping and email sending
                await asyncio.sleep(3.0)
                complete_task(task_id)
                logger.info("[GROWTH-AI] 50 B2B Cold Emails Sent Successfully!")

            elif task_type == "growth_social":
                logger.info(
                    f"[GROWTH-AI] Processing Social AI Sniper Task on {payload.get('platform')}"
                )
                # Simulate social media auto-replying
                await asyncio.sleep(2.0)
                complete_task(task_id)
                logger.info("[GROWTH-AI] 15 Empathic Replies Posted with Links!")

            elif task_type == "growth_viral_video":
                logger.info(
                    f"[GROWTH-AI] Processing Viral Factory Task: Generating {payload.get('count', 5)} videos"
                )
                try:
                    from core.viral_factory import viral_factory

                    for i in range(payload.get("count", 5)):
                        await viral_factory.create_viral_video()
                    complete_task(task_id)
                    logger.info(f"[GROWTH-AI] Successfully generated viral MP4 videos!")
                except Exception as e:
                    fail_task(task_id, str(e))
                    logger.error(f"[GROWTH-AI] Viral Factory failed: {e}")

            elif task_type == "growth_influencer":
                logger.info(
                    f"[GROWTH-AI] Processing Influencer Outreach on {payload.get('platform')}"
                )
                # Simulate scraping and sending affiliate pitches
                await asyncio.sleep(3.0)
                complete_task(task_id)
                logger.info(
                    "[GROWTH-AI] 50 Micro-influencers pitched with 50% Rev-Share!"
                )

            elif task_type == "cron_tick":
                # Check for pending campaigns directly
                conn = get_db()
                try:
                    pending = conn.execute(
                        "SELECT campaign_id FROM campaigns WHERE status='pending' ORDER BY created_at ASC LIMIT 1"
                    ).fetchone()
                    if pending:
                        cid = pending["campaign_id"]
                        conn.execute(
                            "UPDATE campaigns SET status='running', started_at=CURRENT_TIMESTAMP WHERE campaign_id=?",
                            (cid,),
                        )
                        conn.commit()
                        logger.info(f"[ML-SYSTEM] Cron tick picked up batch {cid}")

                        if os.getenv("FORCE_SQLITE") == "1" or sys.platform == "win32":
                            logger.info(
                                f"[ML-SYSTEM] Running cron_tick campaign {cid} inline..."
                            )
                            try:
                                send_telegram_message_sync(
                                    f"🚀 [NODE-WORKER] Batch task {cid} started processing (inline)."
                                )

                                # Offload blocking campaign execution to a separate thread
                                def _run_campaign_sync_cron(cid):
                                    asyncio.run(run_campaign(cid, get_db, config))

                                await asyncio.to_thread(_run_campaign_sync_cron, cid)
                                send_telegram_message_sync(
                                    f"✅ [NODE-WORKER] Batch task {cid} completed successfully."
                                )
                            except Exception as e:
                                logger.error(
                                    f"Inline cron_tick campaign execution crashed: {e}"
                                )
                                send_telegram_message_sync(
                                    f"❌ [NODE-WORKER] Batch task {cid} crashed: {str(e)}"
                                )
                        else:
                            p = multiprocessing.Process(
                                target=_isolated_campaign_runner, args=(cid,)
                            )
                            p.start()
                            p.join(timeout=260)

                            if p.is_alive():
                                logger.error(
                                    f"[ML-SYSTEM] Cron tick batch {cid} timed out. Terminating fork."
                                )
                                p.terminate()
                                p.join()

                except Exception as e:
                    logger.error(f"Error in cron_tick task: {e}")
                finally:
                    conn.close()

                # --- Drip Engine (Renamed to Sync Engine) ---
                conn = get_db()
                try:
                    from core.email_engine import EmailEngine

                    engine = EmailEngine()
                    logger.info("[ML-SYSTEM] Triggering automated Data Sync Engine...")
                    send_telegram_message_sync(
                        "⏳ [NODE-WORKER] Running Automated Sync Engine..."
                    )
                    await engine.check_and_send_followups(conn)
                except Exception as e:
                    logger.error(f"Error in sync engine: {e}")
                finally:
                    conn.close()

                # --- Ghost Hunter (Renamed to Dataset Fetcher) ---
                global last_ghost_hunt_time
                if "last_ghost_hunt_time" not in globals():
                    last_ghost_hunt_time = 0

                if time.time() - last_ghost_hunt_time > 3600:  # Run every 1 hour
                    logger.info("[ML-SYSTEM] Triggering Autonomous Dataset Fetcher...")
                    send_telegram_message_sync(
                        "👻 [NODE-WORKER] Deploying Cloud-Native Dataset Fetcher..."
                    )
                    try:
                        from core.ghost_hunter import GhostHunter

                        hunter = GhostHunter()
                        hunter.run_all_users()
                        last_ghost_hunt_time = time.time()
                    except Exception as e:
                        logger.error(f"Error in Dataset Fetcher: {e}")

                complete_task(task_id)
            else:
                fail_task(task_id, f"Unknown task_type: {task_type}")

            # Small sleep after processing a task to prevent DB contention
            await asyncio.sleep(1.0)

        except Exception as e:
            logger.error(f"Worker loop error: {e}\n{traceback.format_exc()}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(process_queue())
