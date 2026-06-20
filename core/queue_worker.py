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
from web.app_v2 import get_db, config

logging.basicConfig(level=logging.INFO, format="%(asctime)s: [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

    def _isolated_campaign_runner(campaign_id):
        """Executes the campaign inside a fully isolated fork (OS process)."""
        try:
            send_telegram_message_sync(f"🚀 [NODE-WORKER] Batch task {campaign_id} started processing.")
            asyncio.run(run_campaign(campaign_id, get_db, config))
            send_telegram_message_sync(f"✅ [NODE-WORKER] Batch task {campaign_id} completed successfully.")
        except Exception as e:
            logger.error(f"Isolated process crashed: {e}")
            send_telegram_message_sync(f"❌ [NODE-WORKER] Batch task {campaign_id} crashed: {str(e)}")

    async def process_queue():
        """Continuously poll and process tasks from the queue with Fork Isolation."""
        logger.info("[ML-SYSTEM] Starting background inference worker with Fork Isolation...")
        
        while True:
            try:
                task = dequeue_task()
                if not task:
                    time.sleep(5)  # Wait 5 seconds before polling again
                    continue
                    
                task_id = task["id"]
                task_type = task["task_type"]
                payload = task["payload"]
                
                logger.info(f"[ML-SYSTEM] Processing task {task_id}: {task_type}")
                
                if task_type == "run_campaign":
                    campaign_id = payload.get("campaign_id")
                    if campaign_id:
                        # Run the campaign with FORK ISOLATION (Protects against LLM OOM crashes)
                        p = multiprocessing.Process(target=_isolated_campaign_runner, args=(campaign_id,))
                        p.start()
                        p.join(timeout=260)
                        
                        if p.is_alive():
                            logger.error(f"Task {task_id} exceeded 260s. Terminating isolated fork.")
                            p.terminate()
                            p.join()
                            fail_task(task_id, "Fork timeout")
                        else:
                            complete_task(task_id)
                    else:
                        fail_task(task_id, "Missing batch_id")
                        
                elif task_type == "cron_tick":
                    # Check for pending campaigns directly
                    conn = get_db()
                    try:
                        pending = conn.execute(
                            "SELECT campaign_id FROM campaigns WHERE status='pending' ORDER BY created_at ASC LIMIT 1"
                        ).fetchone()
                        if pending:
                            cid = pending["campaign_id"]
                            conn.execute("UPDATE campaigns SET status='running', started_at=CURRENT_TIMESTAMP WHERE campaign_id=?", (cid,))
                            conn.commit()
                            logger.info(f"[ML-SYSTEM] Cron tick picked up batch {cid}")
                            
                            p = multiprocessing.Process(target=_isolated_campaign_runner, args=(cid,))
                            p.start()
                            p.join(timeout=260)
                            
                            if p.is_alive():
                                logger.error(f"[ML-SYSTEM] Cron tick batch {cid} timed out. Terminating fork.")
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
                        engine = EmailEngine(config)
                        logger.info("[ML-SYSTEM] Triggering automated Data Sync Engine...")
                        send_telegram_message_sync("⏳ [NODE-WORKER] Running Automated Sync Engine...")
                        asyncio.run(engine.check_and_send_followups(conn))
                    except Exception as e:
                        logger.error(f"Error in sync engine: {e}")
                    finally:
                        conn.close()
                        
                    # --- Ghost Hunter (Renamed to Dataset Fetcher) ---
                    global last_ghost_hunt_time
                    if 'last_ghost_hunt_time' not in globals():
                        last_ghost_hunt_time = 0
                    
                    if time.time() - last_ghost_hunt_time > 3600: # Run every 1 hour
                        logger.info("[ML-SYSTEM] Triggering Autonomous Dataset Fetcher...")
                        send_telegram_message_sync("👻 [NODE-WORKER] Deploying Cloud-Native Dataset Fetcher...")
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
                    
            except Exception as e:
                logger.error(f"Worker loop error: {e}\n{traceback.format_exc()}")
                time.sleep(5)

if __name__ == "__main__":
    asyncio.run(process_queue())
