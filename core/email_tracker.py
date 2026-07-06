import logging
import core.pg_sqlite_shim as sqlite3
from typing import Any, Dict, Optional
import config

logger = logging.getLogger(__name__)


class EmailTracker:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = (
            db_path or getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"
        )

    def generate_tracking_pixel(self, tracking_id: str) -> str:
        if not tracking_id:
            return ""
        return f'<img src="https://track.sam-salameh.com/pixel/{tracking_id}" width="1" height="1" style="display:none" />'

    def generate_tracking_link(self, tracking_id: str, original_url: str) -> str:
        if not tracking_id or not original_url:
            return original_url or ""
        return f"https://track.sam-salameh.com/click/{tracking_id}?url={original_url}"

    def record_open(self, tracking_id: str) -> bool:
        if not tracking_id:
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE applications SET opened = 1, opened_at = CURRENT_TIMESTAMP WHERE tracking_id = ?",
                    (tracking_id,),
                )
                conn.commit()
                logger.info(f"Email opened: {tracking_id}")
                return True
        except Exception as e:
            logger.warning(f"Track open failed: {e}")
            return False

    def record_click(self, tracking_id: str) -> bool:
        if not tracking_id:
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE applications SET clicked = 1 WHERE tracking_id = ?",
                    (tracking_id,),
                )
                conn.commit()
                logger.info(f"Link clicked: {tracking_id}")
                return True
        except Exception as e:
            logger.warning(f"Track click failed: {e}")
            return False

    def record_response(self, tracking_id: str, response_type: str) -> bool:
        if not tracking_id:
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE applications SET responded = 1, response_type = ? WHERE tracking_id = ?",
                    (response_type, tracking_id),
                )
                row = conn.execute(
                    "SELECT job_id FROM applications WHERE tracking_id = ?",
                    (tracking_id,),
                ).fetchone()
                if row:
                    conn.execute(
                        "UPDATE jobs SET status = 'responded', response_type = ?, responded_at = CURRENT_TIMESTAMP WHERE job_id = ?",
                        (response_type, row[0]),
                    )
                conn.commit()
                logger.info(f"Response recorded: {tracking_id} -> {response_type}")
                return True
        except Exception as e:
            logger.warning(f"Record response failed: {e}")
            return False

    def get_tracking_stats(self) -> Dict[str, Any]:
        """Get email tracking statistics. Returns empty stats dict on DB error."""
        empty: Dict[str, Any] = {
            "total_tracked": 0,
            "opened": 0,
            "clicked": 0,
            "responded": 0,
            "open_rate": 0.0,
            "click_rate": 0.0,
            "response_rate": 0.0,
        }
        try:
            with sqlite3.connect(self.db_path) as conn:
                total = conn.execute(
                    "SELECT COUNT(*) FROM applications WHERE tracking_id != ''"
                ).fetchone()[0]
                opened = conn.execute(
                    "SELECT COUNT(*) FROM applications WHERE opened = 1"
                ).fetchone()[0]
                clicked = conn.execute(
                    "SELECT COUNT(*) FROM applications WHERE clicked = 1"
                ).fetchone()[0]
                responded = conn.execute(
                    "SELECT COUNT(*) FROM applications WHERE responded = 1"
                ).fetchone()[0]
                return {
                    "total_tracked": total,
                    "opened": opened,
                    "clicked": clicked,
                    "responded": responded,
                    "open_rate": round(opened / total * 100, 1) if total > 0 else 0.0,
                    "click_rate": round(clicked / total * 100, 1) if total > 0 else 0.0,
                    "response_rate": round(responded / total * 100, 1)
                    if total > 0
                    else 0.0,
                }
        except Exception as e:
            logger.warning(f"get_tracking_stats failed: {e}")
            return empty
