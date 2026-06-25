import json
import logging
from datetime import datetime, timedelta
import sqlite3
import config

logger = logging.getLogger(__name__)

class Analytics:
    def __init__(self, db_path=None):
        self.db_path = db_path or getattr(config, "DB_PATH", None) or "jobhunt_saas_v2.db"

    def get_dashboard_data(self, days=30):
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            daily = [dict(r) for r in conn.execute("SELECT * FROM analytics WHERE date >= ? ORDER BY date", (since,)).fetchall()]

            by_source = [dict(r) for r in conn.execute("SELECT source, COUNT(*) as count FROM jobs GROUP BY source ORDER BY count DESC").fetchall()]

            by_status = [dict(r) for r in conn.execute("SELECT status, COUNT(*) as count FROM jobs GROUP BY status ORDER BY count DESC").fetchall()]

            top_companies = [dict(r) for r in conn.execute("SELECT company, COUNT(*) as count, AVG(match_score) as avg_score FROM jobs GROUP BY company ORDER BY count DESC LIMIT 10").fetchall()]

            total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
            opened = conn.execute("SELECT COUNT(*) FROM applications WHERE opened = 1").fetchone()[0]
            responded = conn.execute("SELECT COUNT(*) FROM applications WHERE responded = 1").fetchone()[0]
            response_rates = {"total": total, "opened": opened, "responded": responded, "open_rate": round(opened/total*100, 1) if total > 0 else 0, "response_rate": round(responded/total*100, 1) if total > 0 else 0}

            agent_stats = [dict(r) for r in conn.execute("SELECT agent_id, task_type, status, COUNT(*) as count FROM agent_tasks GROUP BY agent_id, task_type, status ORDER BY count DESC LIMIT 20").fetchall()]

            return {
                "daily": daily,
                "by_source": by_source,
                "by_status": by_status,
                "top_companies": top_companies,
                "response_rates": response_rates,
                "agent_stats": agent_stats,
            }

    def get_conversion_funnel(self):
        with sqlite3.connect(self.db_path) as conn:
            found = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            applied = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'applied'").fetchone()[0]
            opened = conn.execute("SELECT COUNT(*) FROM applications WHERE opened = 1").fetchone()[0]
            responded = conn.execute("SELECT COUNT(*) FROM applications WHERE responded = 1").fetchone()[0]
            interviews = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'interview'").fetchone()[0]
            offers = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'offer'").fetchone()[0]

            return {
                "found": found,
                "applied": applied,
                "apply_rate": round(applied/found*100, 1) if found > 0 else 0,
                "opened": opened,
                "open_rate": round(opened/applied*100, 1) if applied > 0 else 0,
                "responded": responded,
                "response_rate": round(responded/opened*100, 1) if opened > 0 else 0,
                "interviews": interviews,
                "interview_rate": round(interviews/responded*100, 1) if responded > 0 else 0,
                "offers": offers,
                "offer_rate": round(offers/interviews*100, 1) if interviews > 0 else 0,
            }

    def generate_html_dashboard(self, data=None):
        if not data:
            data = self.get_dashboard_data()
        funnel = self.get_conversion_funnel()

        html = f"""<!DOCTYPE html>
<html><head><title>Sam Job Hunt Dashboard</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 20px; }}
.container {{ max-width: 1200px; margin: 0 auto; }}
h1 {{ color: #0ea5e9; text-align: center; }}
.stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
.stat {{ background: #1e293b; padding: 20px; border-radius: 10px; text-align: center; }}
.stat-value {{ font-size: 28px; color: #0ea5e9; font-weight: bold; }}
.stat-label {{ color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
.funnel {{ background: #1e293b; padding: 20px; border-radius: 10px; margin: 20px 0; }}
.funnel-bar {{ background: #334155; height: 30px; border-radius: 5px; margin: 5px 0; display: flex; align-items: center; padding: 0 10px; }}
.funnel-fill {{ background: linear-gradient(90deg, #0ea5e9, #0284c7); height: 100%; border-radius: 5px; transition: width 0.5s; }}
</style></head><body>
<div class="container">
<h1>Sam Salameh - Job Hunt Dashboard</h1>
<div class="stats">
<div class="stat"><div class="stat-value">{funnel['found']}</div><div class="stat-label">Jobs Found</div></div>
<div class="stat"><div class="stat-value">{funnel['applied']}</div><div class="stat-label">Applied</div></div>
<div class="stat"><div class="stat-value">{funnel['open_rate']}%</div><div class="stat-label">Open Rate</div></div>
<div class="stat"><div class="stat-value">{funnel['response_rate']}%</div><div class="stat-label">Response Rate</div></div>
</div>
<div class="funnel"><h3>Conversion Funnel</h3>
<div class="funnel-bar">Found: {funnel['found']}</div>
<div class="funnel-bar">Applied: {funnel['applied']} ({funnel['apply_rate']}%)</div>
<div class="funnel-bar">Opened: {funnel['opened']} ({funnel['open_rate']}%)</div>
<div class="funnel-bar">Responded: {funnel['responded']} ({funnel['response_rate']}%)</div>
<div class="funnel-bar">Interviews: {funnel['interviews']} ({funnel['interview_rate']}%)</div>
<div class="funnel-bar">Offers: {funnel['offers']} ({funnel['offer_rate']}%)</div>
</div>
</div></body></html>"""
        return html
