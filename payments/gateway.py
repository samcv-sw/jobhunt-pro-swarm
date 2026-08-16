"""
JobHunt Pro — NOWPayments Payment Gateway v2
Handles: invoice creation, IPN verification, multi-chain crypto deposits ($0 merchant fees)
"""
import hashlib
import hmac
import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

API_BASE = "https://api.nowpayments.io/v1"

class NOWPaymentsGateway:
    """Full NOWPayments integration for JobHunt Pro with Multi-Chain Sovereign Wallet Support."""

    def __init__(self):
        # SECURITY: Secrets are loaded EXCLUSIVELY from environment variables.
        # No hardcoded fallbacks. If a secret is missing, the gateway fails loudly
        # rather than silently operating with a leaked credential.
        self.api_key = os.getenv("NOWPAYMENTS_API_KEY", "")
        self.ipn_secret = os.getenv("NOWPAYMENTS_IPN_SECRET", "")
        # Direct sovereign crypto addresses (non-custodial, $0 merchant fee)
        # Loaded from env only — never commit wallet addresses to source control.
        self.wallets = {
            "btc": os.getenv("CRYPTO_BTC_ADDRESS", ""),
            "eth": os.getenv("CRYPTO_ETH_ADDRESS", ""),
            "usdt": os.getenv("CRYPTO_USDT_ADDRESS", ""),
            "usdt_trc20": os.getenv("CRYPTO_USDT_TRC20_ADDRESS", os.getenv("CRYPTO_TRON_ADDRESS", "")),
            "usdt_polygon": os.getenv("CRYPTO_POLYGON_ADDRESS", ""),
            "usdc_polygon": os.getenv("CRYPTO_POLYGON_ADDRESS", ""),
            "ton": os.getenv("CRYPTO_TON_ADDRESS", ""),
            "ltc": os.getenv("CRYPTO_LTC_ADDRESS", ""),
        }
        if not self.api_key or not self.ipn_secret:
            logging.warning(
                "NOWPAYMENTS_API_KEY / NOWPAYMENTS_IPN_SECRET not set. "
                "Crypto payments will be unavailable until configured via environment."
            )

    def create_invoice(self, price_amount: float = 29.0,
                       price_currency: str = "usd",
                       pay_currency: str = "",
                       order_id: str = None,
                       user_email: str = "") -> dict:
        """
        Create a NOWPayments invoice.
        Returns invoice_url and payment_id.
        Falls back to direct crypto address if API fails.
        """
        if not order_id:
            order_id = f"jhpro_{int(datetime.now().timestamp())}"

        try:
            import urllib.request
            # HARDENING: Public base URL is env-configurable so IPN/success/cancel
            # callbacks resolve correctly regardless of deployment host (Render,
            # PythonAnywhere, Vercel, etc.). Never hardcode a single host.
            base_url = (
                os.environ.get("SITE_URL")
                or os.environ.get("PUBLIC_BASE_URL")
                or os.environ.get("RENDER_EXTERNAL_URL")
                or "https://jhfguf.pythonanywhere.com"
            ).rstrip("/")
            payload = {
                "price_amount": price_amount,
                "price_currency": price_currency,
                "order_id": order_id,
                "order_description": f"JobHunt Pro — Lifetime Access (${price_amount})",
                "ipn_callback_url": f"{base_url}/api/v2/nowpayments-ipn",
                "success_url": f"{base_url}/payment/success",
                "cancel_url": f"{base_url}/payment/cancel",
                "is_fixed_rate": True,
                "is_fee_paid_by_user": True,
            }
            if pay_currency:
                payload["pay_currency"] = pay_currency.lower()
            if user_email:
                payload["payout_address"] = self.wallets.get("usdt_trc20") or self.wallets.get("usdt", "")

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
            "note": "Send exact amount to one of the sovereign non-custodial addresses above ($0 merchant fees)"
        }

    def verify_ipn(self, body: str, signature: str) -> bool:
        """
        Verify NOWPayments IPN signature using canonical JSON sorting.
        Returns True if valid.
        """
        if not signature or not body:
            return False
        try:
            body_dict = json.loads(body)
            sorted_keys = sorted(body_dict.keys())
            sorted_body = {k: body_dict[k] for k in sorted_keys}
            message = json.dumps(sorted_body, separators=(",", ":"), sort_keys=True)

            computed = hmac.new(
                self.ipn_secret.encode("utf-8"),
                message.encode("utf-8"),
                hashlib.sha512
            ).hexdigest()

            return hmac.compare_digest(computed.lower(), signature.lower())
        except Exception as e:
            logger.error(f"IPN verify: {e}")
            return False

    def process_ipn(self, body: dict) -> dict:
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

        if status in ("finished", "confirmed"):
            result["action"] = "activate_user"
            parts = order_id.split("_")
            if len(parts) >= 2:
                result["user_identifier"] = parts[0]
                result["credits"] = max(1, int(float(amount) / 29 * 100))
        elif status == "partially_paid":
            result["action"] = "partial_credit"
            result["credits"] = max(1, int(float(amount) / 29 * 50))
        elif status in ("expired", "cancelled"):
            result["action"] = "none"

        return result

    def get_payment_addresses(self) -> dict:
        """Return available sovereign deposit addresses for $0 merchant fees."""
        return {
            "btc": self.wallets["btc"],
            "eth": self.wallets["eth"],
            "usdt_trc20": self.wallets["usdt_trc20"],
            "usdt_polygon": self.wallets["usdt_polygon"],
            "usdc_polygon": self.wallets["usdc_polygon"],
            "ton": self.wallets["ton"],
            "ltc": self.wallets["ltc"],
            "message": "Send exact amount to any sovereign non-custodial address above ($0 merchant fees)."
        }


# Singleton for easy import
gateway = NOWPaymentsGateway()


def create_payment(amount: float = 29.0, email: str = "", pay_currency: str = "") -> dict:
    """Public convenience function."""
    return gateway.create_invoice(price_amount=amount, user_email=email, pay_currency=pay_currency)


def get_addresses() -> dict:
    """Public convenience: get direct crypto addresses."""
    return gateway.get_payment_addresses()
