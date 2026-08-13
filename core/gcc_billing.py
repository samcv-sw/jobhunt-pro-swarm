"""
GCC Multi-Currency & Dual Language Tax Invoicing Engine
Supports USD, AED (د.إ), SAR (ر.س), KWD (د.ك) with dual Arabic/English rendering.
"""

import time
from typing import Dict, Any, List

class GCCBillingService:
    RATES_TO_USD = {
        "USD": 1.0,
        "AED": 3.6725,
        "SAR": 3.75,
        "KWD": 0.307
    }

    CURRENCY_SYMBOLS = {
        "USD": "$",
        "AED": "د.إ",
        "SAR": "ر.س",
        "KWD": "د.ك"
    }

    def convert_price(self, amount_usd: float, target_currency: str = "AED") -> Dict[str, Any]:
        """
        Converts USD amount to target GCC currency with localized symbols.
        """
        curr = target_currency.upper()
        rate = self.RATES_TO_USD.get(curr, 1.0)
        converted_amount = round(amount_usd * rate, 2)
        symbol = self.CURRENCY_SYMBOLS.get(curr, curr)

        return {
            "amount_usd": amount_usd,
            "currency": curr,
            "rate": rate,
            "converted_amount": converted_amount,
            "formatted_price": f"{converted_amount} {symbol}"
        }

    def generate_tax_invoice(self, client_name: str, client_vat_id: str, amount_usd: float, currency: str = "AED") -> Dict[str, Any]:
        """
        Generates structured dual-language (Arabic/English) B2B tax invoice data.
        """
        pricing = self.convert_price(amount_usd, currency)
        subtotal = pricing["converted_amount"]
        vat_rate = 0.05 if currency in ["AED", "SAR"] else 0.0  # 5% GCC standard VAT
        vat_amount = round(subtotal * vat_rate, 2)
        total_amount = round(subtotal + vat_amount, 2)
        invoice_num = f"INV-GCC-{int(time.time())}"

        return {
            "invoice_number": invoice_num,
            "date": time.strftime("%Y-%m-%d"),
            "client_name": client_name,
            "client_vat_id": client_vat_id or "N/A",
            "currency": pricing["currency"],
            "currency_symbol": self.CURRENCY_SYMBOLS.get(pricing["currency"], pricing["currency"]),
            "subtotal": subtotal,
            "vat_rate_percent": int(vat_rate * 100),
            "vat_amount": vat_amount,
            "total_amount": total_amount,
            "formatted_total": f"{total_amount} {self.CURRENCY_SYMBOLS.get(pricing['currency'], pricing['currency'])}",
            "company_name_en": "JobHunt Pro Enterprise FZ-LLC",
            "company_name_ar": "جوب هانت برو إنتربرايز ش.ذ.م.م",
            "tax_registration_num": "TRN-100482910300003"
        }

gcc_billing_service = GCCBillingService()
