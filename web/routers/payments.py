"""
routers/payments.py - Payments Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])

def _deps():
    from web.shared import get_db, get_verified_user_id, update_wallet, deduct_wallet, config
    from web.app_v2 import PRICING_TIERS, render_template, get_all_pricing
    return get_db, get_verified_user_id, update_wallet, deduct_wallet, config, PRICING_TIERS, render_template, get_all_pricing

@router.post("/api/generate-redeem-code")
async def api_generate_redeem_code(request: Request):
    """API endpoint for Telegram bot to sync redeem codes to PA DB."""
    session_user = request.session.get("user")
    admin_emails = ["samsalameh.cv@gmail.com"]
    if not session_user or session_user.get("email") not in admin_emails:
        return JSONResponse({"ok": False, "error": "Admin access required"}, status_code=403)
    try:
        body = await request.json()
        code = body.get("code", "")
        value = float(body.get("value", 0))
        code_type = body.get("code_type", "sale")
        if not code or value <= 0:
            return {"ok": False, "error": "Invalid code or value"}
        get_db, _, _, _, _, _, _, _ = _deps()
        conn = get_db()
        existing = conn.execute("SELECT id FROM redeem_codes WHERE code = ?", (code,)).fetchone()
        if existing:
            conn.close()
            return {"ok": False, "error": "Code already exists"}
        conn.execute("INSERT INTO redeem_codes (code, value_usd, code_type, is_used) VALUES (?, ?, ?, 0)",
                     (code, value, code_type))
        conn.commit()
        conn.close()
        return {"ok": True, "code": code, "value": value}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@router.post("/redeem")
def redeem_code(request: Request, code: str = Form(...)):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    conn = get_db()
    redeem = conn.execute("SELECT * FROM redeem_codes WHERE code = ? AND is_used = 0", (code,)).fetchone()

    if not redeem:
        conn.close()
        import urllib.parse
        return RedirectResponse(f"/wallet?error={urllib.parse.quote('Invalid or already used code. Please check and try again.')}", status_code=303)

    value = redeem["value_usd"]
    code_type = redeem["code_type"] if "code_type" in dict(redeem).keys() else "sale"
    conn.execute("UPDATE redeem_codes SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP WHERE code = ?",
                 (user_id, code))

    user_row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if not user_row:
        conn.close()
        return RedirectResponse("/login", status_code=303)
    user = dict(user_row)
    new_balance = user["wallet_balance"] + value
    conn.execute("UPDATE users SET wallet_balance = ? WHERE user_id = ?", (new_balance, user_id))

    if code_type == "admin_free":
        desc = f"Admin Free Credit — code: {code}"
        txn_type = "admin_free_credit"
    else:
        desc = f"Redeem code: {code}"
        txn_type = "redeem"

    conn.execute("""INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
                    VALUES (?, ?, ?, ?, ?)""",
                 (user_id, txn_type, value, new_balance, desc))

    conn.commit()
    conn.close()

    import urllib.parse
    if code_type == "admin_free":
        msg = f"Admin credit of ${value:.2f} added to your wallet!"
        return RedirectResponse(f"/wallet?success={urllib.parse.quote(msg)}", status_code=303)
    msg = f"Code redeemed! ${value:.2f} added to your wallet."
    return RedirectResponse(f"/wallet?success={urllib.parse.quote(msg)}", status_code=303)

@router.post("/wallet/deposit/create")
def wallet_deposit_create(request: Request, amount: float = Form(...), currency: str = Form("USDT")):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    if amount < 5:
        return RedirectResponse("/wallet?error=min_amount", status_code=303)
    if currency not in ("USDT", "BTC", "ETH", "LTC"):
        currency = "USDT"

    order_id = f"dep_{uuid.uuid4().hex[:16]}"

    np_address = ""
    np_invoice_url = ""
    np_pay_currency = currency
    np_pay_amount = 0
    np_id = 0
    try:
        from payments.nowpayments import create_crypto_invoice
        invoice = create_crypto_invoice(
            amount_usd=amount,
            order_id=order_id,
            service_name=f"Wallet Topup (${amount:.2f})"
        )
        if invoice:
            np_address = invoice.get("pay_address", "")
            np_invoice_url = invoice.get("invoice_url", "")
            np_pay_currency = invoice.get("pay_currency", currency)
            np_pay_amount = invoice.get("pay_amount", 0)
            np_id = invoice.get("nowpayments_id", 0)
    except Exception as e:
        logger.warning(f"NowPayments invoice failed (fallback to static): {e}")

    if not np_address:
        from payments import get_payment_addresses
        addrs = get_payment_addresses()
        np_address = addrs.get(currency, addrs.get("USDT", ""))

    conn = get_db()
    conn.execute("""INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status, pay_address, nowpayments_id, nowpayments_invoice_url, pay_currency, pay_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                 (order_id, user_id, "deposit", "wallet_topup", 0, amount, currency, "pending", np_address, np_id, np_invoice_url, np_pay_currency, np_pay_amount))
    conn.commit()
    conn.close()

    return RedirectResponse(f"/checkout/{order_id}", status_code=303)

@router.post("/checkout/{order_id}/pay-simulate")
def checkout_pay_simulate(request: Request, order_id: str):
    get_db, get_verified_user_id, update_wallet, _, _, _, _, _ = _deps()
    allow_simulate = os.getenv("ALLOW_PAY_SIMULATE", "false").lower() == "true"
    if not allow_simulate:
        return HTMLResponse("<h2>Simulate Payment Disabled</h2><p>This feature has been permanently disabled.</p>", status_code=403)

    admin_key = os.getenv("ADMIN_SECRET_KEY", "")
    provided_key = request.headers.get("X-Admin-Key", "") or request.query_params.get("key", "")
    if not admin_key or not provided_key or provided_key != admin_key:
        return HTMLResponse("<h2>Admin Authentication Required</h2>", status_code=403)

    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    conn = get_db()
    order = conn.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ? AND payment_status = 'pending'", (order_id, user_id)).fetchone()
    if not order:
        conn.close()
        return RedirectResponse("/wallet", status_code=303)

    amount = order["amount_usd"]
    conn.execute("UPDATE orders SET payment_status = 'completed' WHERE order_id = ?", (order_id,))
    update_wallet(conn, user_id, amount, f"Simulated Crypto Checkout: {order_id}", "deposit")
    conn.commit()
    conn.close()

    return RedirectResponse("/wallet?success=redeemed", status_code=303)

@router.get("/api/v1/order/status/{order_id}")
def api_order_status(order_id: str):
    get_db, _, _, _, _, _, _, _ = _deps()
    conn = get_db()
    order = conn.execute("SELECT payment_status FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    if not order:
        return {"status": "not_found"}
    return {"status": order["payment_status"]}

@router.post("/api/v1/payment/webhook")
async def payment_webhook(request: Request):
    get_db, _, update_wallet, _, _, _, _, _ = _deps()
    raw_body = await request.body()
    try:
        import json as _json
        payload = _json.loads(raw_body) if raw_body else {}
    except Exception:
        return JSONResponse({"status": "error", "message": "invalid_json"}, status_code=400)

    event = payload.get("event")
    data = payload.get("data", {})

    stripe_signature = request.headers.get("stripe-signature")
    if stripe_signature:
        import stripe
        from core.webhook_state import ProcessedWebhook
        from core.database import AsyncSessionLocal
        
        stripe_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not stripe_secret:
            logger.critical("Stripe webhook: STRIPE_WEBHOOK_SECRET not configured!")
            return JSONResponse({"status": "error", "message": "webhook_not_configured"}, status_code=500)
            
        try:
            stripe_event = stripe.Webhook.construct_event(
                payload=raw_body, sig_header=stripe_signature, secret=stripe_secret
            )
        except ValueError:
            return JSONResponse({"status": "error", "message": "invalid_payload"}, status_code=400)
        except Exception:
            return JSONResponse({"status": "error", "message": "invalid_signature"}, status_code=403)
            
        event_id = stripe_event.get("id")
        from sqlalchemy.dialects.postgresql import insert
        
        async with AsyncSessionLocal() as session:
            stmt = insert(ProcessedWebhook).values(event_id=event_id)
            stmt = stmt.on_conflict_do_update(
                index_elements=['event_id'],
                set_={'event_id': stmt.excluded.event_id}
            ).returning(ProcessedWebhook.event_id)
            result = await session.execute(stmt)
            await session.commit()
            
        if stripe_event["type"] == "checkout.session.completed":
            session_obj = stripe_event["data"]["object"]
            email = session_obj.get("customer_details", {}).get("email")
            amount = float(session_obj.get("amount_total", 0)) / 100.0
            
            if email and amount > 0:
                conn = get_db()
                user = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
                if user:
                    update_wallet(conn, user["user_id"], amount, f"Stripe Checkout: {event_id}", "deposit")
                    conn.commit()
                conn.close()
        return {"status": "success", "message": "stripe_processed"}

    if event == "order:paid" and data:
        sellix_secret = os.getenv("SELLIX_WEBHOOK_SECRET", "")
        if not sellix_secret:
            logger.critical("Sellix webhook secret not configured!")
            return JSONResponse({"status": "error", "message": "webhook_not_configured"}, status_code=500)

        sig = request.headers.get("x-sellix-signature", "") or request.headers.get("X-Sellix-Signature", "")
        if not sig:
            return JSONResponse({"status": "error", "message": "missing_signature"}, status_code=403)

        import hmac as _hmac
        import hashlib as _hashlib
        expected_sig = _hmac.new(sellix_secret.encode(), raw_body, _hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(sig, expected_sig):
            return JSONResponse({"status": "error", "message": "invalid_signature"}, status_code=403)

        email = data.get("customer_email") or data.get("email")
        amount = float(data.get("total", 0))
        if email and amount > 0:
            conn = get_db()
            user = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
            if user:
                update_wallet(conn, user["user_id"], amount, f"Automated Webhook Deposit: {data.get('uniqid')}", "deposit")
                conn.commit()
            conn.close()
            return {"status": "success", "message": "wallet_credited"}

    status = payload.get("status")
    merchant_order = payload.get("order_id")
    if status in ["paid", "paid_over"] and merchant_order:
        amount = float(payload.get("amount", 0))
        conn = get_db()
        order = conn.execute("SELECT user_id, payment_status FROM orders WHERE order_id = ? AND payment_status = 'pending'", (merchant_order,)).fetchone()
        if order:
            user_id = order["user_id"]
            conn.execute("UPDATE orders SET payment_status = 'completed' WHERE order_id = ?", (merchant_order,))
            update_wallet(conn, user_id, amount, f"Automated Cryptomus Webhook: {merchant_order}", "deposit")
            conn.commit()
        conn.close()
        return {"status": "success", "message": "cryptomus_credited"}

    return {"status": "ignored"}

@router.get("/api/v1/pricing")
def api_pricing():
    """Return all pricing data as JSON for frontend API calls."""
    get_db, _, _, _, _, _, _, get_all_pricing = _deps()
    return {
        "success": True,
        "data": get_all_pricing(),
        "currency": "USD",
        "payment_methods": ["btc", "eth", "usdt", "ltc"],
    }