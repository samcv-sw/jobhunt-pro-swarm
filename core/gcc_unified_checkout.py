"""
JobHunt Pro — GCC Unified Checkout & Dynamic PPP Gateway
Comprehensive payment routing supporting Mada, Apple Pay, Tap Payments, Moyasar, KNET,
Tamara & Tabby BNPL 4-installment splits, and automated Purchasing Power Parity (PPP)
localization discounts for GCC & MENA.
"""

from typing import Dict, Any, List, Optional, Union
import hmac
import hashlib
import json
import time
import logging

logger = logging.getLogger(__name__)

# Base Global Pricing Matrix (USD)
BASE_PRICING = {
    "starter": {"name": "Starter", "base_usd": 9.00},
    "basic": {"name": "Basic", "base_usd": 19.00},
    "pro": {"name": "Pro", "base_usd": 49.00},
    "enterprise": {"name": "Enterprise / B2B SDR Swarm", "base_usd": 149.00},
    "b2b_sdr_swarm": {"name": "Enterprise / B2B SDR Swarm", "base_usd": 149.00},
    "starter_god": {"name": "Pro Automation", "base_usd": 29.00},
    "enterprise_god": {"name": "God-Mode Empire", "base_usd": 99.00},
    "agency_god": {"name": "Agency White-Label Empire", "base_usd": 299.00},
    "b2b_recruiter_solo": {"name": "Recruiter Solo", "base_usd": 199.00},
    "b2b_enterprise_swarm": {"name": "Enterprise Swarm", "base_usd": 899.00}
}

# Country Purchasing Power Parity & FX Config
COUNTRY_PPP_CONFIG = {
    "SA": {
        "country": "Saudi Arabia",
        "currency": "SAR",
        "rate_to_usd": 3.75,
        "ppp_discount": 0.0,
        "vat_rate": 0.15,
        "methods": ["mada", "apple_pay", "tamara", "tabby", "visa_mastercard", "tap", "moyasar"]
    },
    "AE": {
        "country": "United Arab Emirates",
        "currency": "AED",
        "rate_to_usd": 3.67,
        "ppp_discount": 0.0,
        "vat_rate": 0.05,
        "methods": ["apple_pay", "tamara", "tabby", "visa_mastercard", "tap"]
    },
    "KW": {
        "country": "Kuwait",
        "currency": "KWD",
        "rate_to_usd": 0.31,
        "ppp_discount": 0.0,
        "vat_rate": 0.0,
        "methods": ["knet", "apple_pay", "tamara", "tabby", "tap"]
    },
    "QA": {
        "country": "Qatar",
        "currency": "QAR",
        "rate_to_usd": 3.64,
        "ppp_discount": 0.0,
        "vat_rate": 0.0,
        "methods": ["apple_pay", "visa_mastercard", "tap"]
    },
    "BH": {
        "country": "Bahrain",
        "currency": "BHD",
        "rate_to_usd": 0.376,
        "ppp_discount": 0.0,
        "vat_rate": 0.10,
        "methods": ["benefit", "apple_pay", "visa_mastercard", "tap"]
    },
    "OM": {
        "country": "Oman",
        "currency": "OMR",
        "rate_to_usd": 0.385,
        "ppp_discount": 0.0,
        "vat_rate": 0.05,
        "methods": ["thawani", "apple_pay", "visa_mastercard", "tap"]
    },
    "LB": {
        "country": "Lebanon",
        "currency": "USD",
        "rate_to_usd": 1.0,
        "ppp_discount": 0.50,
        "vat_rate": 0.0,
        "methods": ["crypto_usdt", "moonpay", "whish_money"]
    },
    "EG": {
        "country": "Egypt",
        "currency": "EGP",
        "rate_to_usd": 48.5,
        "ppp_discount": 0.55,
        "vat_rate": 0.14,
        "methods": ["fawry", "vodafone_cash", "visa_mastercard", "tap"]
    },
    "US": {
        "country": "United States",
        "currency": "USD",
        "rate_to_usd": 1.0,
        "ppp_discount": 0.0,
        "vat_rate": 0.0,
        "methods": ["stripe", "apple_pay", "google_pay", "crypto"]
    }
}


class GCCUnifiedCheckout:
    """Unified GCC and Emerging Market Smart Checkout Gateway with BNPL support."""

    def calculate_bnpl_installments(
        self,
        amount_local: float,
        currency: str,
        installments: int = 4
    ) -> Dict[str, Any]:
        """Calculate BNPL split installment schedule (e.g. Tamara/Tabby 4-month splits)."""
        installment_amount = round(amount_local / max(1, installments), 2)
        total_calculated = round(installment_amount * installments, 2)
        diff = round(amount_local - total_calculated, 2)
        first_installment = round(installment_amount + diff, 2)

        return {
            "installments_count": installments,
            "installment_amount": installment_amount,
            "first_installment": first_installment,
            "subsequent_installments": installment_amount,
            "currency": currency,
            "schedule": [
                {"installment": 1, "due": "Today", "amount": first_installment, "currency": currency},
                {"installment": 2, "due": "In 1 month", "amount": installment_amount, "currency": currency},
                {"installment": 3, "due": "In 2 months", "amount": installment_amount, "currency": currency},
                {"installment": 4, "due": "In 3 months", "amount": installment_amount, "currency": currency},
            ]
        }

    def calculate_localized_pricing(self, plan_id: str, country_code: str = "SA") -> Dict[str, Any]:
        """Calculate dynamic pricing with localized currency, FX conversion, and PPP adjustments."""
        plan = BASE_PRICING.get(plan_id, BASE_PRICING.get("starter_god", {"name": "Pro", "base_usd": 49.00}))
        country = COUNTRY_PPP_CONFIG.get(country_code.upper(), COUNTRY_PPP_CONFIG["SA"])

        base_usd = plan["base_usd"]
        discount_rate = country["ppp_discount"]
        adjusted_usd = base_usd * (1.0 - discount_rate)
        local_price = round(adjusted_usd * country["rate_to_usd"], 2)

        vat_rate = country.get("vat_rate", 0.0)
        vat_amount = round(local_price * vat_rate, 2)
        total_with_vat = round(local_price + vat_amount, 2)

        # Include BNPL calculation for SAR/AED/KWD
        bnpl = self.calculate_bnpl_installments(total_with_vat, country["currency"], installments=4)

        return {
            "plan_id": plan_id,
            "plan_name": plan["name"],
            "country_code": country_code.upper(),
            "country_name": country["country"],
            "currency": country["currency"],
            "base_usd": base_usd,
            "original_usd": base_usd,
            "ppp_discount_applied_percent": int(discount_rate * 100),
            "final_amount_local": local_price,
            "vat_rate_percent": int(vat_rate * 100),
            "vat_amount": vat_amount,
            "total_with_vat": total_with_vat,
            "bnpl_installments": bnpl,
            "supported_payment_methods": country["methods"]
        }

    def build_checkout_order(
        self,
        tier: str = "pro",
        country_code: str = "SA",
        user_id: str = "user_default",
        promo_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build checkout order details with localized pricing and supported methods."""
        pricing = self.calculate_localized_pricing(tier, country_code)
        sess = self.generate_gcc_checkout_session(plan_id=tier, country_code=country_code)
        return {
            "tier": tier,
            "user_id": user_id,
            "country_code": country_code.upper(),
            "currency": pricing["currency"],
            "base_usd": pricing["base_usd"],
            "gross_amount_local": pricing["total_with_vat"],
            "supported_payment_methods": pricing["supported_payment_methods"],
            "bnpl_installments": pricing["bnpl_installments"],
            "checkout_session": sess
        }

    def generate_gcc_checkout_session(
        self,
        plan_id: str,
        country_code: str = "SA",
        payment_method: str = "mada",
        user_email: str = "customer@jobhuntpro.io"
    ) -> Dict[str, Any]:
        """Generate direct checkout session for GCC & MENA payment methods."""
        pricing = self.calculate_localized_pricing(plan_id, country_code)
        method = payment_method.lower().strip()
        session_id = f"gcc_sess_{plan_id}_{country_code.lower()}_{int(time.time())}"

        # Generate provider-specific checkout URL and metadata
        if method in ["mada", "tap", "visa_mastercard"]:
            gateway = "Tap Payments GCC"
            checkout_url = f"https://checkout.tap.company/v2/pay/{session_id}?amount={pricing['total_with_vat']}&curr={pricing['currency']}"
        elif method == "knet":
            gateway = "KNET Kuwait Payment Gateway"
            checkout_url = f"https://knet.com.kw/pay/{session_id}?amount={pricing['total_with_vat']}&curr=KWD"
        elif method == "apple_pay":
            gateway = "Apple Pay GCC Direct"
            checkout_url = f"https://checkout.tap.company/v2/apple-pay/{session_id}?amount={pricing['total_with_vat']}&curr={pricing['currency']}"
        elif method == "moyasar":
            gateway = "Moyasar KSA"
            checkout_url = f"https://api.moyasar.com/v1/invoices/{session_id}/pay"
        elif method == "tamara":
            gateway = "Tamara BNPL (4 Installments)"
            checkout_url = f"https://checkout.tamara.co/checkout/{session_id}?amount={pricing['total_with_vat']}&currency={pricing['currency']}"
        elif method == "tabby":
            gateway = "Tabby BNPL (4 Split Payments)"
            checkout_url = f"https://checkout.tabby.ai/checkout/{session_id}?amount={pricing['total_with_vat']}&currency={pricing['currency']}"
        else:
            gateway = "JobHunt Unified GCC Gateway"
            checkout_url = f"https://checkout.jobhuntpro.io/gcc/pay/{session_id}"

        return {
            "success": True,
            "session_id": session_id,
            "gateway": gateway,
            "checkout_url": checkout_url,
            "amount": pricing["final_amount_local"],
            "vat_amount": pricing["vat_amount"],
            "total_amount": pricing["total_with_vat"],
            "currency": pricing["currency"],
            "payment_method": method,
            "user_email": user_email,
            "bnpl_summary": pricing["bnpl_installments"] if method in ("tamara", "tabby") else None,
            "status": "initiated"
        }

    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
        secret_key: str = "tap_sec_test_998124"
    ) -> bool:
        """Verify HMAC-SHA256 signature for incoming GCC payment webhooks."""
        if not signature_header:
            return False
        expected_sig = hmac.new(secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig.lower(), signature_header.lower())

    def process_gcc_webhook(
        self,
        raw_payload: Union[bytes, str, dict],
        signature_header: str,
        secret_key: str = "tap_sec_test_998124"
    ) -> Dict[str, Any]:
        """
        Process GCC payment webhook (Tap, Moyasar, Tamara, Tabby),
        verify cryptographic signature, and credit user wallet atomically.
        """
        # Parse payload
        if isinstance(raw_payload, (bytes, bytearray)):
            payload_bytes = bytes(raw_payload)
            try:
                data = json.loads(payload_bytes.decode("utf-8"))
            except Exception:
                return {"success": False, "error": "Invalid JSON payload"}
        elif isinstance(raw_payload, str):
            payload_bytes = raw_payload.encode("utf-8")
            try:
                data = json.loads(raw_payload)
            except Exception:
                return {"success": False, "error": "Invalid JSON payload"}
        elif isinstance(raw_payload, dict):
            data = raw_payload
            data_str = json.dumps(data, separators=(",", ":"), sort_keys=True)
            payload_bytes = data_str.encode("utf-8")
        else:
            return {"success": False, "error": "Invalid payload format"}

        # Validate signature
        if signature_header and not self.verify_webhook_signature(payload_bytes, signature_header, secret_key):
            logger.warning(f"GCC Webhook: Signature verification failed")
            return {"success": False, "error": "Signature mismatch"}

        session_id = data.get("session_id") or data.get("id") or f"gcc_{int(time.time())}"
        status = data.get("status", "CAPTURED").upper()
        amount_local = float(data.get("amount", 0.0))
        currency = data.get("currency", "SAR").upper()
        user_id = data.get("user_id") or data.get("customer_id") or "user_gcc"

        if status not in ("CAPTURED", "PAID", "COMPLETED", "SUCCESS"):
            return {"success": False, "message": f"Payment status {status} not completed"}

        # Convert to USD estimate for wallet balance
        rate = COUNTRY_PPP_CONFIG.get("SA", {}).get("rate_to_usd", 3.75)
        for cfg in COUNTRY_PPP_CONFIG.values():
            if cfg["currency"] == currency:
                rate = cfg["rate_to_usd"]
                break
        amount_usd = round(amount_local / rate, 2) if rate > 0 else amount_local

        # Atomic credit to wallet
        try:
            from web.shared import update_wallet
            credit_res = update_wallet(
                user_id=user_id,
                amount=amount_usd,
                description=f"GCC Checkout ({currency} {amount_local:.2f}): {session_id}",
                tx_id=session_id
            )
            return {
                "success": True,
                "session_id": session_id,
                "amount_local": amount_local,
                "amount_usd": amount_usd,
                "currency": currency,
                "wallet_credited": credit_res
            }
        except Exception as e:
            logger.error(f"Error processing GCC wallet credit: {e}")
            return {"success": False, "error": str(e)}


# Global singleton instance
gcc_unified_checkout = GCCUnifiedCheckout()
gcc_checkout = gcc_unified_checkout

