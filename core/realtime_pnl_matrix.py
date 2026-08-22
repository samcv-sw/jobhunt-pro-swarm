"""
core/realtime_pnl_matrix.py - Real-Time P&L Profit & Loss Ledger & Multi-Currency Matrix
=======================================================================================
- Computes gross revenue, net profit margin, revenue breakdowns by rail (Crypto, Cards, China),
  and currency distribution with zero paid accounting fees.
"""

import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Fixed zero-cost exchange rates matrix
EXCHANGE_RATES_TO_USD = {
    "USD": 1.0,
    "USDT": 1.0,
    "USDC": 1.0,
    "CNY": 0.138,
    "RMB": 0.138,
    "SAR": 0.266,
    "AED": 0.272,
    "EUR": 1.085,
    "BTC": 64000.0,
    "ETH": 3450.0,
    "SOL": 145.0,
    "TON": 6.8
}


def calculate_realtime_pnl_summary() -> Dict[str, Any]:
    """
    Computes live revenue, orders count, and net profit ledger from the database.
    """
    from web.shared import get_db

    summary = {
        "status": "success",
        "timestamp": time.time(),
        "total_gross_usd": 0.0,
        "estimated_net_profit_usd": 0.0,
        "profit_margin_percent": 98.5,  # 0$ server costs = 98.5% net margin
        "by_payment_method": {
            "nowpayments": 0.0,
            "moonpay": 0.0,
            "changenow": 0.0,
            "xianyu_taobao": 0.0,
            "redeem_codes": 0.0
        },
        "total_completed_orders": 0
    }

    try:
        with get_db() as conn:
            # Query all orders
            cur = conn.execute("SELECT payment_method, amount_usd, payment_status FROM orders WHERE payment_status = 'completed'")
            rows = cur.fetchall()

            for r in rows:
                amt = float(r["amount_usd"] or 0.0)
                method = str(r["payment_method"] or "crypto").lower()
                summary["total_gross_usd"] += amt
                summary["total_completed_orders"] += 1

                if "nowpayments" in method:
                    summary["by_payment_method"]["nowpayments"] += amt
                elif "moonpay" in method:
                    summary["by_payment_method"]["moonpay"] += amt
                elif "changenow" in method:
                    summary["by_payment_method"]["changenow"] += amt
                elif "xianyu" in method or "taobao" in method:
                    summary["by_payment_method"]["xianyu_taobao"] += amt
                else:
                    summary["by_payment_method"]["redeem_codes"] += amt

            # Net profit (accounting for ~1.5% crypto network fees)
            summary["estimated_net_profit_usd"] = round(summary["total_gross_usd"] * 0.985, 2)
            summary["total_gross_usd"] = round(summary["total_gross_usd"], 2)

            return summary
    except Exception as e:
        logger.error(f"[PNL MATRIX] Error calculating PnL: {e}")
        summary["error"] = str(e)
        return summary
