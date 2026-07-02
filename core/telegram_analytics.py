"""
Telegram In-Bot Analytics Dashboard
Real-time job hunt analytics inside Telegram

Provides ASCII charts, conversion funnels, trend analysis,
company intelligence, and comprehensive personal dashboards.

Used by telegram_bot.py handlers: /stats, /trend, /funnel, /companies
"""

import os

if not os.getenv("FORCE_SQLITE"):
    try:
        from core import pg_sqlite_shim as sqlite3
    except ImportError:
        import sqlite3
else:
    import sqlite3
import time
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TelegramAnalytics:
    """In-bot analytics engine for Telegram commands."""

    BLOCK_CHARS = "█▉▊▋▌▍▎▏"

    def __init__(self, db_path: str = ""):
        self.db_path = db_path

    def _get_conn(self) -> sqlite3.Connection:
        """Get a SQLite connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ═══════════════════════════════════════════════════════════════
    #  /stats — Personal Dashboard
    # ═══════════════════════════════════════════════════════════════

    def get_user_stats(self, args: str = "") -> Dict[str, Any]:
        """Get comprehensive stats for the dashboard."""
        conn = None
        try:
            conn = self._get_conn()
            now = time.time()
            now - (now % 86400)
            now - 86400 * 7
            today_str = datetime.now().strftime("%Y-%m-%d")
            week_ago_str = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

            # ── Application counts ──────────────────────────────
            apps_today = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE sent_at >= ?", (today_str,)
            ).fetchone()[0]

            apps_week = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE sent_at >= ?", (week_ago_str,)
            ).fetchone()[0]

            apps_all = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]

            # ── Responses & interviews ──────────────────────────
            responded = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE responded = 1"
            ).fetchone()[0]

            response_rate = (
                round((responded / apps_all) * 100, 1) if apps_all > 0 else 0.0
            )

            interviews = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE response_type = 'interview'"
            ).fetchone()[0]

            # ── Email stats ─────────────────────────────────────
            emails_sent = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails"
            ).fetchone()[0]

            emails_opened = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE opened_at IS NOT NULL"
            ).fetchone()[0]

            # emails_clicked not in campaign_emails schema (no clicked_at column)
            emails_clicked = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE clicked = 1"
            ).fetchone()[0]

            emails_responded = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE responded_at IS NOT NULL"
            ).fetchone()[0]

            emails_today = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE date(sent_at) = ?",
                (today_str,),
            ).fetchone()[0]

            # ── Open / Click / Response rates ───────────────────
            open_rate = (
                round((emails_opened / emails_sent) * 100, 1)
                if emails_sent > 0
                else 0.0
            )
            click_rate = (
                round((emails_clicked / emails_sent) * 100, 1)
                if emails_sent > 0
                else 0.0
            )
            email_response_rate = (
                round((emails_responded / emails_sent) * 100, 1)
                if emails_sent > 0
                else 0.0
            )

            # ── Active campaigns ────────────────────────────────
            active_campaigns = conn.execute(
                "SELECT COUNT(*) FROM campaigns WHERE status IN ('running', 'pending', 'active')"
            ).fetchone()[0]

            total_campaigns = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()[
                0
            ]

            # ── ATS match average ───────────────────────────────
            avg_ats = conn.execute(
                "SELECT AVG(match_score) FROM jobs WHERE match_score IS NOT NULL"
            ).fetchone()[0]
            avg_ats = round(avg_ats, 1) if avg_ats else 0.0

            top_ats = conn.execute(
                "SELECT match_score FROM jobs WHERE match_score IS NOT NULL ORDER BY match_score DESC LIMIT 1"
            ).fetchone()
            best_ats_score = round(top_ats[0], 1) if top_ats else 0.0

            # ── Jobs found ──────────────────────────────────────
            jobs_found = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            jobs_today = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE date(created_at) = ?", (today_str,)
            ).fetchone()[0]

            jobs_applied = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE applied_at IS NOT NULL"
            ).fetchone()[0]

            # ── Money / wallet ──────────────────────────────────
            wallet = conn.execute(
                "SELECT COALESCE(SUM(wallet_balance), 0) FROM users"
            ).fetchone()[0]
            total_spent = conn.execute(
                "SELECT COALESCE(SUM(total_spent), 0) FROM users"
            ).fetchone()[0]

            # ── Revenue from orders ─────────────────────────────
            revenue = conn.execute(
                "SELECT COALESCE(SUM(amount_usd), 0) FROM orders WHERE payment_status = 'completed'"
            ).fetchone()[0]

            # ── Source breakdown ────────────────────────────────
            sources = [
                dict(r)
                for r in conn.execute(
                    "SELECT source, COUNT(*) as cnt FROM jobs WHERE source IS NOT NULL "
                    "GROUP BY source ORDER BY cnt DESC LIMIT 5"
                ).fetchall()
            ]

            # ── Status breakdown ────────────────────────────────
            statuses = [
                dict(r)
                for r in conn.execute(
                    "SELECT status, COUNT(*) as cnt FROM applications "
                    "GROUP BY status ORDER BY cnt DESC"
                ).fetchall()
            ]

            return {
                "error": None,
                # Applications
                "apps_today": apps_today,
                "apps_week": apps_week,
                "apps_all": apps_all,
                # Responses
                "responded": responded,
                "response_rate": response_rate,
                "interviews": interviews,
                # Email
                "emails_sent": emails_sent,
                "emails_opened": emails_opened,
                "emails_clicked": emails_clicked,
                "emails_responded": emails_responded,
                "emails_today": emails_today,
                "open_rate": open_rate,
                "click_rate": click_rate,
                "email_response_rate": email_response_rate,
                # Campaigns
                "active_campaigns": active_campaigns,
                "total_campaigns": total_campaigns,
                # ATS
                "avg_ats": avg_ats,
                "best_ats_score": best_ats_score,
                # Jobs
                "jobs_found": jobs_found,
                "jobs_today": jobs_today,
                "jobs_applied": jobs_applied,
                # Money
                "wallet": wallet,
                "total_spent": total_spent,
                "revenue": revenue,
                # Breakdowns
                "top_sources": sources,
                "statuses": statuses,
            }
        except Exception as e:
            logger.error(f"[TelegramAnalytics] get_user_stats error: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

    def format_stats_message(self, stats: Dict[str, Any]) -> str:
        """Format raw stats into a beautiful Telegram HTML message."""
        if stats.get("error"):
            return f"<b>❌ Analytics Error:</b> {stats['error']}"

        def pct(val: float) -> str:
            return f"{val:.1f}%"

        lines = [
            "<b>📊 PERSONAL DASHBOARD</b>",
            "",
            "<b>📬 APPLICATIONS</b>",
            f"  Today:        <b>{stats['apps_today']}</b>",
            f"  This Week:    <b>{stats['apps_week']}</b>",
            f"  All Time:     <b>{stats['apps_all']}</b>",
            "",
            "<b>📈 RESPONSE METRICS</b>",
            f"  Responded:    <b>{stats['responded']}</b> ({pct(stats['response_rate'])})",
            f"  Interviews:   <b>{stats['interviews']}</b>",
            "",
            "<b>📧 EMAIL PERFORMANCE</b>",
            f"  Sent:         <b>{stats['emails_sent']}</b> (today: {stats['emails_today']})",
            f"  Opened:       <b>{stats['emails_opened']}</b> ({pct(stats['open_rate'])})",
            f"  Clicked:      <b>{stats['emails_clicked']}</b> ({pct(stats['click_rate'])})",
            f"  Replied:      <b>{stats['emails_responded']}</b> ({pct(stats['email_response_rate'])})",
            "",
            "<b>🎯 CAMPAIGNS</b>",
            f"  Active:       <b>{stats['active_campaigns']}</b> / {stats['total_campaigns']} total",
            "",
            "<b>🧠 ATS MATCH SCORES</b>",
            f"  Average:      <b>{stats['avg_ats']}%</b>",
            f"  Best Match:   <b>{stats['best_ats_score']}%</b>",
            "",
            "<b>💼 JOB POOL</b>",
            f"  Total Found:  <b>{stats['jobs_found']}</b>",
            f"  New Today:    <b>{stats['jobs_today']}</b>",
            f"  Applied:      <b>{stats['jobs_applied']}</b>",
            "",
            "<b>💰 FINANCIAL</b>",
            f"  Wallet:       <b>${stats['wallet']:.2f}</b>",
            f"  Total Spent:  <b>${stats['total_spent']:.2f}</b>",
            f"  Revenue:      <b>${stats['revenue']:.2f}</b>",
        ]

        # Append top sources if available
        if stats.get("top_sources"):
            lines.append("")
            lines.append("<b>🌐 TOP SOURCES</b>")
            for s in stats["top_sources"]:
                lines.append(f"  {s['source'] or 'Unknown'}: <b>{s['cnt']}</b> jobs")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    #  /funnel — Application Conversion Funnel
    # ═══════════════════════════════════════════════════════════════

    def get_funnel(self, args: str = "") -> Dict[str, Any]:
        """Build the application conversion funnel."""
        conn = None
        try:
            conn = self._get_conn()

            # Stage 0: Jobs found
            found = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

            # Stage 1: Applied (jobs with applied_at set)
            applied = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE applied_at IS NOT NULL"
            ).fetchone()[0]

            # Stage 2: Applications sent
            apps_sent = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]

            # Use the larger of jobs.applied or apps count as baseline
            apps_total = max(applied, apps_sent, 1)

            # Stage 3: Viewed / Opened
            apps_opened = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE opened = 1"
            ).fetchone()[0]

            # Also check campaign_emails for opens
            emails_opened = conn.execute(
                "SELECT COUNT(*) FROM campaign_emails WHERE opened_at IS NOT NULL"
            ).fetchone()[0]

            # Stage 4: Responded
            apps_responded = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE responded = 1"
            ).fetchone()[0]

            # Stage 5: Interview
            apps_interview = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE response_type = 'interview'"
            ).fetchone()[0]

            # Also check jobs table for interview status
            jobs_interview = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status = 'interview'"
            ).fetchone()[0]
            total_interview = max(apps_interview, jobs_interview)

            # Stage 6: Offer
            apps_offer = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE response_type = 'offer' OR status = 'offer'"
            ).fetchone()[0]

            jobs_offer = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE status = 'offer'"
            ).fetchone()[0]
            total_offer = max(apps_offer, jobs_offer)

            # Stage 7: Hired / Accepted
            apps_hired = conn.execute(
                "SELECT COUNT(*) FROM applications WHERE status = 'hired' OR response_type = 'hired'"
            ).fetchone()[0]

            return {
                "error": None,
                "found": found,
                "applied": apps_total,
                "opened": max(apps_opened, emails_opened),
                "responded": apps_responded,
                "interview": total_interview,
                "offer": total_offer,
                "hired": apps_hired,
            }
        except Exception as e:
            logger.error(f"[TelegramAnalytics] get_funnel error: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

    def generate_funnel_chart(self, data: Dict[str, Any], max_width: int = 20) -> str:
        """Generate a visual ASCII funnel chart for Telegram."""
        if data.get("error"):
            return f"<b>❌ Funnel Error:</b> {data['error']}"

        stages = [
            ("Applied", data["applied"]),
            ("Viewed", data["opened"]),
            ("Responded", data["responded"]),
            ("Interview", data["interview"]),
            ("Offer", data["offer"]),
            ("Hired", data["hired"]),
        ]

        baseline = max(data["applied"], 1)

        # Calculate label padding
        max_label_len = max(len(s[0]) for s in stages)

        lines = ["<pre>┌──────────────────────────────────────┐"]
        lines.append("│      📊 APPLICATION FUNNEL           │")
        lines.append("├──────────────────────────────────────┤")

        for label, count in stages:
            pct = (count / baseline * 100) if baseline > 0 else 0
            bar_len = int(round(pct / 100 * max_width))
            bar = "█" * min(bar_len, max_width)

            label_padded = label.rjust(max_label_len)
            count_str = f"{count}"
            pct_str = f"({pct:.1f}%)"

            # Truncate bar length for tight fit
            available = 32 - max_label_len - 1 - 7 - 7
            displayed_bar = bar[:available] if len(bar) > available else bar

            lines.append(
                f"│ {label_padded} {displayed_bar} {count_str:>4} {pct_str:>6} │"
            )

        lines.append("└──────────────────────────────────────┘</pre>")

        # Summary below the chart
        lines.append("")
        lines.append(f"<b>📈 Funnel Summary</b>")
        if baseline > 0:
            lines.append(f"Open Rate: <b>{(data['opened'] / baseline * 100):.1f}%</b>")
            lines.append(
                f"Response Rate: <b>{(data['responded'] / baseline * 100):.1f}%</b>"
            )
            if data["responded"] > 0:
                lines.append(
                    f"Interview Rate: <b>{(data['interview'] / data['responded'] * 100):.1f}%</b>"
                )
            if data["interview"] > 0:
                lines.append(
                    f"Offer Rate: <b>{(data['offer'] / max(data['interview'], 1) * 100):.1f}%</b>"
                )

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    #  /trend [period] — Trend Analysis with ASCII Bar Chart
    # ═══════════════════════════════════════════════════════════════

    def get_trends(self, args: str = "") -> Dict[str, Any]:
        """Get application volume trends over a period."""
        conn = None
        try:
            period = (args or "week").strip().lower()
            if period in ("week", "7", "7d"):
                days = 7
                label = "7-Day"
            elif period in ("month", "30", "30d"):
                days = 30
                label = "30-Day"
            elif period in ("14", "14d", "2w", "fortnight"):
                days = 14
                label = "14-Day"
            elif period in ("90", "90d", "3m", "quarter"):
                days = 90
                label = "90-Day"
            else:
                try:
                    days = int(period)
                    days = max(1, min(days, 365))
                    label = f"{days}-Day"
                except (TypeError, ValueError):
                    days = 7
                    label = "7-Day"

            conn = self._get_conn()

            daily_data = []
            for i in range(days - 1, -1, -1):
                d = datetime.now() - timedelta(days=i)
                date_str = d.strftime("%Y-%m-%d")
                day_name = d.strftime("%a")

                # Count apps sent that day
                apps = conn.execute(
                    "SELECT COUNT(*) FROM applications WHERE date(sent_at) = ?",
                    (date_str,),
                ).fetchone()[0]

                # Count emails sent that day
                emails = conn.execute(
                    "SELECT COUNT(*) FROM campaign_emails WHERE date(sent_at) = ?",
                    (date_str,),
                ).fetchone()[0]

                # Count responses that day
                responses = conn.execute(
                    "SELECT COUNT(*) FROM campaign_emails WHERE date(responded_at) = ?",
                    (date_str,),
                ).fetchone()[0]

                # Count jobs found that day
                jobs_new = conn.execute(
                    "SELECT COUNT(*) FROM jobs WHERE date(created_at) = ?", (date_str,)
                ).fetchone()[0]

                daily_data.append(
                    {
                        "date": date_str,
                        "day": day_name,
                        "apps": apps,
                        "emails": emails,
                        "responses": responses,
                        "jobs_found": jobs_new,
                        "total": apps + emails,  # total activity
                    }
                )

            # Compute stats
            total_apps = sum(d["apps"] for d in daily_data)
            total_emails = sum(d["emails"] for d in daily_data)
            total_responses = sum(d["responses"] for d in daily_data)
            total_jobs_found = sum(d["jobs_found"] for d in daily_data)

            best_day = max(daily_data, key=lambda d: d["total"]) if daily_data else None
            worst_day = (
                min(daily_data, key=lambda d: d["total"]) if daily_data else None
            )
            avg_per_day = round(total_apps / days, 1) if days > 0 else 0

            # Growth/decline: compare first half vs second half
            half = days // 2
            first_half_total = (
                sum(d["apps"] for d in daily_data[:half]) if half > 0 else 0
            )
            second_half_total = (
                sum(d["apps"] for d in daily_data[half:]) if half > 0 else 0
            )

            if first_half_total > 0:
                growth_pct = round(
                    (second_half_total - first_half_total) / first_half_total * 100, 1
                )
            else:
                growth_pct = 0.0 if second_half_total == 0 else 100.0

            # Streak: consecutive days with activity
            current_streak = 0
            for d in reversed(daily_data):
                if d["total"] > 0:
                    current_streak += 1
                else:
                    break
            longest_streak = current_streak
            temp_streak = 0
            for d in daily_data:
                if d["total"] > 0:
                    temp_streak += 1
                    longest_streak = max(longest_streak, temp_streak)
                else:
                    temp_streak = 0

            return {
                "error": None,
                "period": label,
                "days": days,
                "daily": daily_data,
                "total_apps": total_apps,
                "total_emails": total_emails,
                "total_responses": total_responses,
                "total_jobs_found": total_jobs_found,
                "avg_per_day": avg_per_day,
                "best_day": best_day,
                "worst_day": worst_day,
                "growth_pct": growth_pct,
                "active_days": sum(1 for d in daily_data if d["total"] > 0),
                "current_streak": current_streak,
                "longest_streak": longest_streak,
            }
        except Exception as e:
            logger.error(f"[TelegramAnalytics] get_trends error: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

    def generate_trend_chart(self, data: Dict[str, Any], max_bar: int = 10) -> str:
        """Generate ASCII bar chart for trend data."""
        if data.get("error"):
            return f"<b>❌ Trend Error:</b> {data['error']}"

        daily = data["daily"]
        if not daily:
            return "<b>📉 No trend data available.</b>"

        max_val = max(d["total"] for d in daily) if daily else 1
        max_val = max(max_val, 1)

        # Header
        lines = [
            f"<b>📈 {data['period']} APPLICATION TREND</b>",
            f"<pre>",
        ]

        # Chart: each day gets a bar
        for d in daily:
            bar_len = int(round(d["total"] / max_val * max_bar))
            bar = "█" * bar_len + "░" * (max_bar - bar_len)
            marker = (
                "🔴"
                if d["total"] == 0
                else ("🟢" if d["total"] >= max_val * 0.5 else "🟡")
            )
            lines.append(f"{marker} {d['day']} {d['date'][5:]} {bar} {d['total']:>3}")

        lines.append("</pre>")

        # Stats summary
        trend_arrow = (
            "📈"
            if data["growth_pct"] > 0
            else ("📉" if data["growth_pct"] < 0 else "➡️")
        )
        growth_str = (
            f"+{data['growth_pct']}%"
            if data["growth_pct"] > 0
            else f"{data['growth_pct']}%"
        )

        lines.extend(
            [
                "",
                "<b>📊 Trend Stats</b>",
                f"Total Apps:    <b>{data['total_apps']}</b>",
                f"Total Emails:  <b>{data['total_emails']}</b>",
                f"Avg/Day:       <b>{data['avg_per_day']}</b>",
                f"Growth:        <b>{trend_arrow} {growth_str}</b>",
                f"Active Days:   <b>{data['active_days']}/{data['days']}</b>",
                f"Streak:        <b>{data['current_streak']} days</b> (best: {data['longest_streak']})",
            ]
        )

        if data["best_day"]:
            bd = data["best_day"]
            lines.append(
                f"Best Day:      <b>{bd['day']} {bd['date']}</b> ({bd['total']} sent)"
            )
        if data["worst_day"]:
            wd = data["worst_day"]
            # Don't show worst if it's a day with 0 (could be today hasn't started)
            if wd["total"] > 0 or data["days"] > 7:
                lines.append(
                    f"Worst Day:     <b>{wd['day']} {wd['date']}</b> ({wd['total']} sent)"
                )

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    #  /companies [name|top] — Company Intelligence
    # ═══════════════════════════════════════════════════════════════

    def get_top_companies(self, limit: int = 10) -> Dict[str, Any]:
        """Get most applied-to companies."""
        conn = None
        try:
            conn = self._get_conn()

            # Top companies by application count
            top = [
                dict(r)
                for r in conn.execute(
                    "SELECT a.company, COUNT(*) as apps, "
                    "SUM(CASE WHEN a.status = 'responded' OR a.responded = 1 THEN 1 ELSE 0 END) as responses, "
                    "AVG(j.match_score) as avg_score "
                    "FROM applications a "
                    "LEFT JOIN jobs j ON a.company = j.company "
                    "WHERE a.company IS NOT NULL AND a.company != '' "
                    "GROUP BY a.company ORDER BY apps DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            ]

            # Also check jobs table for companies
            jobs_top = [
                dict(r)
                for r in conn.execute(
                    "SELECT company, COUNT(*) as jobs, "
                    "AVG(match_score) as avg_score "
                    "FROM jobs WHERE company IS NOT NULL AND company != '' "
                    "GROUP BY company ORDER BY jobs DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            ]

            # Merge both results
            merged = {}
            for c in top:
                merged[c["company"]] = {
                    "company": c["company"],
                    "apps": c["apps"],
                    "responses": c.get("responses", 0),
                    "avg_score": round(c.get("avg_score", 0) or 0, 1),
                }
            for c in jobs_top:
                name = c["company"]
                if name in merged:
                    merged[name]["jobs_found"] = c["jobs"]
                    merged[name]["job_avg_score"] = round(c.get("avg_score", 0) or 0, 1)
                else:
                    merged[name] = {
                        "company": name,
                        "apps": 0,
                        "responses": 0,
                        "avg_score": round(c.get("avg_score", 0) or 0, 1),
                        "jobs_found": c["jobs"],
                    }

            # Sort by application count descending
            result = sorted(merged.values(), key=lambda x: x["apps"], reverse=True)[
                :limit
            ]

            return {
                "error": None,
                "companies": result,
                "total_unique_companies": len(merged),
            }
        except Exception as e:
            logger.error(f"[TelegramAnalytics] get_top_companies error: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

    def get_company_detail(self, company_name: str) -> Dict[str, Any]:
        """Get detailed intel on a specific company."""
        conn = None
        try:
            conn = self._get_conn()

            # Applications to this company
            apps = [
                dict(r)
                for r in conn.execute(
                    "SELECT title, status, responded, response_type, sent_at, "
                    "opened_at, responded_at "
                    "FROM applications WHERE company LIKE ? "
                    "ORDER BY sent_at DESC LIMIT 30",
                    (f"%{company_name}%",),
                ).fetchall()
            ]

            # Jobs from this company
            jobs = [
                dict(r)
                for r in conn.execute(
                    "SELECT title, status, match_score, created_at "
                    "FROM jobs WHERE company LIKE ? "
                    "ORDER BY created_at DESC LIMIT 30",
                    (f"%{company_name}%",),
                ).fetchall()
            ]

            # Emails to this company
            emails = [
                dict(r)
                for r in conn.execute(
                    "SELECT job_title, status, sent_at, opened_at, responded_at, response_type "
                    "FROM campaign_emails WHERE company_name LIKE ? "
                    "ORDER BY sent_at DESC LIMIT 30",
                    (f"%{company_name}%",),
                ).fetchall()
            ]

            # Exact match first
            exact = conn.execute(
                "SELECT company, COUNT(*) as cnt FROM applications WHERE company = ?",
                (company_name,),
            ).fetchone()

            total_apps = exact["cnt"] if exact else len(apps)
            responded_count = sum(
                1 for a in apps if a.get("responded") or a.get("response_type")
            )
            response_rate = (
                round((responded_count / total_apps) * 100, 1) if total_apps > 0 else 0
            )

            return {
                "error": None,
                "company_name": company_name,
                "total_apps": total_apps,
                "responded_count": responded_count,
                "response_rate": response_rate,
                "applications": apps,
                "jobs": jobs,
                "emails": emails,
            }
        except Exception as e:
            logger.error(f"[TelegramAnalytics] get_company_detail error: {e}")
            return {"error": str(e)}
        finally:
            if conn:
                conn.close()

    def format_companies_top(self, data: Dict[str, Any]) -> str:
        """Format top companies for Telegram."""
        if data.get("error"):
            return f"<b>❌ Companies Error:</b> {data['error']}"

        companies = data.get("companies", [])
        if not companies:
            return "<b>🏢 TOP COMPANIES</b>\n\nNo company data available yet."

        lines = [
            "<b>🏢 TOP 10 COMPANIES</b>",
            f"<i>Unique companies in database: {data.get('total_unique_companies', len(companies))}</i>",
            "",
        ]

        for i, c in enumerate(companies, 1):
            emoji = (
                "🥇" if i == 1 else ("🥈" if i == 2 else ("🥉" if i == 3 else f"{i}."))
            )
            resp_str = (
                f" | {c.get('responses', 0)} replies"
                if c.get("responses", 0) > 0
                else ""
            )
            score_str = (
                f" | ATS {c.get('avg_score', 0):.1f}%"
                if c.get("avg_score", 0) > 0
                else ""
            )
            lines.append(
                f"{emoji} <b>{c['company']}</b> — {c['apps']} apps{resp_str}{score_str}"
            )

        return "\n".join(lines)

    def format_company_detail(self, data: Dict[str, Any]) -> str:
        """Format detailed company intel for Telegram."""
        if data.get("error"):
            return f"<b>❌ Company Detail Error:</b> {data['error']}"

        name = data["company_name"]
        lines = [
            f"<b>🏢 COMPANY INTEL: {name}</b>",
            "",
            f"<b>Applications:</b> {data['total_apps']}",
            f"<b>Responses:</b> {data['responded_count']} ({data['response_rate']:.1f}%)",
            "",
        ]

        # Recent applications
        apps = data.get("applications", [])
        if apps:
            lines.append("<b>📬 Recent Applications:</b>")
            for a in apps[:10]:
                status_icon = {
                    "responded": "✅",
                    "pending": "⏳",
                    "sent": "📤",
                    "interview": "🎯",
                    "offer": "🏆",
                    "hired": "💼",
                    "viewed": "👁",
                    "opened": "👁",
                }.get(a.get("status", "pending"), "📌")

                resp = ""
                if a.get("response_type"):
                    resp = f" → {a['response_type']}"
                title = (a.get("title") or a.get("job_title") or "Unknown")[:40]
                date_str = (a.get("sent_at") or "")[:10]
                lines.append(f"  {status_icon} {title} ({date_str}){resp}")
            if len(apps) > 10:
                lines.append(f"  <i>... and {len(apps) - 10} more</i>")

        # Jobs found
        jobs = data.get("jobs", [])
        if jobs:
            lines.append("")
            lines.append("<b>💼 Jobs Found:</b>")
            for j in jobs[:5]:
                ats = (
                    f" (ATS: {j.get('match_score', 'N/A')})"
                    if j.get("match_score")
                    else ""
                )
                title = (j.get("title") or "Unknown")[:40]
                lines.append(f"  📋 {title}{ats}")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════════
    #  Helper: ASCII Bar Chart Generator
    # ═══════════════════════════════════════════════════════════════

    def generate_ascii_chart(
        self, data: Dict[str, int], max_width: int = 20, title: str = ""
    ) -> str:
        """Generate a generic ASCII bar chart for Telegram display."""
        if not data:
            return "<b>📊 No data</b>"

        max_val = max(data.values()) if data else 1
        max_val = max(max_val, 1)
        max_key_len = max(len(k) for k in data)

        lines = []
        if title:
            lines.append(f"<b>{title}</b>")
        lines.append("<pre>")

        for label, value in data.items():
            bar_len = int(round(value / max_val * max_width))
            bar = "█" * bar_len
            pct = round(value / max_val * 100, 1) if max_val > 0 else 0
            lines.append(f"  {label.ljust(max_key_len)}  {bar} {value} ({pct}%)")

        lines.append("</pre>")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  Module-level convenience
# ═══════════════════════════════════════════════════════════════════


def create_analytics(db_path: str) -> TelegramAnalytics:
    """Factory for creating TelegramAnalytics with a given DB path."""
    return TelegramAnalytics(db_path)
