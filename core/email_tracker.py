import logging
import sqlite3
from datetime import datetime
import config

logger = logging.getLogger(__name__)

class EmailTracker:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DB_PATH

    def generate_tracking_pixel(self, tracking_id):
        return f'<img src="https://track.sam-salameh.com/pixel/{tracking_id}" width="1" height="1" style="display:none" />'

    def generate_tracking_link(self, tracking_id, original_url):
        return f"https://track.sam-salameh.com/click/{tracking_id}?url={original_url}"

    def record_open(self, tracking_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE applications SET opened = 1, opened_at = CURRENT_TIMESTAMP WHERE tracking_id = ?", (tracking_id,))
                conn.commit()
                logger.info(f"Email opened: {tracking_id}")
                return True
        except Exception as e:
            logger.warning(f"Track open failed: {e}")
            return False

    def record_click(self, tracking_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE applications SET clicked = 1 WHERE tracking_id = ?", (tracking_id,))
                conn.commit()
                logger.info(f"Link clicked: {tracking_id}")
                return True
        except Exception as e:
            logger.warning(f"Track click failed: {e}")
            return False

    def record_response(self, tracking_id, response_type):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("UPDATE applications SET responded = 1, response_type = ? WHERE tracking_id = ?", (response_type, tracking_id))
                job_id = conn.execute("SELECT job_id FROM applications WHERE tracking_id = ?", (tracking_id,)).fetchone()
                if job_id:
                    conn.execute("UPDATE jobs SET status = 'responded', response_type = ?, responded_at = CURRENT_TIMESTAMP WHERE job_id = ?", (response_type, job_id[0]))
                conn.commit()
                logger.info(f"Response recorded: {tracking_id} -> {response_type}")
                return True
        except Exception as e:
            logger.warning(f"Record response failed: {e}")
            return False

    def get_tracking_stats(self):
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute("SELECT COUNT(*) FROM applications WHERE tracking_id != ''").fetchone()[0]
            opened = conn.execute("SELECT COUNT(*) FROM applications WHERE opened = 1").fetchone()[0]
            clicked = conn.execute("SELECT COUNT(*) FROM applications WHERE clicked = 1").fetchone()[0]
            responded = conn.execute("SELECT COUNT(*) FROM applications WHERE responded = 1").fetchone()[0]
            return {
                "total_tracked": total,
                "opened": opened,
                "clicked": clicked,
                "responded": responded,
                "open_rate": round(opened/total*100, 1) if total > 0 else 0,
                "click_rate": round(clicked/total*100, 1) if total > 0 else 0,
                "response_rate": round(responded/total*100, 1) if total > 0 else 0,
            }
