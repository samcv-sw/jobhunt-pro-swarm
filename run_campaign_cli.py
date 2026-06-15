"""CLI campaign runner — independent process spawned by cron endpoint.
Usage: python3 run_campaign_cli.py <campaign_id>
Runs a single campaign, sends up to 10 emails, then exits.
"""
import sys, os, time, json, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s [CampaignCLI] %(message)s')
logger = logging.getLogger('campaign_cli')

if len(sys.argv) < 2:
    print(json.dumps({"error": "No campaign_id provided"}))
    sys.exit(1)

campaign_id = sys.argv[1]
timeout_s = int(sys.argv[2]) if len(sys.argv) > 2 else 260

logger.info(f"Starting campaign {campaign_id} (timeout={timeout_s}s)")

# Import app modules
try:
    from web.app_v2 import get_db, config
    from core.campaign_runner import run_campaign as _run
    import asyncio
except Exception as e:
    logger.error(f"Import failed: {e}")
    print(json.dumps({"error": f"Import failed: {e}"}))
    sys.exit(1)

async def main():
    try:
        result = await asyncio.wait_for(_run(campaign_id, get_db, config), timeout=timeout_s)
        sent = result.get("sent", 0) if isinstance(result, dict) else 0
        logger.info(f"Campaign {campaign_id} completed: sent={sent}")
        print(json.dumps({"sent": sent, "campaign_id": campaign_id, "status": "completed"}))
    except asyncio.TimeoutError:
        logger.warning(f"Campaign {campaign_id} timed out after {timeout_s}s")
        # Mark as pending for next run
        try:
            conn = get_db()
            current = conn.execute("SELECT COUNT(*) FROM campaign_emails WHERE campaign_id=? AND status='sent'", (campaign_id,)).fetchone()[0]
            conn.execute("UPDATE campaigns SET status='pending', sent_count=? WHERE campaign_id=?", (current, campaign_id))
            conn.commit()
            conn.close()
        except Exception:
            pass
        print(json.dumps({"sent": "timeout", "campaign_id": campaign_id, "status": "pending_continue"}))
    except Exception as e:
        logger.error(f"Campaign {campaign_id} failed: {e}")
        try:
            conn = get_db()
            conn.execute("UPDATE campaigns SET status='failed', completed_at=CURRENT_TIMESTAMP WHERE campaign_id=?", (campaign_id,))
            conn.commit()
            conn.close()
        except Exception:
            pass
        print(json.dumps({"error": str(e), "campaign_id": campaign_id, "status": "failed"}))
    sys.stdout.flush()

asyncio.run(main())
