"""
JobHunt Pro — NOWPayments.io Integration
=========================================
Cryptocurrency payment gateway with IPN (Instant Payment Notification).

Features:
- Create payment invoices (BTC, ETH, USDT, LTC + 50+ coins)
- Webhook verification via IPN callback
- Auto-delivery on payment confirmation
- Payment status polling fallback

Setup:
1. Sign up at https://nowpayments.io
2. Get your API key from Dashboard → API Keys
3. Set NOWPAYMENTS_API_KEY in .env
4. Set NOWPAYMENTS_IPN_SECRET in .env (optional, for IPN verification)
5. Set SITE_URL in .env (for IPN callback URL)
"""

import hashlib
import hmac
import json
import logging
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import config

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"
SUPPORTED_CURRENCIES = ["BTC", "ETH", "USDT", "LTC", "BNB", "MATIC", "SOL", "TRX", "ADA", "DOT", "DAI", "BUSD"]

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
        Create a payment invoice.

        Args:
            pay_currency: Crypto currency code (e.g. "btc", "eth", "usdttrc20").
                         Leave empty to let the user choose on the invoice page.

        Returns: {
            "id": int,              # NOWPayments invoice ID
            "invoice_url": str,     # URL to send customer to
            "payment_id": str,      # Payment ID
            "payment_status": str,  # "waiting", "confirming", "confirmed", "sending", "finished", "failed"
            "pay_address": str,     # Crypto address to send payment to
            "price_amount": float,  # Amount in fiat
            "price_currency": str,  # Fiat currency
            "pay_amount": float,    # Amount in crypto
            "pay_currency": str,    # Crypto currency
            "order_id": str,        # Your internal order ID
        }
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
        Verify IPN callback signature.
        NOWPayments sends x-nowpayments-sig header.
        If NOWPAYMENTS_IPN_SECRET is not configured, we accept the callback without HMAC.
        """
        sig = headers.get("x-nowpayments-sig", "")
        ipn_secret = config.NOWPAYMENTS_IPN_SECRET

        # If IPN secret is configured, verify HMAC
        if ipn_secret:
            if not sig:
                logger.warning("IPN: Missing signature header — rejecting")
                return False
            body = json.dumps(ipn_data, sort_keys=True).encode()
            expected_sig = hmac.new(
                ipn_secret.encode(),
                body,
                hashlib.sha512,
            ).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                logger.warning("IPN: Invalid signature — possible fraud!")
                return False
        else:
            logger.critical("IPN: REJECTED — no IPN secret configured! Set NOWPAYMENTS_IPN_SECRET in .env")
            return False  # NEVER accept unverified IPN callbacks

        # Verify payment is in expected state
        payment_status = ipn_data.get("payment_status", "")
        if payment_status not in ("finished", "confirmed", "sending"):
            logger.info(f"IPN: Payment {ipn_data.get('payment_id')} status={payment_status} — not yet complete")
            return False

        logger.info(f"IPN: Verified payment #{ipn_data.get('payment_id')} — {payment_status}")
        return True


# ── Payment Processing ─────────────────────────────────────────

def create_crypto_invoice(
    amount_usd: float,
    order_id: str,
    customer_email: str = "",
    service_name: str = "",
) -> dict | None:
    """
    Create a NOWPayments invoice for a service order.
    Returns invoice data or None on failure.

    Example return:
    {
        "nowpayments_id": 12345,
        "invoice_url": "https://nowpayments.io/payment?invoice_id=...",
        "pay_address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa",
        "pay_amount": 0.0012,
        "pay_currency": "BTC",
        "price_amount": 10.0,
        "payment_status": "waiting",
    }
    """
    if not config.NOWPAYMENTS_API_KEY:
        logger.warning("NOWPayments API key not configured — falling back to manual addresses")
        return None

    client = NOWPaymentsClient()
    result = client.create_invoice(
        price_amount=amount_usd,
        order_id=order_id,
        order_description=f"JobHunt Pro: {service_name or 'Service'}",
        ipn_callback_url=f"{config.SITE_URL}/api/v2/nowpayments-ipn",
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


def process_ipn_callback(ipn_data: dict, headers: dict) -> bool:
    """
    Process an IPN callback from NOWPayments.
    Returns True if payment was successfully processed and delivery triggered.

    IPN data format:
    {
        "payment_id": int,
        "payment_status": str,
        "pay_address": str,
        "price_amount": float,
        "price_currency": str,
        "pay_amount": float,
        "actually_paid": float,
        "actually_paid_at_fiat": float,
        "order_id": str,
        "order_description": str,
        "purchase_id": str,
        "created_at": str,
        "updated_at": str,
        "outcome_amount": float,
        "outcome_currency": str,
    }
    """
    client = NOWPaymentsClient()

    # Verify IPN signature
    if not client.verify_ipn(ipn_data, headers):
        logger.warning(f"IPN verification failed for payment #{ipn_data.get('payment_id')}")
        return False

    order_id = ipn_data.get("order_id", "")
    payment_status = ipn_data.get("payment_status", "")
    actually_paid = float(ipn_data.get("actually_paid_at_fiat", 0))
    payment_id = ipn_data.get("payment_id")
    tx_hash = ipn_data.get("purchase_id", f"nowpayments-{payment_id}")

    if not order_id:
        logger.error("IPN: Missing order_id in callback")
        return False

    logger.info(
        f"IPN: Payment #{payment_id} for order {order_id} — "
        f"{payment_status} — ${actually_paid:.2f}"
    )

    # Record payment in our system
    try:
        from services.fulfillment import ServiceFulfillment

        ServiceFulfillment()

        # Record the payment
        from payments import record_payment
        record_payment(
            order_id=order_id,
            currency=ipn_data.get("pay_currency", "USDT"),
            amount_usd=actually_paid or float(ipn_data.get("price_amount", 0)),
            tx_hash=tx_hash,
            customer_email="",  # Will be filled by fulfillment from order data
            payment_code="NOWPAYMENTS_IPN",
            client_ip="nowpayments.io",
        )

        logger.info(f"IPN: Payment recorded for order {order_id}, delivery triggered")
        return True

    except Exception as e:
        logger.error(f"IPN: Failed to process payment for {order_id}: {e}")
        return False


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
            # Payment confirmed — trigger delivery
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
