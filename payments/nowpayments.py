"""
JobHunt Pro — NOWPayments.io Integration
=========================================
Cryptocurrency payment gateway with HMAC SHA-512 IPN (Instant Payment Notification)
and multi-chain stablecoin routing (USDT/USDC on TRC20, Polygon, TON with $0 merchant fees).

Features:
- Create payment invoices (BTC, ETH, USDT-TRC20, USDT-Polygon, USDC-Polygon, TON, LTC + 50+ coins)
- Canonical HMAC SHA-512 webhook verification via IPN callback
- Multi-chain currency resolution and zero merchant fees routing
- Auto-delivery on payment confirmation
- Payment status polling fallback
"""

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import config

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"
SUPPORTED_CURRENCIES = [
    "BTC", "ETH", "USDT", "USDTTRC20", "USDTMATIC", "USDCMATIC", "USDCTRC20",
    "TON", "USDTON", "LTC", "BNB", "MATIC", "SOL", "TRX", "ADA", "DOT", "DAI", "BUSD"
]

# ── API Client ─────────────────────────────────────────────────

class NOWPaymentsClient:
    """Client for NOWPayments.io API."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or config.NOWPAYMENTS_API_KEY

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

    def _request(self, method: str, path: str, data: dict = None) -> dict | None:
        """Make an API request to NOWPayments."""
        url = f"{NOWPAYMENTS_API_URL}{path}"
        body = json.dumps(data).encode() if data else None

        req = Request(url, data=body, method=method)
        for k, v in self._headers().items():
            req.add_header(k, v)

        try:
            with urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except HTTPError as e:
            err_body = e.read().decode() if e.fp else ""
            logger.error(f"NOWPayments HTTP {e.code}: {err_body}")
            return None
        except URLError as e:
            logger.error(f"NOWPayments connection error: {e.reason}")
            return None
        except Exception as e:
            logger.error(f"NOWPayments error: {e}")
            return None

    def get_currencies(self) -> list[str]:
        """Get list of supported cryptocurrencies."""
        result = self._request("GET", "/currencies")
        if result and isinstance(result, list):
            return [c.upper() for c in result]
        return SUPPORTED_CURRENCIES

    def get_minimum_amount(self, currency_from: str, currency_to: str = "usd") -> float | None:
        """Get minimum payment amount for a currency."""
        params = urlencode({
            "currency_from": currency_from.lower(),
            "currency_to": currency_to,
        })
        result = self._request("GET", f"/min-amount?{params}")
        if result and "min_amount" in result:
            return float(result["min_amount"])
        return None

    def create_invoice(
        self,
        price_amount: float,
        price_currency: str = "usd",
        pay_currency: str = "",
        order_id: str = "",
        order_description: str = "",
        ipn_callback_url: str = "",
        success_url: str = "",
        cancel_url: str = "",
        is_fixed_rate: bool = True,
        is_fee_paid_by_user: bool = True,
    ) -> dict | None:
        """
        Create a payment invoice with $0 merchant fees.
        """
        payload = {
            "price_amount": price_amount,
            "price_currency": price_currency,
            "order_id": order_id[:50] if order_id else "",
            "order_description": order_description[:200] if order_description else "",
            "ipn_callback_url": ipn_callback_url or f"{config.SITE_URL}/api/v2/nowpayments-ipn",
            "success_url": success_url or f"{config.SITE_URL}/payment-success?order_id={order_id}",
            "cancel_url": cancel_url or f"{config.SITE_URL}/checkout?order_id={order_id}",
            "is_fixed_rate": is_fixed_rate,
            "is_fee_paid_by_user": is_fee_paid_by_user,
        }
        if pay_currency:
            payload["pay_currency"] = pay_currency.lower()
        result = self._request("POST", "/invoice", payload)
        if result and "id" in result:
            logger.info(
                f"NOWPayments invoice created: #{result['id']} "
                f"for ${price_amount} (order: {order_id})"
            )
            return result
        logger.error(f"NOWPayments invoice creation failed: {result}")
        return None

    def get_payment_status(self, payment_id: int) -> dict | None:
        """Check the status of a payment."""
        result = self._request("GET", f"/payment/{payment_id}")
        if result:
            return result
        return None

    def verify_ipn(self, ipn_data: dict, headers: dict) -> bool:
        """
        Verify IPN callback HMAC-SHA512 signature.
        NOWPayments sends signature in x-nowpayments-sig header.
        Payload keys are canonicalized and sorted in ascending order.
        """
        sig = headers.get("x-nowpayments-sig") or headers.get("X-Nowpayments-Sig", "")
        ipn_secret = config.NOWPAYMENTS_IPN_SECRET

        if not ipn_secret:
            logger.critical("IPN: REJECTED — no IPN secret configured! Set NOWPAYMENTS_IPN_SECRET in .env")
            return False  # NEVER accept unverified IPN callbacks

        if not sig:
            logger.warning("IPN: Missing signature header — rejecting")
            return False

        try:
            # Canonical compact JSON with sorted keys
            sorted_dict = dict(sorted(ipn_data.items(), key=lambda item: item[0]))
            compact_json = json.dumps(sorted_dict, separators=(",", ":"), sort_keys=True).encode("utf-8")
            expected_sig = hmac.new(
                ipn_secret.encode("utf-8"),
                compact_json,
                hashlib.sha512,
            ).hexdigest()

            if not hmac.compare_digest(sig.lower(), expected_sig.lower()):
                logger.warning(f"IPN: Invalid signature — possible fraud! Received: {sig[:10]}... Expected: {expected_sig[:10]}...")
                return False
        except Exception as e:
            logger.error(f"IPN: Error computing HMAC SHA-512 signature: {e}")
            return False

        # Verify payment is in valid state
        payment_status = str(ipn_data.get("payment_status", "")).lower()
        if payment_status not in ("finished", "confirmed", "sending", "partially_paid"):
            logger.info(f"IPN: Payment {ipn_data.get('payment_id')} status={payment_status} — not yet completed")
            return False

        logger.info(f"IPN: Verified payment #{ipn_data.get('payment_id')} — {payment_status}")
        return True


# ── Payment Processing ─────────────────────────────────────────

def create_crypto_invoice(
    amount_usd: float,
    order_id: str,
    customer_email: str = "",
    service_name: str = "",
    pay_currency: str = ""
) -> dict | None:
    """
    Create a NOWPayments invoice for a service order with multi-chain routing.
    Returns invoice data or None on failure.
    """
    if not config.NOWPAYMENTS_API_KEY:
        logger.warning("NOWPayments API key not configured — falling back to manual addresses")
        return None

    # Map currency aliases for NOWPayments API
    curr = (pay_currency or "").lower().strip().replace(" ", "").replace("-", "")
    if curr in ("usdt", "usdttrc20", "trc20", "usdt(trc20)"):
        target_currency = "usdttrc20"
    elif curr in ("usdtmatic", "usdtpolygon", "usdt(polygon)"):
        target_currency = "usdtmatic"
    elif curr in ("usdcmatic", "usdcpolygon", "usdc(polygon)"):
        target_currency = "usdcmatic"
    elif curr in ("usdctrc20", "usdc(trc20)"):
        target_currency = "usdctrc20"
    elif curr in ("ton", "theopennetwork"):
        target_currency = "ton"
    elif curr in ("usdton", "usdtton", "usdt(ton)"):
        target_currency = "usdton"
    elif curr in ("any", "other", "all", ""):
        target_currency = ""
    else:
        target_currency = curr

    site_url = config.SITE_URL if (config.SITE_URL and config.SITE_URL.startswith("https://")) else "https://jhfguf.pythonanywhere.com"
    client = NOWPaymentsClient()
    
    result = client.create_invoice(
        price_amount=amount_usd,
        pay_currency=target_currency,
        order_id=order_id,
        order_description=f"JobHunt Pro: {service_name or 'Service'}",
        ipn_callback_url=f"{site_url}/api/v2/nowpayments-ipn",
        is_fixed_rate=True,
        is_fee_paid_by_user=True,
    )

    # Fallback retry if primary coin is under temporary NOWPayments maintenance
    if not result and target_currency != "trx":
        logger.warning(f"NOWPayments coin {target_currency} unavailable — retrying with TRX (TRON)...")
        result = client.create_invoice(
            price_amount=amount_usd,
            pay_currency="trx",
            order_id=order_id,
            order_description=f"JobHunt Pro: {service_name or 'Service'}",
            ipn_callback_url=f"{site_url}/api/v2/nowpayments-ipn",
            is_fixed_rate=True,
            is_fee_paid_by_user=True,
        )

    if not result:
        return None

    return {
        "nowpayments_id": result.get("id"),
        "invoice_url": result.get("invoice_url", ""),
        "pay_address": result.get("pay_address", ""),
        "pay_amount": result.get("pay_amount", 0),
        "pay_currency": result.get("pay_currency", "BTC"),
        "price_amount": result.get("price_amount", amount_usd),
        "payment_status": result.get("payment_status", "waiting"),
        "expiration_seconds": result.get("expiration_seconds", 3600),
    }


def process_ipn_callback(
    raw_body: Union[bytes, str, dict],
    headers: dict
) -> Tuple[bool, str, float, str]:
    """
    Process an IPN callback from NOWPayments.
    Safely handles raw bytes, string, or parsed dict, validates HMAC-SHA512,
    prevents replay attacks, and records payment.

    Returns: (success: bool, order_id: str, actually_paid_usd: float, message: str)
    """
    client = NOWPaymentsClient()

    # Parse input body
    ipn_data: dict = {}
    if isinstance(raw_body, bytes):
        try:
            ipn_data = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            logger.error(f"IPN: Failed to decode json from bytes: {e}")
            return False, "", 0.0, "Invalid JSON payload"
    elif isinstance(raw_body, str):
        try:
            ipn_data = json.loads(raw_body)
        except Exception as e:
            logger.error(f"IPN: Failed to parse json string: {e}")
            return False, "", 0.0, "Invalid JSON payload"
    elif isinstance(raw_body, dict):
        ipn_data = raw_body
    else:
        return False, "", 0.0, "Unsupported payload format"

    # Verify IPN signature
    if not client.verify_ipn(ipn_data, headers):
        logger.warning(f"IPN verification failed for payment #{ipn_data.get('payment_id')}")
        return False, str(ipn_data.get("order_id", "")), 0.0, "HMAC signature verification failed"

    order_id = str(ipn_data.get("order_id", "")).strip()
    payment_status = str(ipn_data.get("payment_status", "")).strip().lower()
    actually_paid = float(ipn_data.get("actually_paid_at_fiat") or ipn_data.get("actually_paid") or ipn_data.get("price_amount") or 0.0)
    payment_id = ipn_data.get("payment_id")
    tx_hash = str(ipn_data.get("purchase_id") or f"nowpayments-{payment_id}")

    if not order_id:
        logger.error("IPN: Missing order_id in callback")
        return False, "", 0.0, "Missing order_id"

    logger.info(
        f"IPN: Payment #{payment_id} for order {order_id} — "
        f"{payment_status} — ${actually_paid:.2f}"
    )

    # Replay protection: check if payment was already recorded
    from payments.crypto_verifier import on_chain_verifier
    if on_chain_verifier.is_tx_already_processed(tx_hash):
        logger.info(f"IPN: Duplicate notification for already processed tx {tx_hash}")
        return True, order_id, actually_paid, "Already processed (idempotent)"

    # Record payment in our system
    try:
        from services.fulfillment import ServiceFulfillment
        ServiceFulfillment()

        from payments import record_payment
        record_payment(
            order_id=order_id,
            currency=ipn_data.get("pay_currency", "USDT"),
            amount_usd=actually_paid or float(ipn_data.get("price_amount", 0)),
            tx_hash=tx_hash,
            customer_email="",
            payment_code="NOWPAYMENTS_IPN",
            client_ip="nowpayments.io",
        )

        on_chain_verifier.record_processed_tx(
            tx_hash=tx_hash,
            network=ipn_data.get("pay_currency", "crypto"),
            amount_usd=actually_paid,
            recipient=ipn_data.get("pay_address", "nowpayments"),
            order_id=order_id,
        )

        logger.info(f"IPN: Payment recorded for order {order_id}, delivery triggered")
        return True, order_id, actually_paid, "Payment processed successfully"

    except Exception as e:
        logger.error(f"IPN: Failed to process payment for {order_id}: {e}")
        return False, order_id, actually_paid, f"Processing error: {str(e)}"


def poll_payment_status(nowpayments_id: int, order_id: str, max_retries: int = 30) -> bool:
    """
    Poll NOWPayments for payment status (fallback if IPN fails).
    Checks every 30 seconds for up to max_retries times.
    Returns True if payment completed.
    """
    client = NOWPaymentsClient()

    for attempt in range(1, max_retries + 1):
        result = client.get_payment_status(nowpayments_id)
        if not result:
            logger.warning(f"Poll attempt {attempt}/{max_retries}: No response for order {order_id}")
            time.sleep(30)
            continue

        status = result.get("payment_status", "")
        logger.info(
            f"Poll attempt {attempt}/{max_retries}: "
            f"Order {order_id} → {status}"
        )

        if status in ("finished", "confirmed"):
            try:
                from services.fulfillment import ServiceFulfillment
                fulfillment = ServiceFulfillment()
                verify_result = fulfillment.verify_payment(
                    order_id=order_id,
                    tx_hash=f"nowpayments-{nowpayments_id}",
                    payment_code="NOWPAYMENTS_POLL",
                    client_ip="nowpayments-poll",
                )
                if verify_result.get("success"):
                    logger.info(f"Poll: Payment verified for order {order_id}")
                    return True
            except Exception as e:
                logger.error(f"Poll: Verify failed for {order_id}: {e}")

        if status == "failed":
            logger.warning(f"Poll: Payment failed for order {order_id}")
            return False

        time.sleep(30)

    logger.warning(f"Poll: Max retries reached for order {order_id}")
    return False
