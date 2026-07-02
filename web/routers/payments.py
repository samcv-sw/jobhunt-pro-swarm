from core.pg_sqlite_shim import get_db
import os
import logging
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse


from core.pricing_manager import PRICING_TIERS
PRICING_TIERS_MAP = {t['companies']: t for t in PRICING_TIERS}
from core.pricing_manager import BOUQUET_PACKAGES
BOUQUET_PACKAGES_MAP = {b['bouquet']: b for b in BOUQUET_PACKAGES}
from payments import get_payment_addresses
from services.fulfillment import ServiceFulfillment

router = APIRouter()
logger = logging.getLogger(__name__)

fulfillment = ServiceFulfillment()

def get_verified_user_id(request: Request) -> str:
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    import config
    SECRET_KEY = os.getenv("SECRET_KEY") or getattr(config, "SECRET_KEY", None)
    if not SECRET_KEY:
        return None
    session_serializer = URLSafeTimedSerializer(SECRET_KEY)
    cookie = request.cookies.get("user_id", "")
    if cookie:
        try:
            return session_serializer.loads(cookie, max_age=86400 * 30)
        except (BadSignature, SignatureExpired):
            pass
    try:
        session_user = request.session.get("user")
        if session_user and session_user.get("id"):
            return session_user["id"]
    except Exception:
        pass
    return None

@router.get("/checkout", include_in_schema=False)
def checkout_redirect():
    return RedirectResponse(url="/pricing")

@router.get("/checkout/{order_id}", response_class=HTMLResponse)
def checkout_page(request: Request, order_id: str):
    from web.app_v2 import templates, config # safe local import for templates
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ?", (order_id, user_id)).fetchone()
    if not order:
        conn.close()
        return RedirectResponse("/wallet", status_code=303)

    user_row = conn.execute("SELECT name, email FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    if order["payment_status"] == "completed":
        return RedirectResponse("/wallet?success=redeemed", status_code=303)

    user_name = "Candidate"
    user_email = ""
    if user_row:
        user_name = user_row["name"] or "Candidate"
        user_email = user_row["email"] or ""

    currency = order["payment_method"]
    addr = order["pay_address"] if order["pay_address"] else ""
    if not addr:
        addresses = get_payment_addresses()
        addr = addresses.get(currency, "")
    if not addr:
        addr = "0xSimulatedTrc20UsdtAddressForAutomatedJobHuntPayments"

    payment_code = order["payment_code"] if "payment_code" in dict(order) else ""
    if not payment_code:
        payment_code = order_id[-8:].upper()

    order_dict = {
        "order_id": order["order_id"],
        "status": order["payment_status"],
        "item_type": order["order_type"],
        "price": order["amount_usd"],
        "total_price": order["amount_usd"],
        "service_name": "Wallet Topup" if order["package_name"] == "wallet_topup" else order["package_name"],
        "customer_name": user_name,
        "customer_email": user_email,
        "payment_code": payment_code,
        "crypto_addresses": {currency: addr} if addr else get_payment_addresses(),
    }

    return templates.TemplateResponse(request, "checkout_v3.html", {
        "order": order_dict,
        "address": addr,
        "currency": currency,
        "VERSION": config.VERSION
    })

@router.get("/checkout/v2/{order_id}", response_class=HTMLResponse)
def checkout_v2_page(request: Request, order_id: str):
    """Checkout page for a new service order."""
    from web.app_v2 import templates # safe local import for templates
    order = fulfillment.get_order(order_id)
    if not order:
        return HTMLResponse("Order not found", status_code=404)
    return templates.TemplateResponse(request, "checkout_v2.html", {
        "order": order,
    })
