"""
JobHunt Pro — NOWPayments Payment Gateway v2
Handles: invoice creation, IPN verification, crypto deposits
"""
import hashlib
import hmac
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict

logger = logging.getLogger(__name__)

API_BASE = "https://api.nowpayments.io/v1"

class NOWPaymentsGateway:
    """Full NOWPayments integration for JobHunt Pro."""

    def __init__(self):
        self.api_key = os.getenv("NOWPAYMENTS_API_KEY", "VA1FDVQ-JBJ41KM-QN6MVGF-TTR80X4")
        self.ipn_secret = os.getenv("NOWPAYMENTS_IPN_SECRET", "OE+zU1NbfNNlySwH3zrUthqQWZtGqrJa")
        # Fallback direct crypto addresses
        self.wallets = {
            "btc": os.getenv("CRYPTO_BTC_ADDRESS", "bc1q0e68d76d8dc303249a1992405ac2879f97fa8f"),
            "eth": os.getenv("CRYPTO_ETH_ADDRESS", "0x0e68d76d8dc303249a1992405ac2879f97fa8fec"),
            "usdt": os.getenv("CRYPTO_USDT_ADDRESS", "0xc303249a1992405ac2879f97fa8fec34c72be2f8"),
            "ltc": os.getenv("CRYPTO_LTC_ADDRESS", "ltc1q0e68d76d8dc303249a1992405ac2879f97fa8f"),
        }

    def create_invoice(self, price_amount: float = 29.0, 
                       price_currency: str = "usd",
                       order_id: str = None,
                       user_email: str = "") -> Dict:
        """
        Create a NOWPayments invoice.
        Returns invoice_url and payment_id.
        Falls back to direct crypto address if API fails.
        """
        if not order_id:
            order_id = f"jhpro_{int(datetime.now().timestamp())}"

        try:
            import urllib.request
            payload = {
                "price_amount": price_amount,
                "price_currency": price_currency,
                "order_id": order_id,
                "order_description": f"JobHunt Pro — Lifetime Access (${price_amount})",
                "ipn_callback_url": "https://olympus-webhook.samsalameh-cv.workers.dev/api/v1/webhook/nowpayments",
                "success_url": "https://jhfguf.pythonanywhere.com/payment/success",
                "cancel_url": "https://jhfguf.pythonanywhere.com/payment/cancel",
                "is_fixed_rate": True,
                "is_fee_paid_by_user": True,
            }
            if user_email:
                payload["payout_address"] = self.wallets.get("usdt", "")

            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{API_BASE}/invoice",
                data=data,
                headers={
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json"
                }
            )
            resp = urllib.request.urlopen(req, timeout=15)
            result = json.loads(resp.read())

            if result.get("invoice_url"):
                return {
                    "success": True,
                    "invoice_url": result["invoice_url"],
                    "payment_id": result.get("payment_id", ""),
                    "method": "nowpayments"
                }
        except Exception as e:
            logger.warning(f"NOWPayments invoice: {e}")

        # Fallback to direct deposit
        return {
            "success": True,
            "invoice_url": None,
            "method": "direct_crypto",
            "wallets": self.wallets,
            "note": "Send exact amount to one of the addresses above"
        }

    def verify_ipn(self, body: str, signature: str) -> bool:
        """
        Verify NOWPayments IPN signature.
        Returns True if valid.
        """
        if not signature or not body:
            return False
        try:
            body_dict = json.loads(body)
            sorted_keys = sorted(body_dict.keys())
            sorted_body = {k: body_dict[k] for k in sorted_keys}
            message = json.dumps(sorted_body, separators=(",", ":"))

            computed = hmac.new(
                self.ipn_secret.encode(),
                message.encode(),
                hashlib.sha512
            ).hexdigest()

            return hmac.compare_digest(computed, signature)
        except Exception as e:
            logger.error(f"IPN verify: {e}")
            return False

    def process_ipn(self, body: dict) -> Dict:
        """
        Process a verified IPN webhook.
        Returns action to take.
        """
        status = body.get("payment_status", "")
        order_id = body.get("order_id", "")
        payment_id = body.get("payment_id", "")
        amount = body.get("actually_paid", 0)
        currency = body.get("pay_currency", "usd")

        result = {
            "order_id": order_id,
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "action": "none"
        }

        if status == "finished":
            result["action"] = "activate_user"
            # Extract user info from order_id
            parts = order_id.split("_")
            if len(parts) >= 2:
                result["user_identifier"] = parts[0]
                result["credits"] = max(1, int(float(amount) / 29 * 100))
        elif status == "partially_paid":
            result["action"] = "partial_credit"
            result["credits"] = max(1, int(float(amount) / 29 * 50))
        elif status in ("expired", "cancelled"):
            result["action"] = "none"  # Order expired, no action

        return result

    def get_payment_addresses(self) -> Dict:
        """Return available deposit addresses (fallback when NOWPayments down)."""
        return {
            "btc": self.wallets["btc"],
            "eth": self.wallets["eth"],
            "usdt_erc20": self.wallets["usdt"],
            "ltc": self.wallets["ltc"],
            "message": "Send exact amount to any address above. Auto-crediting within 1-12 hours."
        }


# Singleton for easy import
gateway = NOWPaymentsGateway()


def create_payment(amount: float = 29.0, email: str = "") -> Dict:
    """Public convenience function."""
    return gateway.create_invoice(price_amount=amount, user_email=email)


def get_addresses() -> Dict:
    """Public convenience: get direct crypto addresses."""
    return gateway.get_payment_addresses()
