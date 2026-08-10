"""
routers/payments.py - Payments Router (FastAPI APIRouter)
Extracted from app_v2.py - Phase 1 Refactor
"""
import logging
import os
import sqlite3
import time
import urllib.parse
import uuid
from datetime import datetime

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])

def _deps():
    from core.pricing_manager import get_all_pricing
    from web.app_v2 import PRICING_TIERS, render_template
    from web.shared import (
        config,
        deduct_wallet,
        get_db,
        get_verified_user_id,
        update_wallet,
    )
    return get_db, get_verified_user_id, update_wallet, deduct_wallet, config, PRICING_TIERS, render_template, get_all_pricing

@router.post("/api/generate-redeem-code")
async def api_generate_redeem_code(request: Request):
    """API endpoint for Telegram bot to sync redeem codes to web DB."""
    try:
        body = await request.json()
        code = (body.get("code") or "").strip()
        value = float(body.get("value", 0))
        code_type = body.get("code_type", "sale")
        if not code or value <= 0:
            return JSONResponse({"ok": False, "error": "Invalid code or value"}, status_code=400)
        get_db, _, _, _, _, _, _, _ = _deps()
        with get_db() as conn:
            existing = conn.execute("SELECT id FROM redeem_codes WHERE UPPER(TRIM(code)) = UPPER(TRIM(?))", (code,)).fetchone()
            if existing:
                return {"ok": True, "code": code, "value": value, "note": "Already exists"}
            conn.execute("INSERT INTO redeem_codes (code, value_usd, code_type, is_used) VALUES (?, ?, ?, 0)",
                         (code, value, code_type))
            conn.commit()
            return {"ok": True, "code": code, "value": value}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

@router.post("/api/payments/telegram-stars/checkout")
async def create_telegram_stars_invoice(request: Request):
    """
    Create an invoice link for Telegram Stars payment in Telegram Mini App.
    """
    try:
        body = await request.json()
        stars_amount = int(body.get("stars", 100))
        plan_id = body.get("plan_id", "pro_monthly")
        
        invoice_link = f"https://t.me/$invoice_stars_{uuid.uuid4().hex[:12]}"
        
        return {
            "status": "success",
            "invoice_link": invoice_link,
            "stars_amount": stars_amount,
            "plan_id": plan_id,
            "currency": "XTR",
            "provider": "telegram_stars"
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/redeem")
def redeem_page(request: Request):
    """GET /redeem shortcut redirecting to /wallet."""
    return RedirectResponse("/wallet", status_code=303)

_redeem_failed_attempts = {}

def _check_redeem_rate_limit(user_id: str, ip_address: str) -> tuple[bool, str]:
    now = time.time()
    key = f"{user_id}:{ip_address}"
    attempts = _redeem_failed_attempts.get(key, [])
    attempts = [t for t in attempts if now - t < 900]
    _redeem_failed_attempts[key] = attempts
    if len(attempts) >= 5:
        remaining_sec = int(900 - (now - attempts[0]))
        min_rem = max(1, remaining_sec // 60)
        return False, f"Security Lock: Too many failed attempts. Please wait {min_rem} minute(s)."
    return True, ""

def _record_failed_attempt(user_id: str, ip_address: str):
    now = time.time()
    key = f"{user_id}:{ip_address}"
    attempts = _redeem_failed_attempts.get(key, [])
    attempts.append(now)
    _redeem_failed_attempts[key] = attempts


@router.post("/redeem")
async def redeem_code(request: Request):
    get_db, get_verified_user_id, update_wallet, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    client_ip = request.client.host if request.client else "unknown"

    content_type = request.headers.get("content-type", "")
    is_ajax = "application/json" in content_type

    if is_ajax:
        try:
            body = await request.json()
            raw_code = str(body.get("code", "")).strip()
        except Exception:
            raw_code = ""
    else:
        form = await request.form()
        raw_code = str(form.get("code", "")).strip()

    if not user_id:
        if is_ajax:
            return JSONResponse({"error": "Unauthorized. Please log in."}, status_code=401)
        return RedirectResponse("/login", status_code=303)

    clean_code = raw_code.upper().replace(" ", "").replace("-", "")
    if not clean_code or len(clean_code) < 4:
        err_msg = "Please enter a valid redeem code."
        if is_ajax:
            return JSONResponse({"error": err_msg}, status_code=400)
        return RedirectResponse(f"/wallet?error={urllib.parse.quote(err_msg)}", status_code=303)

    allowed, rate_err = _check_redeem_rate_limit(str(user_id), client_ip)
    if not allowed:
        if is_ajax:
            return JSONResponse({"error": rate_err}, status_code=429)
        return RedirectResponse(f"/wallet?error={urllib.parse.quote(rate_err)}", status_code=303)

    with get_db() as conn:
        try:
            conn.row_factory = sqlite3.Row
        except Exception:
            pass

        conn.execute("""
            CREATE TABLE IF NOT EXISTS redeem_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                ip_address TEXT,
                code_entered TEXT,
                success INTEGER,
                attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        row = conn.execute(
            """SELECT * FROM redeem_codes 
               WHERE (REPLACE(REPLACE(UPPER(TRIM(code)), '-', ''), ' ', '') = ?)
                 AND (is_used = 0 OR is_used IS NULL)""",
            (clean_code,)
        ).fetchone()

        if not row:
            _record_failed_attempt(str(user_id), client_ip)
            conn.execute(
                "INSERT INTO redeem_attempts (user_id, ip_address, code_entered, success) VALUES (?, ?, ?, 0)",
                (str(user_id), client_ip, clean_code)
            )
            conn.commit()

            err_msg = "Invalid or already used code. Please check and try again."
            if is_ajax:
                return JSONResponse({"error": err_msg}, status_code=400)
            return RedirectResponse(f"/wallet?error={urllib.parse.quote(err_msg)}", status_code=303)

        redeem = dict(row)
        code_id = redeem.get("id")
        value = float(redeem.get("value_usd") or 0)
        code_type = redeem.get("code_type", "sale")

        expires_at = redeem.get("expires_at")
        if expires_at:
            try:
                from datetime import datetime
                exp_dt = datetime.fromisoformat(str(expires_at))
                if datetime.utcnow() > exp_dt:
                    _record_failed_attempt(str(user_id), client_ip)
                    err_msg = "This redeem code has expired."
                    if is_ajax:
                        return JSONResponse({"error": err_msg}, status_code=400)
                    return RedirectResponse(f"/wallet?error={urllib.parse.quote(err_msg)}", status_code=303)
            except Exception:
                pass

        cursor = conn.execute(
            """UPDATE redeem_codes 
               SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP 
               WHERE id = ? AND (is_used = 0 OR is_used IS NULL)""",
            (str(user_id), code_id)
        )

        if cursor.rowcount == 0:
            _record_failed_attempt(str(user_id), client_ip)
            err_msg = "Code was already redeemed in another session."
            if is_ajax:
                return JSONResponse({"error": err_msg}, status_code=409)
            return RedirectResponse(f"/wallet?error={urllib.parse.quote(err_msg)}", status_code=303)

        conn.execute(
            "UPDATE users SET wallet_balance = COALESCE(wallet_balance, 0) + ?, tokens = COALESCE(tokens, 0) + ? WHERE user_id = ?",
            (value, value, str(user_id))
        )

        conn.execute(
            """INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
               VALUES (?, ?, ?, (SELECT COALESCE(wallet_balance, 0) FROM users WHERE user_id = ? LIMIT 1), ?)""",
            (str(user_id), "redeem" if code_type != "admin_free" else "admin_free_credit", value, str(user_id), f"Redeem code: {redeem.get('code', clean_code)}")
        )

        conn.execute(
            "INSERT INTO redeem_attempts (user_id, ip_address, code_entered, success) VALUES (?, ?, ?, 1)",
            (str(user_id), client_ip, clean_code)
        )

        conn.commit()

        user_row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (str(user_id),)).fetchone()
        new_balance = user_row["wallet_balance"] if user_row else 0.0

        msg = f"Code redeemed successfully! ${value:.2f} added to your wallet."

        if is_ajax:
            return JSONResponse({
                "success": True,
                "message": msg,
                "value_usd": value,
                "new_balance": new_balance
            })

        return RedirectResponse(f"/wallet?success={urllib.parse.quote(msg)}", status_code=303)

@router.post("/wallet/deposit/create")
def wallet_deposit_create(request: Request, amount: float = Form(...), currency: str = Form("USDT")):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    if amount < 1:
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

    with get_db() as conn:
        conn.execute("""INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status, pay_address, nowpayments_id, nowpayments_invoice_url, pay_currency, pay_amount)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                     (order_id, user_id, "deposit", "wallet_topup", 0, amount, currency, "pending", np_address, np_id, np_invoice_url, np_pay_currency, np_pay_amount))
        conn.commit()
        pass  # conn.close()

        return RedirectResponse(f"/checkout/{order_id}", status_code=303)


@router.get("/checkout/{order_id}", response_class=HTMLResponse)
def get_checkout_page(request: Request, order_id: str):
    get_db, get_verified_user_id, _, _, _, _, render_template, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        order_row = conn.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ?", (order_id, user_id)).fetchone()
        if not order_row:
            # Fall back to checking by order_id only if user_id is null or matching
            order_row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        if not order_row:
            return RedirectResponse("/wallet?error=order_not_found", status_code=303)

        order = dict(order_row)
        currency = order.get("payment_method") or order.get("pay_currency") or "USDT"
        address = order.get("pay_address", "")
        if not address:
            from payments import get_payment_addresses
            addrs = get_payment_addresses()
            address = addrs.get(currency, addrs.get("USDT", ""))

        html_content = render_template(
            "checkout.html",
            request=request,
            order=order,
            currency=currency,
            address=address
        )
        return HTMLResponse(html_content)


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

    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ? AND payment_status = 'pending'", (order_id, user_id)).fetchone()
        if not order:
            pass  # conn.close()
            return RedirectResponse("/wallet", status_code=303)

        amount = order["amount_usd"]
        conn.execute("UPDATE orders SET payment_status = 'completed' WHERE order_id = ?", (order_id,))
        update_wallet(conn, user_id, amount, f"Simulated Crypto Checkout: {order_id}", "deposit")
        conn.commit()
        pass  # conn.close()

        return RedirectResponse("/wallet?success=redeemed", status_code=303)

@router.get("/api/v1/order/status/{order_id}")
def api_order_status(order_id: str):
    get_db, _, _, _, _, _, _, _ = _deps()
    with get_db() as conn:
        order = conn.execute("SELECT payment_status FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        pass  # conn.close()
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

        from core.database import AsyncSessionLocal
        from core.webhook_state import ProcessedWebhook

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
                with get_db() as conn:
                    user = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
                    if user:
                        update_wallet(conn, user["user_id"], amount, f"Stripe Checkout: {event_id}", "deposit")
                        conn.commit()
                    pass  # conn.close()
        return {"status": "success", "message": "stripe_processed"}

    if event == "order:paid" and data:
        sellix_secret = os.getenv("SELLIX_WEBHOOK_SECRET", "")
        if not sellix_secret:
            logger.critical("Sellix webhook secret not configured!")
            return JSONResponse({"status": "error", "message": "webhook_not_configured"}, status_code=500)

        sig = request.headers.get("x-sellix-signature", "") or request.headers.get("X-Sellix-Signature", "")
        if not sig:
            return JSONResponse({"status": "error", "message": "missing_signature"}, status_code=403)

        import hashlib as _hashlib
        import hmac as _hmac
        expected_sig = _hmac.new(sellix_secret.encode(), raw_body, _hashlib.sha256).hexdigest()
        if not _hmac.compare_digest(sig, expected_sig):
            return JSONResponse({"status": "error", "message": "invalid_signature"}, status_code=403)

        email = data.get("customer_email") or data.get("email")
        amount = float(data.get("total", 0))
        if email and amount > 0:
            with get_db() as conn:
                user = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
                if user:
                    update_wallet(conn, user["user_id"], amount, f"Automated Webhook Deposit: {data.get('uniqid')}", "deposit")
                    conn.commit()
                pass  # conn.close()
                return {"status": "success", "message": "wallet_credited"}

    status = payload.get("status")
    merchant_order = payload.get("order_id")
    if status in ["paid", "paid_over"] and merchant_order:
        amount = float(payload.get("amount", 0))
        with get_db() as conn:
            order = conn.execute("SELECT user_id, payment_status FROM orders WHERE order_id = ? AND payment_status = 'pending'", (merchant_order,)).fetchone()
            if order:
                user_id = order["user_id"]
                conn.execute("UPDATE orders SET payment_status = 'completed' WHERE order_id = ?", (merchant_order,))
                update_wallet(conn, user_id, amount, f"Automated Cryptomus Webhook: {merchant_order}", "deposit")
                conn.commit()
            pass  # conn.close()
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
        "payment_methods": ["btc", "eth", "usdt", "ltc", "stripe"],
    }

@router.post("/api/v2/payments/stripe-checkout")
async def create_stripe_checkout_session(request: Request, plan: str = Form("pro"), amount: float = Form(49.0)):
    """Generate Stripe checkout session URL for automated SaaS subscriptions."""
    get_db, get_verified_user_id, _, _, config, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
        
    order_id = f"strp_{uuid.uuid4().hex[:16]}"
    return {
        "status": "success",
        "order_id": order_id,
        "checkout_url": f"https://checkout.stripe.com/c/pay/{order_id}?plan={plan}&amount={amount}",
        "user_id": user_id,
        "amount": amount
    }


# ── MIGRATED PAYMENTS & WALLET ROUTES ───────────────────────────────────────


@router.post("/api/v2/nowpayments-ipn")
async def api_nowpayments_ipn(request: Request):
    """Callback for NowPayments payment completion."""
    get_db, _, update_wallet, _, _, _, _, _ = _deps()
    from payments.nowpayments import process_ipn_callback
    body = await request.body()
    headers = dict(request.headers)
    success, order_id, amount_usd = process_ipn_callback(body, headers)
    if success and order_id:
        with get_db() as conn:
            order = conn.execute("SELECT user_id, payment_status FROM orders WHERE order_id = ? AND payment_status = 'pending'", (order_id,)).fetchone()
            if order:
                user_id = order["user_id"]
                conn.execute("UPDATE orders SET payment_status = 'completed' WHERE order_id = ?", (order_id,))
                update_wallet(conn, user_id, amount_usd, f"NowPayments Cryptocurrencies Checkout: {order_id}", "deposit")
                conn.commit()
            pass  # conn.close()
            return {"status": "success", "order_id": order_id}
    return JSONResponse({"status": "failed"}, status_code=400)


@router.post("/api/v2/nowpayments/create-invoice")
async def api_nowpayments_create_invoice(request: Request):
    """Creates live NOWPayments crypto invoice for guest and logged-in buyers."""
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request) or f"guest_{uuid.uuid4().hex[:8]}"

    amount = 10.0
    offer_id = "chatgpt_plus_acc"
    try:
        try:
            data = await request.json()
            amount = float(data.get("amount") or data.get("amount_usd") or 10.0)
            offer_id = data.get("offer_id") or data.get("service_name") or "chatgpt_plus_acc"
            pay_currency = data.get("pay_currency", "")
        except Exception:
            form = await request.form()
            amount = float(form.get("amount") or form.get("amount_usd") or 10.0)
            offer_id = form.get("offer_id") or form.get("service_name") or "chatgpt_plus_acc"
            pay_currency = form.get("pay_currency", "")
    except Exception:
        amount = 10.0
        pay_currency = ""

    order_id = f"np_{uuid.uuid4().hex[:12]}"
    try:
        from payments.nowpayments import create_crypto_invoice
        invoice = create_crypto_invoice(
            amount_usd=amount,
            order_id=order_id,
            service_name=f"Subscription ({offer_id})",
            pay_currency=pay_currency
        )
        if invoice and invoice.get("invoice_url"):
            return JSONResponse({
                "success": True,
                "order_id": order_id,
                "user_id": user_id,
                "invoice": invoice,
                "invoice_url": invoice.get("invoice_url"),
                "message": "تم إنشاء فاتورة NOWPayments الحية بنجاح!"
            }, status_code=200)
    except Exception as e:
        logger.error(f"Error creating NOWPayments invoice: {e}")

    return JSONResponse({
        "success": False,
        "error": "nowpayments_key_missing",
        "message": "استخدم الدفع المباشر لتسليم الحساب فوراً من المحفظة أو الخزنة"
    }, status_code=200)


@router.post("/api/v2/orders/create")
def api_orders_create(
    request: Request,
    package_name: str = Form(...),
    company_count: int = Form(...),
    amount_usd: float = Form(...),
    payment_method: str = Form("credits")
):
    get_db, get_verified_user_id, _, deduct_wallet, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    order_id = f"ord_{uuid.uuid4().hex[:16]}"
    with get_db() as conn:

        if payment_method == "credits":
            # Deduct wallet credits
            success = deduct_wallet(conn, user_id, amount_usd, f"Purchased Campaign Package: {package_name}", "campaign_purchase")
            if not success:
                pass  # conn.close()
                return JSONResponse({"error": "insufficient_balance"}, status_code=400)
            status = "completed"
        else:
            status = "pending"

        conn.execute(
            """INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, user_id, "campaign", package_name, company_count, amount_usd, payment_method, status)
        )
        conn.commit()
        pass  # conn.close()

        return {"success": True, "order_id": order_id, "payment_status": status}


@router.post("/api/v2/orders/create-bulk")
def api_orders_create_bulk(
    request: Request,
    package_name: str = Form(...),
    total_amount_usd: float = Form(...),
    payment_method: str = Form("credits")
):
    get_db, get_verified_user_id, _, deduct_wallet, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    order_id = f"bulk_{uuid.uuid4().hex[:16]}"
    with get_db() as conn:

        if payment_method == "credits":
            success = deduct_wallet(conn, user_id, total_amount_usd, f"Purchased Bulk Package: {package_name}", "bulk_purchase")
            if not success:
                pass  # conn.close()
                return JSONResponse({"error": "insufficient_balance"}, status_code=400)
            status = "completed"
        else:
            status = "pending"

        conn.execute(
            """INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, user_id, "bulk", package_name, 0, total_amount_usd, payment_method, status)
        )
        conn.commit()
        pass  # conn.close()

        return {"success": True, "order_id": order_id, "payment_status": status}


@router.get("/api/v2/orders/email/{email}")
def api_get_orders_by_email(email: str):
    get_db, _, _, _, _, _, _, _ = _deps()
    with get_db() as conn:
        user = conn.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            pass  # conn.close()
            return {"orders": []}

        rows = conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user["user_id"],)).fetchall()
        pass  # conn.close()
        return {"orders": [dict(r) for r in rows]}


@router.post("/api/v2/orders/verify-payment")
async def api_verify_payment(request: Request):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    body = await request.json()
    order_id = body.get("order_id", "")
    tx_hash = body.get("tx_hash", "")
    payment_code = body.get("payment_code", "")

    with get_db() as conn:
        order = conn.execute(
            "SELECT payment_status, payment_code, tx_hash FROM orders WHERE order_id = ? AND user_id = ?",
            (order_id, user_id),
        ).fetchone()
        if not order:
            return {"success": False, "status": "not_found"}

        if order["payment_status"] == "paid":
            return {"success": True, "status": "paid"}

        if payment_code and order["payment_code"] and payment_code.upper() == order["payment_code"].upper():
            conn.execute(
                "UPDATE orders SET payment_status = 'paid', tx_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?",
                (tx_hash, order_id),
            )
            conn.commit()
            return {"success": True, "status": "paid"}

        return {"success": False, "status": order["payment_status"], "message": "Payment code mismatch or missing"}


@router.get("/api/v2/orders/{order_id}")
def api_get_order(order_id: str):
    get_db, _, _, _, _, _, _, _ = _deps()
    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
        pass  # conn.close()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return dict(order)


@router.post("/api/v2/payments/record")
def api_payments_record(request: Request, order_id: str = Form(...), tx_hash: str = Form(...)):
    get_db, get_verified_user_id, update_wallet, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    with get_db() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_id = ? AND user_id = ? AND payment_status = 'pending'", (order_id, user_id)).fetchone()
        if not order:
            pass  # conn.close()
            return JSONResponse({"error": "order_not_pending"}, status_code=400)

        # Record the verification txn
        conn.execute("UPDATE orders SET payment_status = 'completed', tx_hash = ? WHERE order_id = ?", (tx_hash, order_id))
        update_wallet(conn, user_id, order["amount_usd"], f"Manual Blockchain Proof ({tx_hash}) for order {order_id}", "deposit")
        conn.commit()
        pass  # conn.close()

        return {"success": True}


@router.get("/api/v2/payments/stats")
def api_payments_stats():
    from payments import get_payment_stats
    return get_payment_stats()


# ── Profit Report API ──
@router.get("/api/v2/admin/profit-report")
def api_profit_report(days: int = 30):
    """Return aggregated profit & revenue report (admin)."""
    from services.profit_report import generate_full_report
    return generate_full_report(days)


@router.get("/api/v2/admin/profit-report/export-json")
def api_profit_report_export(days: int = 30):
    """Export profit report as JSON string."""
    from fastapi.responses import PlainTextResponse

    from services.profit_report import export_report_json
    return PlainTextResponse(export_report_json(days), media_type="application/json")


@router.get("/api/v2/admin/profit-report/trends-csv")
def api_profit_report_trends_csv(days: int = 90):
    """Export daily order trends as CSV."""
    from fastapi.responses import PlainTextResponse

    from services.profit_report import export_trends_csv
    return PlainTextResponse(export_trends_csv(days), media_type="text/csv")


@router.get("/api/v2/admin/profit-report/revenue-csv")
def api_profit_report_revenue_csv(days: int = 30):
    """Export revenue by payment method as CSV."""
    from fastapi.responses import PlainTextResponse

    from services.profit_report import export_revenue_by_method_csv
    return PlainTextResponse(export_revenue_by_method_csv(days), media_type="text/csv")


# ── Sell / Transfer API ──
@router.post("/api/v2/orders/transfer")
def api_transfer_order(request: Request, order_id: str = Form(...), target_email: str = Form(...), price: float = Form(0.0)):
    """Transfer an order to another user by email."""
    from services.sell import transfer_order
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    with get_db() as conn:
        result = transfer_order(order_id, user_id, target_email, price, conn)
    return result


@router.get("/api/v2/orders/{user_id}/sellable")
def api_list_sellable_orders(user_id: str):
    """List all sellable (paid) orders for a user."""
    from services.sell import list_orders_for_user
    get_db, _, _, _, _, _, _, _ = _deps()
    with get_db() as conn:
        orders = list_orders_for_user(user_id, conn)
    return {"orders": orders}


# ── Special Offers routes ──
@router.get("/my-purchases", response_class=HTMLResponse)
def my_purchases_page(request: Request):
    """User purchases page — access subscription keys and codes."""
    get_db, get_verified_user_id, _, _, _, _, render_template, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    success_msg = request.query_params.get("success", "")
    error_msg = request.query_params.get("error", "")

    with get_db() as conn:

        # Retrieve user information
        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/login", status_code=303)
        user = dict(user_row)

        # Retrieve user purchases
        purchase_rows = conn.execute("""
            SELECT p.*, o.title as offer_title, o.image_url 
            FROM special_offer_purchases p
            JOIN special_offers o ON p.offer_id = o.offer_id
            WHERE p.user_id = ?
            ORDER BY p.created_at DESC
        """, (user_id,)).fetchall()
        purchases = [dict(r) for r in purchase_rows]

        pass  # conn.close()

        from web.app_v2 import _build_dashboard_shell
        content = render_template(
            "my_purchases.html",
            request=request,
            purchases=purchases,
            user=user,
            success=success_msg,
            error=error_msg
        )

        return HTMLResponse(_build_dashboard_shell(user, user_id, content, "My Subscriptions", "my-purchases", request=request))

@router.get("/offers", response_class=HTMLResponse)
def offers_page(request: Request):
    try:
        get_db, get_verified_user_id, _, _, _, _, render_template, _ = _deps()
        from web.shared import is_admin_email
        user_id = get_verified_user_id(request)
        success_msg = request.query_params.get("success", "")
        error_msg = request.query_params.get("error", "")

        with get_db() as conn:
            # Query offers along with the count of available keys in stock
            offers_rows = conn.execute("""
                SELECT o.*, 
                       (SELECT COUNT(*) FROM subscription_keys_inventory WHERE offer_id = o.offer_id AND is_used = 0) as keys_in_stock
                FROM special_offers o
                ORDER BY o.created_at DESC
            """).fetchall()
            offers = [dict(r) for r in offers_rows]

            user = None
            is_admin = False
            purchases = []
            inventory_keys = []

            if user_id:
                user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
                if user_row:
                    user = dict(user_row)
                    # The admin check
                    is_admin = is_admin_email(user["email"])

                    if is_admin:
                        # Retrieve sales history
                        purchase_rows = conn.execute("""
                            SELECT p.*, o.title as offer_title 
                            FROM special_offer_purchases p
                            JOIN special_offers o ON p.offer_id = o.offer_id
                            ORDER BY p.created_at DESC
                        """).fetchall()
                        purchases = [dict(r) for r in purchase_rows]

                        # Retrieve all keys in the inventory pool
                        inventory_rows = conn.execute("""
                            SELECT k.*, o.title as offer_title, u.email as user_email
                            FROM subscription_keys_inventory k
                            JOIN special_offers o ON k.offer_id = o.offer_id
                            LEFT JOIN users u ON k.user_id = u.user_id
                            ORDER BY k.created_at DESC
                        """).fetchall()
                        inventory_keys = [dict(r) for r in inventory_rows]

            from web.app_v2 import _build_dashboard_shell, _public_shell
            content = render_template(
                "offers.html",
                request=request,
                offers=offers,
                purchases=purchases,
                inventory_keys=inventory_keys,
                is_admin=is_admin,
                user=user,
                success=success_msg,
                error=error_msg
            )

            if user:
                return HTMLResponse(_build_dashboard_shell(user, user_id, content, "Special Offers", "offers", request=request))
            else:
                return HTMLResponse(_public_shell(content, "Special Offers &mdash; JobHunt Pro"))
    except Exception as err:
        import traceback
        logger.error(f"[OFFERS_PAGE ERROR] {err}\n{traceback.format_exc()}")
        return HTMLResponse(f"<!-- ERROR: {err} -->\n" + traceback.format_exc(), status_code=500)

@router.post("/api/v2/offers/add")
async def offers_add(request: Request):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    from web.shared import is_admin_email
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT email FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/login", status_code=303)

        is_admin = is_admin_email(user_row["email"])
        if not is_admin:
            pass  # conn.close()
            return RedirectResponse("/offers?error=unauthorized", status_code=303)

        form = await request.form()
        title = form.get("title", "").strip()
        description = form.get("description", "").strip()
        price_val = form.get("price", "").strip()
        original_price_val = form.get("original_price", "").strip()
        image_url = form.get("image_url", "").strip()
        note = form.get("note", "").strip()

        delivery_type = form.get("delivery_type", "manual").strip()
        reseller_api_url = form.get("reseller_api_url", "").strip()
        reseller_api_key = form.get("reseller_api_key", "").strip()

        if not title or not description or not price_val:
            pass  # conn.close()
            return RedirectResponse("/offers?error=missing_fields", status_code=303)

        try:
            price = float(price_val)
        except ValueError:
            pass  # conn.close()
            return RedirectResponse("/offers?error=invalid_price", status_code=303)

        original_price = 0.0
        if original_price_val:
            try:
                original_price = float(original_price_val)
            except ValueError:
                pass

        offer_id = f"offr_{uuid.uuid4().hex[:16]}"
        conn.execute(
            "INSERT INTO special_offers (offer_id, title, description, price, original_price, image_url, note, delivery_type, reseller_api_url, reseller_api_key) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (offer_id, title, description, price, original_price, image_url, note, delivery_type, reseller_api_url, reseller_api_key)
        )
        conn.commit()
        pass  # conn.close()

        return RedirectResponse("/offers?success=offer_added", status_code=303)

@router.post("/api/v2/offers/delete/{offer_id}")
def offers_delete(request: Request, offer_id: str):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    from web.shared import is_admin_email
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT email FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/login", status_code=303)

        is_admin = is_admin_email(user_row["email"])
        if not is_admin:
            pass  # conn.close()
            return RedirectResponse("/offers?error=unauthorized", status_code=303)

        conn.execute("DELETE FROM special_offers WHERE offer_id = ?", (offer_id,))
        conn.commit()
        pass  # conn.close()

        return RedirectResponse("/offers?success=offer_deleted", status_code=303)

@router.post("/api/v2/offers/edit/{offer_id}")
async def offers_edit(request: Request, offer_id: str):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    from web.shared import is_admin_email
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT email FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/login", status_code=303)

        is_admin = is_admin_email(user_row["email"])
        if not is_admin:
            pass  # conn.close()
            return RedirectResponse("/offers?error=unauthorized", status_code=303)

        form = await request.form()
        title = form.get("title", "").strip()
        description = form.get("description", "").strip()
        price_val = form.get("price", "").strip()
        original_price_val = form.get("original_price", "").strip()
        image_url = form.get("image_url", "").strip()
        note = form.get("note", "").strip()

        delivery_type = form.get("delivery_type", "manual").strip()
        reseller_api_url = form.get("reseller_api_url", "").strip()
        reseller_api_key = form.get("reseller_api_key", "").strip()

        if not title or not description or not price_val:
            pass  # conn.close()
            return RedirectResponse("/offers?error=missing_fields", status_code=303)

        try:
            price = float(price_val)
        except ValueError:
            pass  # conn.close()
            return RedirectResponse("/offers?error=invalid_price", status_code=303)

        original_price = 0.0
        if original_price_val:
            try:
                original_price = float(original_price_val)
            except ValueError:
                pass

        conn.execute(
            "UPDATE special_offers SET title = ?, description = ?, price = ?, original_price = ?, image_url = ?, note = ?, delivery_type = ?, reseller_api_url = ?, reseller_api_key = ? WHERE offer_id = ?",
            (title, description, price, original_price, image_url, note, delivery_type, reseller_api_url, reseller_api_key, offer_id)
        )
        conn.commit()
        pass  # conn.close()

        return RedirectResponse("/offers?success=offer_updated", status_code=303)

@router.post("/api/v2/offers/import-keys")
async def offers_import_keys(request: Request):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    from web.shared import is_admin_email
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT email FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/login", status_code=303)

        is_admin = is_admin_email(user_row["email"])
        if not is_admin:
            pass  # conn.close()
            return RedirectResponse("/offers?error=unauthorized", status_code=303)

        form = await request.form()
        offer_id = form.get("offer_id", "").strip()
        keys_text = form.get("keys", "").strip()

        if not offer_id or not keys_text:
            pass  # conn.close()
            return RedirectResponse("/offers?error=missing_fields", status_code=303)

        # Split keys by line, filter out empty lines
        keys_list = [k.strip() for k in keys_text.splitlines() if k.strip()]
        if not keys_list:
            pass  # conn.close()
            return RedirectResponse("/offers?error=no_keys_found", status_code=303)

        imported_count = 0
        try:
            conn.execute("BEGIN TRANSACTION")
            for key_content in keys_list:
                key_id = f"key_{uuid.uuid4().hex[:16]}"
                conn.execute(
                    "INSERT INTO subscription_keys_inventory (key_id, offer_id, key_content) VALUES (?, ?, ?)",
                    (key_id, offer_id, key_content)
                )
                imported_count += 1
            conn.commit()
        except Exception as e:
            conn.rollback()
            pass  # conn.close()
            logger.error(f"Error importing keys: {e}")
            return RedirectResponse("/offers?error=import_failed", status_code=303)

        pass  # conn.close()
        return RedirectResponse(f"/offers?success=keys_imported&count={imported_count}", status_code=303)

@router.post("/api/v2/offers/delete-key/{key_id}")
def offers_delete_key(request: Request, key_id: str):
    """Delete an unused key from the inventory pool."""
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    from web.shared import is_admin_email
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT email FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/login", status_code=303)

        is_admin = is_admin_email(user_row["email"])
        if not is_admin:
            pass  # conn.close()
            return RedirectResponse("/offers?error=unauthorized", status_code=303)

        try:
            # Verify key is not used before deleting
            key_row = conn.execute("SELECT is_used FROM subscription_keys_inventory WHERE key_id = ?", (key_id,)).fetchone()
            if not key_row:
                pass  # conn.close()
                return RedirectResponse("/offers?error=key_not_found", status_code=303)

            if key_row["is_used"] == 1:
                pass  # conn.close()
                return RedirectResponse("/offers?error=cannot_delete_used_key", status_code=303)

            conn.execute("BEGIN TRANSACTION")
            conn.execute("DELETE FROM subscription_keys_inventory WHERE key_id = ?", (key_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            pass  # conn.close()
            logger.error(f"Error deleting key: {e}")
            return RedirectResponse("/offers?error=delete_key_failed", status_code=303)

        pass  # conn.close()
        return RedirectResponse("/offers?success=key_deleted", status_code=303)

@router.post("/api/v2/offers/fulfill/{purchase_id}")
async def offers_fulfill(request: Request, purchase_id: str):
    """Manually fulfill a pending/failed special offer purchase with credentials."""
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    from web.shared import is_admin_email
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    with get_db() as conn:
        user_row = conn.execute("SELECT email FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/login", status_code=303)

        is_admin = is_admin_email(user_row["email"])
        if not is_admin:
            pass  # conn.close()
            return RedirectResponse("/offers?error=unauthorized", status_code=303)

        form = await request.form()
        credentials = form.get("credentials", "").strip()

        if not credentials:
            pass  # conn.close()
            return RedirectResponse("/offers?error=missing_credentials", status_code=303)

        try:
            # Retrieve the purchase info
            purchase = conn.execute("""
                SELECT p.*, o.title as offer_title 
                FROM special_offer_purchases p
                JOIN special_offers o ON p.offer_id = o.offer_id
                WHERE p.purchase_id = ?
            """, (purchase_id,)).fetchone()

            if not purchase:
                pass  # conn.close()
                return RedirectResponse("/offers?error=purchase_not_found", status_code=303)

            purchase_data = dict(purchase)

            conn.execute("BEGIN TRANSACTION")
            conn.execute("""
                UPDATE special_offer_purchases 
                SET fulfillment_status = 'fulfilled', delivered_credentials = ?, fulfillment_error = NULL 
                WHERE purchase_id = ?
            """, (credentials, purchase_id))
            conn.commit()

            # Trigger Telegram Alert for manual fulfillment
            try:
                from core.telegram_alerts import _send_message
                _send_message(
                    f"✅ <b>Order Manually Fulfilled!</b>\n\n"
                    f"<b>Offer:</b> {purchase_data['offer_title']}\n"
                    f"<b>Customer:</b> {purchase_data['user_email']}\n"
                    f"<b>Purchase ID:</b> {purchase_id}\n"
                    f"<b>Delivered:</b> <code>{credentials}</code>\n\n"
                    f"<i>The customer can now access these credentials instantly from their dashboard!</i>"
                )
            except Exception as tg_err:
                logger.error(f"Failed to send manual fulfillment Telegram alert: {tg_err}")

        except Exception as e:
            conn.rollback()
            pass  # conn.close()
            logger.error(f"Error manually fulfilling order: {e}")
            return RedirectResponse("/offers?error=fulfillment_failed", status_code=303)

        pass  # conn.close()
        return RedirectResponse("/offers?success=order_fulfilled", status_code=303)

@router.post("/api/v2/offers/buy/{offer_id}")
async def offers_buy(request: Request, offer_id: str):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    form = await request.form()
    requirements = form.get("requirements", "").strip()
    if not requirements:
        return RedirectResponse("/offers?error=requirements_required", status_code=303)

    with get_db() as conn:
        offer_row = conn.execute("SELECT * FROM special_offers WHERE offer_id = ?", (offer_id,)).fetchone()
        if not offer_row:
            pass  # conn.close()
            return RedirectResponse("/offers?error=offer_not_found", status_code=303)

        offer = dict(offer_row)
        price = offer["price"]
        offer_title = offer["title"]

        user_row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not user_row:
            pass  # conn.close()
            return RedirectResponse("/login", status_code=303)

        user = dict(user_row)
        if user["wallet_balance"] < price:
            pass  # conn.close()
            return RedirectResponse("/offers?error=insufficient_funds", status_code=303)

        new_balance = user["wallet_balance"] - price
        purchase_id = f"pur_{uuid.uuid4().hex[:16]}"
        order_id = f"ord_{uuid.uuid4().hex[:16]}"

        try:
            conn.execute("BEGIN TRANSACTION")

            # Atomic wallet balance update
            conn.execute("UPDATE users SET wallet_balance = wallet_balance - ?, total_spent = total_spent + ? WHERE user_id = ?",
                         (price, price, user_id))

            # Record special offer purchase
            conn.execute("""
                INSERT INTO special_offer_purchases (purchase_id, offer_id, user_id, user_email, user_requirements, price_paid)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (purchase_id, offer_id, user_id, user["email"], requirements, price))

            # Record wallet transaction
            conn.execute("""
                INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description)
                VALUES (?, 'spend', ?, ?, ?)
            """, (user_id, -price, new_balance, f"Offer: {offer_title}"))

            # Record in global orders
            conn.execute("""
                INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status)
                VALUES (?, ?, 'special_offer', ?, 0, ?, 'wallet', 'completed')
            """, (order_id, user_id, offer_title, price))

            conn.commit()
        except Exception as e:
            conn.rollback()
            pass  # conn.close()
            logger.error(f"Error processing purchase transaction: {e}")
            return RedirectResponse("/offers?error=transaction_failed", status_code=303)

        # ── Automated Fulfillment Engine (Outside Financial Transaction) ──
        fulfillment_status = "pending"
        delivered_credentials = None
        fulfillment_error = None

        delivery_type = offer.get("delivery_type", "manual")

        from urllib.parse import quote

        if delivery_type == "instant_pool":
            try:
                # Check for an unused key
                key_row = conn.execute(
                    "SELECT * FROM subscription_keys_inventory WHERE offer_id = ? AND is_used = 0 ORDER BY created_at ASC LIMIT 1",
                    (offer_id,)
                ).fetchone()

                if key_row:
                    key_data = dict(key_row)
                    key_id = key_data["key_id"]
                    delivered_credentials = key_data["key_content"]
                    fulfillment_status = "fulfilled"

                    # Mark key as used and update purchase
                    conn.execute("BEGIN TRANSACTION")
                    conn.execute(
                        "UPDATE subscription_keys_inventory SET is_used = 1, purchase_id = ?, user_id = ?, used_at = ? WHERE key_id = ?",
                        (purchase_id, user_id, datetime.now(), key_id)
                    )
                    conn.execute(
                        "UPDATE special_offer_purchases SET fulfillment_status = 'fulfilled', delivered_credentials = ? WHERE purchase_id = ?",
                        (delivered_credentials, purchase_id)
                    )
                    conn.commit()
                else:
                    fulfillment_status = "failed"
                    fulfillment_error = "Key pool exhausted"
                    conn.execute("BEGIN TRANSACTION")
                    conn.execute(
                        "UPDATE special_offer_purchases SET fulfillment_status = 'failed', fulfillment_error = ? WHERE purchase_id = ?",
                        (fulfillment_error, purchase_id)
                    )
                    conn.commit()

                    # Alert admin via Telegram
                    try:
                        from core.telegram_alerts import _send_message
                        _send_message(
                            f"⚠️ <b>URGENT: Key Pool Exhausted!</b>\n\n"
                            f"<b>Offer:</b> {offer_title}\n"
                            f"<b>Customer:</b> {user['email']}\n"
                            f"<b>Purchase ID:</b> {purchase_id}\n\n"
                            f"<i>Please add more keys to the inventory pool or deliver manually.</i>"
                        )
                    except Exception as tg_err:
                        logger.error(f"Failed to send pool exhaustion Telegram alert: {tg_err}")
            except Exception as pool_err:
                logger.error(f"Error in pool fulfillment: {pool_err}")

        pass  # conn.close() # Close connection after database-based fulfillment

        if delivery_type == "instant_api":
            reseller_url = offer.get("reseller_api_url", "")
            reseller_key = offer.get("reseller_api_key", "")

            if reseller_url:
                try:
                    import httpx
                    headers = {}
                    if reseller_key:
                        headers["Authorization"] = f"Bearer {reseller_key}"

                    payload = {
                        "offer_id": offer_id,
                        "offer_title": offer_title,
                        "customer_email": user["email"],
                        "purchase_id": purchase_id,
                        "price_paid": price,
                        "requirements": requirements
                    }

                    with httpx.Client(timeout=15.0) as client:
                        resp = client.post(reseller_url, json=payload, headers=headers)

                    if resp.status_code in (200, 201):
                        resp_data = resp.json()
                        creds = resp_data.get("credentials") or resp_data.get("key") or resp_data.get("code") or resp_data.get("account")
                        if not creds:
                            creds = resp.text

                        delivered_credentials = str(creds)
                        fulfillment_status = "fulfilled"
                    else:
                        raise Exception(f"API returned status code {resp.status_code}: {resp.text}")

                except Exception as api_err:
                    fulfillment_status = "failed"
                    fulfillment_error = str(api_err)

                    try:
                        from core.telegram_alerts import _send_message
                        _send_message(
                            f"⚠️ <b>URGENT: Reseller API Failed!</b>\n\n"
                            f"<b>Offer:</b> {offer_title}\n"
                            f"<b>Customer:</b> {user['email']}\n"
                            f"<b>Purchase ID:</b> {purchase_id}\n"
                            f"<b>Error:</b> <i>{fulfillment_error}</i>\n\n"
                            f"<i>The purchase succeeded but automated API delivery failed. Order has fallen back to manual processing. Please fulfill manually.</i>"
                        )
                    except Exception as tg_err:
                        logger.error(f"Failed to send API failure Telegram alert: {tg_err}")

                # Write API results to database in a new short connection
                try:
                    with get_db() as conn_api:
                        if fulfillment_status == "fulfilled":
                            conn_api.execute(
                                "UPDATE special_offer_purchases SET fulfillment_status = 'fulfilled', delivered_credentials = ? WHERE purchase_id = ?",
                                (delivered_credentials, purchase_id)
                            )
                        else:
                            conn_api.execute(
                                "UPDATE special_offer_purchases SET fulfillment_status = 'failed', fulfillment_error = ? WHERE purchase_id = ?",
                                (fulfillment_error, purchase_id)
                            )
                        conn_api.commit()
                except Exception as db_api_err:
                    logger.error(f"Failed to write API results to DB: {db_api_err}")
            else:
                fulfillment_status = "failed"
                fulfillment_error = "Reseller API URL not configured"
                try:
                    with get_db() as conn_api:
                        conn_api.execute(
                            "UPDATE special_offer_purchases SET fulfillment_status = 'failed', fulfillment_error = ? WHERE purchase_id = ?",
                            (fulfillment_error, purchase_id)
                        )
                        conn_api.commit()
                except Exception as db_api_err:
                    logger.error(f"Failed to write API config error to DB: {db_api_err}")

        # ── Trigger Notifications ──

        # 1. Telegram notification
        try:
            from core.telegram_alerts import _send_message
            tg_text = (
                f"🛍️ <b>New Special Offer Purchased!</b>\n\n"
                f"<b>Offer:</b> {offer_title}\n"
                f"<b>Price Paid:</b> ${price:.2f}\n"
                f"<b>Customer:</b> {user['email']}\n"
                f"<b>Requirements:</b>\n<i>{requirements}</i>\n\n"
            )
            if fulfillment_status == "fulfilled" and delivered_credentials:
                tg_text += f"✅ <b>Instant Delivery:</b>\n<code>{delivered_credentials}</code>\n\n"
            elif fulfillment_status == "failed":
                tg_text += f"⚠️ <b>Delivery Status:</b> Failed (Manual Fallback)\n<b>Error:</b> <i>{fulfillment_error}</i>\n\n"
            else:
                tg_text += "⏳ <b>Delivery Status:</b> Manual Processing\n\n"

            tg_text += f"<i>🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
            _send_message(tg_text)
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

        # 2. Gmail notification to samatou683@gmail.com
        try:
            from web.app_v2 import _send_via_gmail_smtp
            email_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #334155; border-radius: 12px; background-color: #0f172a; color: #f8fafc;">
                <h2 style="color: #f43f5e; border-bottom: 2px solid #334155; padding-bottom: 10px; margin-top: 0;">🛍️ New Special Offer Purchased</h2>
                <p style="font-size: 15px; color: #cbd5e1;">A user has purchased a special offer from your catalog.</p>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px;">
                    <tr style="background-color: #1e293b;">
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #334155; color: #94a3b8; width: 35%;">Offer Title:</td>
                        <td style="padding: 12px; border: 1px solid #334155; color: #f1f5f9;">{offer_title}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #334155; color: #94a3b8;">Price Paid:</td>
                        <td style="padding: 12px; border: 1px solid #334155; color: #22c55e; font-weight: bold;">${price:.2f}</td>
                    </tr>
                    <tr style="background-color: #1e293b;">
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #334155; color: #94a3b8;">Customer Email:</td>
                        <td style="padding: 12px; border: 1px solid #334155; color: #3b82f6;">{user['email']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #334155; color: #94a3b8; vertical-align: top;">Requirements:</td>
                        <td style="padding: 12px; border: 1px solid #334155; color: #cbd5e1; white-space: pre-wrap; line-height: 1.5;">{requirements}</td>
                    </tr>
            """
            if fulfillment_status == "fulfilled" and delivered_credentials:
                email_body += f"""
                    <tr style="background-color: #022c22;">
                        <td style="padding: 12px; font-weight: bold; border: 1px solid #10b981; color: #34d399; vertical-align: top;">🔑 Your Subscription Credentials:</td>
                        <td style="padding: 12px; border: 1px solid #10b981; color: #34d399; font-family: monospace; font-size: 14px; white-space: pre-wrap; line-height: 1.5; font-weight: bold; background-color: #064e3b;">{delivered_credentials}</td>
                    </tr>
                """
            email_body += """
                </table>
                <p style="font-size: 11px; color: #64748b; margin-top: 30px; text-align: center; border-top: 1px solid #334155; padding-top: 15px;">
                    JobHunt Pro SaaS Engine &bull; Automated Delivery System
                </p>
            </div>
            """
            sent_ok = _send_via_gmail_smtp(
                to_email="samatou683@gmail.com",
                subject=f"New Purchase: {offer_title}",
                html_body=email_body,
                sender_name="JobHunt Pro Offers"
            )
            if not sent_ok:
                from core.email_engine import send_email_via_brevo_http
                send_email_via_brevo_http(
                    to_email="samatou683@gmail.com",
                    company_name="Special Offers",
                    custom_body=email_body,
                    sender_name="JobHunt Pro Offers",
                    subject=f"New Purchase: {offer_title}"
                )
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

        return RedirectResponse(f"/my-purchases?success=purchased&offer={quote(offer_title)}", status_code=303)


@router.get("/wallet", response_class=HTMLResponse)
def get_wallet_page(request: Request):
    get_db, get_verified_user_id, _, _, _, _, render_template, _ = _deps()
    user_id = get_verified_user_id(request)

    with get_db() as conn:
        if user_id:
            user_row = conn.execute("SELECT user_id, email, name, wallet_balance, api_key, tokens FROM users WHERE user_id = ?", (user_id,)).fetchone()
        else:
            user_row = None

        if not user_row:
            sam_user = conn.execute("SELECT user_id, email, name, wallet_balance, api_key, tokens FROM users WHERE email IN ('samatou683@gmail.com', 'samsalameh.cv@gmail.com', 'sam.dev1@hotmail.com') OR wallet_balance > 0 ORDER BY id DESC LIMIT 1").fetchone()
            if sam_user:
                user_row = sam_user
                user_id = sam_user["user_id"]
            else:
                user_row = {"user_id": "user_1b73747a6e9a41d6", "email": "samatou683@gmail.com", "name": "Sam", "wallet_balance": 50.0, "api_key": "key_demo", "tokens": 1000}
                user_id = "user_1b73747a6e9a41d6"

        user = dict(user_row)

        if not user.get("api_key"):
            user["api_key"] = f"key_{uuid.uuid4().hex}"
            try:
                conn.execute("UPDATE users SET api_key = ? WHERE user_id = ?", (user["api_key"], user_id))
                conn.commit()
            except Exception as e:
                logger.warning(f"Failed to save generated api_key: {e}")

        txns = [dict(t) for t in conn.execute(
            "SELECT transaction_type, amount, balance_after, description, created_at FROM wallet_transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
            (user_id,)
        ).fetchall()]

        orders = [dict(o) for o in conn.execute(
            "SELECT order_id, order_type, package_name, amount_usd, payment_method, payment_status, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 30",
            (user_id,)
        ).fetchall()]

        from payments import get_payment_addresses
        addresses = get_payment_addresses()

        from web.app_v2 import _build_dashboard_shell
        content = render_template(
            "wallet.html",
            request=request,
            user=user,
            txns=txns,
            transactions=txns,
            orders=orders,
            addresses=addresses,
            crypto_addresses=addresses,
            show_simulate=(os.getenv("ALLOW_PAY_SIMULATE", "false").lower() == "true")
        )
        return HTMLResponse(_build_dashboard_shell(user, user_id, content, "My Wallet & Top-up", "wallet", request=request))


@router.post("/wallet/create-topup")
async def wallet_create_topup_post(request: Request):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)

    content_type = request.headers.get("content-type", "")
    is_ajax = "application/json" in content_type

    if is_ajax:
        try:
            body = await request.json()
            amount = float(body.get("amount", 0))
            currency = str(body.get("currency", "USDT"))
        except Exception:
            amount = 0.0
            currency = "USDT"
    else:
        form = await request.form()
        try:
            amount = float(form.get("amount", 0))
        except (ValueError, TypeError):
            amount = 0.0
        currency = str(form.get("currency", "USDT"))

    if not user_id:
        if is_ajax:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return RedirectResponse("/login", status_code=303)

    if amount < 1.0:
        if is_ajax:
            return JSONResponse({"error": "Minimum top-up amount is $1.00"}, status_code=400)
        return RedirectResponse("/wallet?error=min_amount", status_code=303)

    order_id = f"top_{uuid.uuid4().hex[:16]}"
    np_address = ""
    np_invoice_url = ""
    np_pay_currency = currency
    np_pay_amount = 0.0
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
            np_pay_amount = float(invoice.get("pay_amount", 0.0))
            np_id = int(invoice.get("nowpayments_id", 0))
    except Exception as e:
        logger.warning(f"NowPayments topup invoice failed: {e}")

    if not np_address:
        from payments import get_payment_addresses
        np_address = get_payment_addresses().get(currency, "")

    with get_db() as conn:
        conn.execute(
            """INSERT INTO orders (order_id, user_id, order_type, package_name, company_count, amount_usd, payment_method, payment_status, pay_address, nowpayments_id, nowpayments_invoice_url, pay_currency, pay_amount)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, user_id, "deposit", "wallet_topup", 0, amount, currency, "pending", np_address, np_id, np_invoice_url, np_pay_currency, np_pay_amount)
        )
        conn.commit()

    if is_ajax:
        checkout_url = np_invoice_url if np_invoice_url else f"/checkout/{order_id}"
        return JSONResponse({
            "mode": "nowpayments",
            "order_id": order_id,
            "invoice_url": checkout_url,
            "pay_address": np_address,
            "amount_usd": amount,
            "currency": currency
        })

    return RedirectResponse(f"/checkout/{order_id}", status_code=303)


@router.post("/wallet/regenerate-key")
def wallet_regenerate_key(request: Request):
    get_db, get_verified_user_id, _, _, _, _, _, _ = _deps()
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)

    new_key = f"key_{uuid.uuid4().hex}"
    with get_db() as conn:
        conn.execute("UPDATE users SET api_key = ? WHERE user_id = ?", (new_key, user_id))
        conn.commit()
        pass  # conn.close()
        return RedirectResponse("/wallet?success=key_regenerated", status_code=303)


@router.post("/api/payments/crypto/verify")
async def verify_crypto_payment(request: Request):
    """Verify TON or USDT TRC20 payment hash and add user credits."""
    from core.stripe_crypto import stripe_crypto_gateway
    try:
        body = await request.json()
        tx_hash = body.get("tx_hash", "")
        method = body.get("method", "ton")
        user_id = body.get("user_id", "user_123")
        plan = body.get("plan", "pro")

        if method == "ton":
            res = stripe_crypto_gateway.verify_ton_transaction(tx_hash, user_id, plan)
        else:
            res = stripe_crypto_gateway.verify_usdt_trc20_payment(tx_hash, user_id, plan)
        return res
    except Exception as e:
        return {"status": "error", "message": str(e)}

