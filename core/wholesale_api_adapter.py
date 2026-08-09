"""
Wholesale Supplier API Integration Module — JobHunt Pro SaaS 2026

Connects your SaaS platform to wholesale digital product supplier APIs
(e.g., Kinguin API, G2A API, Z2U API, or any custom REST API supplier).

Flow:
1. Fetches live wholesale catalog & pricing.
2. Applies your custom Profit Margin Markup (e.g. +30% profit).
3. Provisions live credentials automatically from supplier API upon buyer payment.
"""

import urllib.request
import urllib.parse
import json
import logging
import os
import time

logger = logging.getLogger(__name__)

# Default Configuration (Can be overridden via environment or config.py)
DEFAULT_SUPPLIER_API_URL = os.getenv("WHOLESALE_API_URL", "https://api.kinguin.net/v1")
DEFAULT_SUPPLIER_API_KEY = os.getenv("WHOLESALE_API_KEY", "")
PROFIT_MARGIN_MULTIPLIER = float(os.getenv("WHOLESALE_PROFIT_MARGIN", "1.25")) # 25% profit margin default


class WholesaleSupplierAPIAdapter:
    """
    Adapter for connecting to wholesale digital account & subscription providers.
    Supports catalog synchronization, profit margin calculation, and instant ordering.
    """

    def __init__(self, api_url: str = None, api_key: str = None, profit_margin: float = None):
        self.api_url = (api_url or DEFAULT_SUPPLIER_API_URL).rstrip('/')
        self.api_key = api_key or DEFAULT_SUPPLIER_API_KEY
        self.profit_margin = profit_margin or PROFIT_MARGIN_MULTIPLIER

    def _http_request(self, endpoint: str, method: str = "GET", payload: dict = None):
        """Helper for making authenticated HTTP requests to supplier APIs."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        headers = {
            "User-Agent": "JobHuntPro-SaaS-Reseller/2.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
            headers["Authorization"] = f"Bearer {self.api_key}"

        data_bytes = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_body = resp.read().decode("utf-8")
                return json.loads(res_body) if res_body else {}
        except Exception as exc:
            logger.warning(f"Supplier API request error to {url}: {exc}")
            return None

    def fetch_live_catalog(self):
        """
        Fetches live products from supplier API and calculates retail prices with your profit margin.
        Returns a list of formatted offers ready for external_offers.json.
        """
        if not self.api_key:
            logger.info("Wholesale API Key not configured yet. Returning ready-to-connect API adapter schema.")
            return {
                "status": "ready_for_key",
                "message": "المحول جاهز للربط عبر API Key بمجرد تزويده بمفتاح المورد الخاص بك.",
                "profit_margin_applied": f"{(self.profit_margin - 1) * 100:.0f}% Profit"
            }

        data = self._http_request("products", method="GET")
        if not data or "products" not in data:
            return None

        formatted_offers = []
        for item in data.get("products", []):
            wholesale_cost = float(item.get("price", 10.0))
            retail_price = round(wholesale_cost * self.profit_margin, 2)
            profit_per_sale = round(retail_price - wholesale_cost, 2)

            formatted_offers.append({
                "id": str(item.get("id")),
                "title": item.get("name"),
                "title_ar": item.get("name_ar", item.get("name")),
                "wholesale_cost": wholesale_cost,
                "price": retail_price,
                "profit_margin": profit_per_sale,
                "supplier_name": item.get("supplier_name", "Connected Wholesale API"),
                "supplier_url": self.api_url,
                "in_stock": item.get("qty", 0) > 0
            })

        return formatted_offers

    def order_live_account(self, product_id: str, buyer_email: str = None):
        """
        Calls supplier API to purchase real credentials in real-time upon buyer payment on your site.
        Returns delivered credentials dict.
        """
        if not self.api_key:
            logger.info(f"Demo mode order for product {product_id}. API Key required for real supplier purchasing.")
            rand_id = int(time.time()) % 10000
            return {
                "success": True,
                "is_demo": True,
                "credentials": f"👑 [G2A Wholesale B2B API] | Email: {buyer_email or 'pro_subscriber_' + str(rand_id) + '@gmail.com'} | Pass: Pass#2026-{rand_id} | LicenseKey: G2A-B2B-{rand_id}-2026-VIP",
                "message": "يرجى إضافة WHOLESALE_API_KEY لشراء وتوليد الحسابات المباشرة من سيرفر المورد تلقائياً."
            }

        # Real Supplier Order Request
        order_payload = {
            "productId": product_id,
            "quantity": 1,
            "refId": f"SAAS-{int(time.time())}"
        }
        res = self._http_request("orders", method="POST", payload=order_payload)

        if res and res.get("status") in ["completed", "success", "paid"]:
            keys = res.get("keys", [])
            cred_str = keys[0].get("value") if keys else res.get("credential_text", "")
            return {
                "success": True,
                "is_demo": False,
                "credentials": cred_str or f"Order #{res.get('orderId')} Delivered Successfully",
                "order_id": res.get("orderId")
            }
        else:
            err_msg = res.get("message") if res else "لم يرجع سيرفر المورد استجابة صحيحة"
            return {
                "success": False,
                "message": f"خطأ من سيرفر المورد: {err_msg}"
            }


# Singleton instance ready for import across router files
wholesale_adapter = WholesaleSupplierAPIAdapter()
