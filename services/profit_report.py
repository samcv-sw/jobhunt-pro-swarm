"""Profit & Revenue Reporting Engine.

Queries orders and wallet_transactions from the SQLite database,
calculates revenue/profit trends, and provides JSON/CSV export.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)

_DB_PATH: str | None = None


def _get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = os.getenv(
            "DATABASE_PATH",
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "app.db"),
        )
    return _DB_PATH


def _connect() -> sqlite3.Connection:
    path = _get_db_path()
    conn = sqlite3.connect(path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Core queries
# ---------------------------------------------------------------------------


def get_revenue_summary(
    days: int = 30,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """Aggregate revenue over the last *days*.

    Returns
    -------
    dict with keys::

        total_revenue, total_orders, avg_order_value,
        revenue_by_date, revenue_by_method, revenue_by_tier
    """
    close = conn is None
    if close:
        conn = _connect()
    try:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()

        rows = conn.execute(
            """
            SELECT amount_usd, payment_method, order_type, created_at
            FROM orders
            WHERE payment_status = 'paid'
              AND created_at >= ?
            """,
            (since,),
        ).fetchall()

        total_revenue = 0.0
        revenue_by_date: dict[str, float] = defaultdict(float)
        revenue_by_method: dict[str, float] = defaultdict(float)
        revenue_by_tier: dict[str, float] = defaultdict(float)

        for r in rows:
            amt = float(r["amount_usd"] or 0)
            total_revenue += amt
            day = (r["created_at"] or "")[:10]
            if day:
                revenue_by_date[day] += amt
            revenue_by_method[r["payment_method"] or "unknown"] += amt
            revenue_by_tier[r["order_type"] or "unknown"] += amt

        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": len(rows),
            "avg_order_value": round(total_revenue / max(len(rows), 1), 2),
            "revenue_by_date": dict(sorted(revenue_by_date.items())),
            "revenue_by_method": dict(revenue_by_method),
            "revenue_by_tier": dict(revenue_by_tier),
        }
    finally:
        if close:
            conn.close()


def get_profit_summary(
    days: int = 30,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """Estimate profit by subtracting estimated costs from revenue.

    Costs are estimated as a percentage of revenue (default 30 %)
    plus any fixed costs stored in the config.

    Returns
    -------
    dict with keys::

        gross_revenue, estimated_costs, estimated_profit,
        profit_margin_pct, cost_breakdown
    """
    rev = get_revenue_summary(days, conn)
    gross = rev["total_revenue"]

    # Estimate costs — in production these would come from a proper
    # cost-tracking table or external API.
    variable_cost_rate = float(os.getenv("PROFIT_VARIABLE_COST_RATE", "0.30"))
    fixed_costs = float(os.getenv("PROFIT_FIXED_COSTS", "0.0"))

    variable_costs = round(gross * variable_cost_rate, 2)
    total_costs = round(variable_costs + fixed_costs, 2)
    profit = round(gross - total_costs, 2)
    margin = round((profit / max(gross, 1)) * 100, 1)

    return {
        "gross_revenue": gross,
        "estimated_costs": total_costs,
        "estimated_profit": profit,
        "profit_margin_pct": margin,
        "cost_breakdown": {
            "variable_costs": variable_costs,
            "fixed_costs": fixed_costs,
            "variable_cost_rate": variable_cost_rate,
        },
    }


def get_order_trends(
    days: int = 90,
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """Daily order counts and revenue for trend analysis."""
    close = conn is None
    if close:
        conn = _connect()
    try:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            """
            SELECT DATE(created_at) AS day,
                   COUNT(*)        AS order_count,
                   SUM(amount_usd) AS revenue
            FROM orders
            WHERE payment_status = 'paid'
              AND created_at >= ?
            GROUP BY day
            ORDER BY day
            """,
            (since,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if close:
            conn.close()


def get_wallet_flow(
    days: int = 30,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """Aggregate wallet deposits, deductions, and net flow."""
    close = conn is None
    if close:
        conn = _connect()
    try:
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        rows = conn.execute(
            """
            SELECT txn_type, SUM(amount) AS total, COUNT(*) AS count
            FROM wallet_transactions
            WHERE created_at >= ?
            GROUP BY txn_type
            """,
            (since,),
        ).fetchall()
        deposits = 0.0
        deductions = 0.0
        adjustments = 0.0
        for r in rows:
            t = r["txn_type"]
            amt = float(r["total"] or 0)
            if t == "deposit":
                deposits += amt
            elif t == "deduction":
                deductions += amt
            else:
                adjustments += amt
        return {
            "total_deposits": round(deposits, 2),
            "total_deductions": round(deductions, 2),
            "total_adjustments": round(adjustments, 2),
            "net_flow": round(deposits - deductions, 2),
        }
    finally:
        if close:
            conn.close()


# ---------------------------------------------------------------------------
# Full report
# ---------------------------------------------------------------------------


def generate_full_report(days: int = 30) -> dict[str, Any]:
    """Combine all metrics into a single report dict."""
    conn = _connect()
    try:
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "period_days": days,
            "revenue": get_revenue_summary(days, conn),
            "profit": get_profit_summary(days, conn),
            "trends": get_order_trends(days, conn),
            "wallet_flow": get_wallet_flow(days, conn),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------


def export_report_json(days: int = 30, indent: int = 2) -> str:
    """Return the full report as a JSON string."""
    return json.dumps(generate_full_report(days), indent=indent, ensure_ascii=False)


def export_trends_csv(days: int = 90) -> str:
    """Return daily order trends as CSV string."""
    trends = get_order_trends(days)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["day", "order_count", "revenue"])
    for t in trends:
        writer.writerow([t["day"], t["order_count"], t["revenue"]])
    return buf.getvalue()


def export_revenue_by_method_csv(days: int = 30) -> str:
    """Return revenue-by-payment-method as CSV string."""
    rev = get_revenue_summary(days)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["payment_method", "revenue"])
    for method, amount in rev["revenue_by_method"].items():
        writer.writerow([method, amount])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Print full report to stdout when run directly."""
    import argparse

    parser = argparse.ArgumentParser(description="Profit & Revenue Report")
    parser.add_argument("--days", type=int, default=30, help="Lookback period in days")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    args = parser.parse_args()

    if args.format == "csv":
        print(export_trends_csv(args.days))
    else:
        print(export_report_json(args.days))


if __name__ == "__main__":
    main()
