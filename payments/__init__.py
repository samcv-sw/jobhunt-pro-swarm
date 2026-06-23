"""
JobHunt Pro — Payments Module
Crypto payment processing for automated service delivery
Supports: BTC, ETH, USDT, LTC
"""
import json
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

import config

logger = logging.getLogger(__name__)

# Payment tracking
PAYMENTS_FILE = "cache/payments.json"


def _ensure_cache():
    os.makedirs("cache", exist_ok=True)


def _load_payments() -> Dict[str, Any]:
    _ensure_cache()
    if os.path.exists(PAYMENTS_FILE):
        try:
            with open(PAYMENTS_FILE) as f:
                return json.load(f)
        except Exception:
            return {"payments": [], "total_received": 0}
    return {"payments": [], "total_received": 0}


def _save_payments(data: Dict[str, Any]):
    _ensure_cache()
    with open(PAYMENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


_dotenv_loaded = False


def _try_load_dotenv():
    """Force-reload .env so env vars injected by PA are picked up."""
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    try:
        from dotenv import load_dotenv
        import os.path as _p
        for p in [_p.join(_p.dirname(__file__), '..', '.env'),
                   '/home/JHFGUF/jobhunt/.env',
                   '.env']:
            if _p.exists(p):
                load_dotenv(p, override=True)
                break
    except Exception:
        pass
    _dotenv_loaded = True


def get_payment_addresses() -> Dict[str, str]:
    """Get all configured crypto wallet addresses.
    Tries direct env first (covers PA web env injection), falls back to config.
    """
    _try_load_dotenv()
    return {
        "BTC": os.getenv("CRYPTO_BTC_ADDRESS", "") or config.CRYPTO_BTC_ADDRESS,
        "ETH": os.getenv("CRYPTO_ETH_ADDRESS", "") or config.CRYPTO_ETH_ADDRESS,
        "USDT": os.getenv("CRYPTO_USDT_ADDRESS", "") or config.CRYPTO_USDT_ADDRESS,
        "LTC": os.getenv("CRYPTO_LTC_ADDRESS", "") or config.CRYPTO_LTC_ADDRESS,
    }


def record_payment(
    order_id: str,
    currency: str,
    amount_usd: float,
    tx_hash: str = "",
    customer_email: str = "",
    payment_code: str = "",
    client_ip: str = "",
) -> bool:
    """Record a crypto payment. Returns True if recorded."""
    if currency.upper() not in ("BTC", "ETH", "USDT", "LTC"):
        logger.warning(f"Unsupported currency: {currency}")
        return False

    data = _load_payments()
    payment = {
        "payment_id": f"PAY-{order_id}",
        "order_id": order_id,
        "currency": currency.upper(),
        "amount_usd": amount_usd,
        "tx_hash": tx_hash or "manual",
        "customer_email": customer_email,
        "payment_code": payment_code or "",
        "client_ip": client_ip or "",
        "timestamp": datetime.now().isoformat(),
    }
    data["payments"].append(payment)
    data["total_received"] += amount_usd
    _save_payments(data)

    # Also update the order in the fulfillment system
    try:
        from services.fulfillment import ServiceFulfillment
        fulfillment = ServiceFulfillment()
        result = fulfillment.verify_payment(
            order_id=order_id,
            tx_hash=tx_hash,
            payment_code=payment_code or "ADMIN_INTERNAL",
            client_ip=client_ip or "internal",
        )
        if not result.get("success"):
            logger.warning(f"Auto-verify result for {order_id}: {result.get('message')}")
    except Exception as e:
        logger.warning(f"Could not auto-deliver: {e}")

    logger.info(
        f"Payment recorded: {currency} ${amount_usd:.2f} for order {order_id}"
    )
    return True


def get_payment_stats() -> Dict[str, Any]:
    """Get payment statistics."""
    data = _load_payments()
    payments = data["payments"]

    by_currency = {}
    for p in payments:
        cur = p["currency"]
        by_currency[cur] = by_currency.get(cur, 0) + p["amount_usd"]

    return {
        "total_payments": len(payments),
        "total_received_usd": data["total_received"],
        "by_currency": by_currency,
        "recent": payments[-5:] if payments else [],
    }
