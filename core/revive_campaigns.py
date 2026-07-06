import core.pg_sqlite_shim as sqlite3
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = "jobhunt_saas_v2.db"


def revive_campaigns():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Find failed or stuck campaigns (running for more than 12 hours)
        stuck_campaigns = conn.execute("""
            SELECT campaign_id, status, created_at 
            FROM campaigns 
            WHERE status = 'failed' OR (status = 'running' AND datetime(created_at) < datetime('now', '-12 hours'))
        """).fetchall()

        if not stuck_campaigns:
            logger.info("No failed or stuck campaigns found. Everything is healthy.")
            conn.close()
            return

        logger.info(f"Found {len(stuck_campaigns)} campaigns to revive.")

        for row in stuck_campaigns:
            campaign_id = row["campaign_id"]
            old_status = row["status"]

            # Reset the status back to pending so the cron_trigger / job_queue can pick it up
            conn.execute(
                "UPDATE campaigns SET status = 'pending', retry_count = retry_count + 1 WHERE campaign_id = ?",
                (campaign_id,),
            )
            logger.info(f"Revived campaign {campaign_id} (was {old_status}).")

        conn.commit()
        logger.info(
            "Revival complete. The backend Swarm will automatically pick these up on the next tick."
        )
        conn.close()
    except Exception as e:
        logger.error(f"Failed to revive campaigns: {e}")


if __name__ == "__main__":
    revive_campaigns()
