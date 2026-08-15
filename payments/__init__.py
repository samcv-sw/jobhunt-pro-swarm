"""
JobHunt Pro — Payments Module
Crypto payment processing for automated service delivery
Supports: BTC, ETH, USDT-TRC20, USDT-Polygon, USDC-Polygon, TON, LTC with $0 merchant fees
"""
import json
import logging
import os
from datetime import datetime
from typing import Any

import config

logger = logging.getLogger(__name__)

# Payment tracking
PAYMENTS_FILE = "cache/payments.json"

ALLOWED_CURRENCIES = (
    "BTC", "ETH", "USDT", "USDT_TRC20", "USDTTRC20", "USDT_POLYGON", "USDTMATIC",
    "USDC_POLYGON", "USDCMATIC", "USDC_TRC20", "USDCTRC20", "TON", "USDTON", "LTC"
)


def _ensure_cache():
    os.makedirs("cache", exist_ok=True)


def _load_payments() -> dict[str, Any]:
    _ensure_cache()
    if os.path.exists(PAYMENTS_FILE):
        try:
            with open(PAYMENTS_FILE) as f:
                return json.load(f)
        except Exception:
            return {"payments": [], "total_received": 0}
    return {"payments": [], "total_received": 0}


def _save_payments(data: dict[str, Any]):
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
        import os.path as _p
        from dotenv import load_dotenv
        for p in [_p.join(_p.dirname(__file__), '..', '.env'),
                   '/home/JHFGUF/jobhunt/.env',
                   '.env']:
            if _p.exists(p):
                load_dotenv(p, override=True)
                break
    except Exception:
        pass
    _dotenv_loaded = True


def get_payment_addresses() -> dict[str, str]:
    """Get all configured multi-chain sovereign crypto wallet addresses ($0 merchant fee)."""
    _try_load_dotenv()
    return {
        "BTC": os.getenv("CRYPTO_BTC_ADDRESS", "") or config.CRYPTO_BTC_ADDRESS or "bc1q0e68d76d8dc303249a1992405ac2879f97fa8f",
        "ETH": os.getenv("CRYPTO_ETH_ADDRESS", "") or config.CRYPTO_ETH_ADDRESS or "0x0e68d76d8dc303249a1992405ac2879f97fa8fec",
        "USDT": os.getenv("CRYPTO_USDT_ADDRESS", "") or config.CRYPTO_USDT_ADDRESS or "0xc303249a1992405ac2879f97fa8fec34c72be2f8",
        "USDT_TRC20": os.getenv("CRYPTO_USDT_TRC20_ADDRESS", os.getenv("CRYPTO_TRON_ADDRESS", "TYDzsYUEpvnYmQk4zGP9sWWcTEd3ZiPULj")),
        "USDT_POLYGON": os.getenv("CRYPTO_POLYGON_ADDRESS", "0x0e68d76d8dc303249a1992405ac2879f97fa8fec"),
        "USDC_POLYGON": os.getenv("CRYPTO_POLYGON_ADDRESS", "0x0e68d76d8dc303249a1992405ac2879f97fa8fec"),
        "TON": os.getenv("CRYPTO_TON_ADDRESS", "EQB_k02mK3m1UoG7zW9T0z2_Z9nK3m1UoG7zW9T0z2_Z9nK3"),
        "LTC": os.getenv("CRYPTO_LTC_ADDRESS", "") or config.CRYPTO_LTC_ADDRESS or "ltc1q0e68d76d8dc303249a1992405ac2879f97fa8f",
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
    cur_upper = currency.upper().replace("-", "_").replace(" ", "")
    if cur_upper not in ALLOWED_CURRENCIES and not any(c in cur_upper for c in ("USDT", "USDC", "TON", "BTC", "ETH", "LTC")):
        logger.warning(f"Unsupported currency: {currency}")
        return False

    data = _load_payments()
    payment = {
        "payment_id": f"PAY-{order_id}",
        "order_id": order_id,
        "currency": cur_upper,
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
        f"Payment recorded: {cur_upper} ${amount_usd:.2f} for order {order_id}"
    )
    return True


def get_payment_stats() -> dict[str, Any]:
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
