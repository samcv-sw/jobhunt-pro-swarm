# Handoff Report — Milestone M4 (Features 17 & 18 Investigation)

**Agent**: explorer_m4_2 (Milestone M4 Explorer)  
**Parent**: 1a88d940-650d-405f-a7dd-88b2f8b9a304  
**Date**: 2026-08-14  
**Focus**: Feature 17 (Atomic Wallet Balance Increment & Deduction Ledger) and Feature 18 (Localized GCC Fiat Checkout: Mada, KNET, Apple Pay, Tamara, Tabby with SAR/AED Pricing)

---

## 1. Observation

Direct code and database inspections revealed the following facts:

1. **Wallet Schema & Table Definitions**:
   - In `infra/init.sql` (lines 118–130) and `web/app_v2.py` (lines 1915–1925):
     ```sql
     CREATE TABLE IF NOT EXISTS wallet_transactions (
         id INTEGER/SERIAL PRIMARY KEY AUTOINCREMENT,
         user_id VARCHAR(64)/TEXT NOT NULL,
         transaction_type VARCHAR(50)/TEXT NOT NULL,
         amount DECIMAL(10,2)/REAL NOT NULL,
         balance_after DECIMAL(10,2)/REAL,
         description TEXT,
         tx_hash VARCHAR(255)/TEXT,
         created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
         FOREIGN KEY (user_id) REFERENCES users(user_id)
     );
     ```
   - In `infra/init.sql` (line 130) and `web/app_v2.py` (lines 1988, 2289), index is only on `user_id` (`idx_wallet_tx_user`), but **no index exists on `tx_hash`**, which impedes fast idempotency lookups.

2. **Existing Wallet Helper Functions in `web/shared.py` (lines 207–235)**:
   - `update_wallet(conn, user_id, delta, desc, txn_type="adjustment")`:
     ```python
     conn.execute("UPDATE users SET wallet_balance = wallet_balance + ? WHERE user_id = ?", (delta, user_id))
     row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
     if row:
         bal = row[0] if not hasattr(row, "__getitem__") else row["wallet_balance"]
         conn.execute("INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) VALUES (?, ?, ?, ?, ?)",
                      (user_id, txn_type, delta, bal, desc))
         return bal
     ```
   - `deduct_wallet(conn, user_id, amount, desc, txn_type="deduction") -> bool`:
     ```python
     cur = conn.execute("UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ? AND wallet_balance >= ?",
                        (amount, user_id, amount))
     if getattr(cur, "rowcount", 0) == 0:
         return False
     row = conn.execute("SELECT wallet_balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
     bal = row[0] if row and not hasattr(row, "__getitem__") else (row["wallet_balance"] if row else 0.0)
     conn.execute("INSERT INTO wallet_transactions (user_id, transaction_type, amount, balance_after, description) VALUES (?, ?, ?, ?, ?)",
                  (user_id, txn_type, -amount, bal, desc))
     return True
     ```
   - Neither function accepts `tx_id` or `tx_hash`, nor do they record `tx_hash` into `wallet_transactions`.
   - In `PROJECT.md` (line 65), the specified Interface Contract is:
     `update_wallet(user_id: int, amount: float, description: str, tx_id: str) -> dict`.

3. **Inconsistent / Race-Prone Wallet Deductions Across Routers**:
   - In `web/routers/payments.py` lines 1324–1337 (`/api/v2/offers/buy/{offer_id}`):
     ```python
     if user["wallet_balance"] < price:
         return RedirectResponse("/offers?error=insufficient_funds", status_code=303)
     # ...
     conn.execute("UPDATE users SET wallet_balance = wallet_balance - ?, total_spent = total_spent + ? WHERE user_id = ?",
                  (price, price, user_id))
     ```
     The query lacks `AND wallet_balance >= ?`, creating a race condition where concurrent requests can drive the balance negative.
   - In `web/routers/webhook_bot.py` lines 70–89:
     ```python
     if user["tokens"] < 1: ...
     await conn.execute("UPDATE users SET tokens = tokens - 1 WHERE user_id = $1", user["user_id"])
     ```
     Lacks `AND tokens >= 1`, allowing tokens to become negative under concurrent webhook dispatches.

4. **Existing GCC Pricing & Billing Capabilities**:
   - `core/pricing_manager.py` (lines 460–556): Contains `GCC_CURRENCIES` (SAR rate 3.75, AED rate 3.6725, QAR 3.64, KWD 0.308, BHD 0.376, OMR 0.385) and `get_gcc_localized_pricing(country_code, preferred_currency)`.
   - `core/gcc_billing.py` (lines 10–106): `GCCBillingService` computes VAT for KSA (15% ZATCA), UAE (5% FTA), Bahrain (10%), Oman (5%), and generates compliant dual-language B2B invoices with base64 ZATCA QR codes.
   - `core/gcc_unified_checkout.py` (lines 15–109): `GCCUnifiedCheckout` provides country PPP configurations and session generation for Mada, Apple Pay, Tap, Moyasar, and KNET, with HMAC-SHA256 signature verification.

5. **Gaps in GCC Checkout (Feature 18)**:
   - Tamara (`tamara`) and Tabby (`tabby`) Buy-Now-Pay-Later (BNPL) 4-installment split payment options are not implemented in `core/gcc_unified_checkout.py`.
   - Missing dedicated REST endpoints `/api/v2/checkout/gcc-session` and `/api/v2/checkout/gcc-webhook` for generating GCC gateway sessions and handling webhooks with automatic atomic wallet crediting.
   - `web/templates/checkout_v3.html` does not feature dedicated tabs / badges for Mada 🇸🇦, KNET 🇰🇼, Apple Pay 🍏, Tamara 🛍️, and Tabby 💳 with 4-split installment displays.

---

## 2. Logic Chain

1. **From Observation 1 & 2 to Ledger Integrity**:
   - `wallet_transactions` contains `tx_hash`, but `update_wallet` does not record it or check for duplicate transactions.
   - When crypto or GCC webhooks retry callbacks, absence of `tx_hash` deduplication allows double-crediting.
   - *Conclusion*: `update_wallet` must accept `tx_id`/`tx_hash`, perform an idempotency lookup against `wallet_transactions.tx_hash`, and insert `tx_hash` into the ledger. An index `idx_wallet_tx_hash` must be added.

2. **From Observation 2 & 3 to Concurrency & Negative Balance Prevention**:
   - Reading `wallet_balance` via `SELECT` followed by an unconstrained `UPDATE` creates a classic Time-of-Check to Time-of-Use (TOCTOU) race condition.
   - Deductions must always execute conditionally in SQL: `UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ? AND wallet_balance >= ?` and inspect `rowcount == 1`.
   - All router deduction paths must be routed through a hardened `deduct_wallet()` or use atomic conditional SQL.

3. **From Observation 2 & Interface Contract to Backward Compatibility**:
   - Existing codebase callers use `update_wallet(conn, user_id, delta, desc, txn_type)`.
   - `PROJECT.md` requires `update_wallet(user_id, amount, description, tx_id) -> dict`.
   - *Conclusion*: A polymorphic signature in `web/shared.py` (and imported in `web/app_v2.py`) can inspect arguments: if the first argument is a DB connection, it operates on that connection; if `user_id` is passed directly, it acquires a managed DB connection via `get_db()`, executes inside an explicit transaction, and returns a structured dictionary `{ "success": True, "new_balance": bal, "tx_hash": tx_id, ... }`.

4. **From Observation 4 & 5 to Localized GCC Fiat Checkout (Feature 18)**:
   - `core/pricing_manager.py` and `core/gcc_billing.py` already possess accurate exchange rates (SAR 3.75, AED 3.67, KWD 0.31) and tax logic (ZATCA 15%, UAE FTA 5%).
   - Extending `core/gcc_unified_checkout.py` with Tamara and Tabby BNPL 4-installment splits (`calculate_bnpl_installments`), connecting it to new API endpoints (`/api/v2/checkout/gcc-session`, `/api/v2/checkout/gcc-webhook`), and updating the frontend `checkout_v3.html` UI completes Feature 18.

---

## 3. Caveats

1. **No External Live Gateway Credentials Required for M4**:
   - Production API credentials for Tap, Moyasar, Tamara, and Tabby are sandbox/configurable via environment variables (`TAP_SECRET_KEY`, `MOYASAR_API_KEY`, `TAMARA_API_TOKEN`, `TABBY_PUBLIC_KEY`). Mock / sandbox session generation and HMAC webhook validation ensure 100% testability and zero live financial dependency.
2. **SQLite vs PostgreSQL Concurrency Differences**:
   - SQLite operates with database-level locking during writes (`WAL` mode). PostgreSQL operates with row-level locks. The conditional `UPDATE ... WHERE wallet_balance >= ?` query is atomic across both SQLite and PostgreSQL.
3. **Database Migration Safety**:
   - The column `tx_hash` already exists in `wallet_transactions` across `init.sql` and `app_v2.py`. Only the missing index `idx_wallet_tx_hash` needs `CREATE INDEX IF NOT EXISTS`.

---

## 4. Conclusion & Actionable Blueprint for Worker

The Worker agent should implement the following concrete plan:

### Step 1: Harden `web/shared.py` with Polymorphic Atomic Wallet Ledger
- Implement enhanced `update_wallet` and `deduct_wallet`:
  - **Signatures**:
    - `update_wallet(conn_or_user_id, user_id_or_amount=None, delta_or_desc=None, desc_or_tx_id=None, txn_type="adjustment", tx_id=None) -> dict | float`
    - `deduct_wallet(conn_or_user_id, user_id_or_amount=None, amount_or_desc=None, desc_or_tx_id=None, txn_type="deduction", tx_id=None) -> dict | bool`
  - **Idempotency**: If `tx_id`/`tx_hash` is given, check `SELECT id, balance_after FROM wallet_transactions WHERE tx_hash = ?`. If found, return `{ "success": True, "duplicate": True, "new_balance": balance_after }`.
  - **Negative Balance Guard**: In `deduct_wallet`, use `UPDATE users SET wallet_balance = wallet_balance - ? WHERE user_id = ? AND wallet_balance >= ?`, verify `rowcount > 0`.
  - **Audit Trail**: Always insert a row into `wallet_transactions` with `(user_id, transaction_type, amount, balance_after, description, tx_hash)`.
  - **Index**: Add `CREATE INDEX IF NOT EXISTS idx_wallet_tx_hash ON wallet_transactions(tx_hash);` in `web/app_v2.py`, `infra/init.sql`, and `core/pg_sqlite_shim.py`.

### Step 2: Extend `core/gcc_unified_checkout.py` for Tamara & Tabby BNPL
- Add `tamara` and `tabby` to `COUNTRY_PPP_CONFIG` for `SA`, `AE`, and `KW`.
- Implement `calculate_bnpl_installments(amount_local: float, currency: str, installments: int = 4) -> dict`.
- Implement provider checkout URLs for Tamara (`https://api.tamara.co/v2/checkout`) and Tabby (`https://api.tabby.ai/api/v2/checkout`).
- Implement `process_gcc_webhook(payload, signature, secret_key)` which validates HMAC SHA-256 and calls `update_wallet(user_id=user_id, amount=amount_usd, description=..., tx_id=tx_hash)`.

### Step 3: Expose GCC Checkout Endpoints in `web/routers/gcc_billing_router.py`
- `POST /api/v2/checkout/gcc-session`: Accepts `plan_id`, `country_code`, `payment_method`, `user_email`. Returns localized amounts (SAR/AED/KWD), installment info, and provider checkout link.
- `POST /api/v2/checkout/gcc-webhook`: Validates HMAC signature, prevents replay attacks, and updates user wallet.
- `GET /api/v2/checkout/gcc-methods`: Returns supported payment methods, currencies, and BNPL parameters per country.

### Step 4: Update Frontend `web/templates/checkout_v3.html` & `crypto_checkout_modal.html`
- Add localized GCC payment method selector: Mada 🇸🇦, KNET 🇰🇼, Apple Pay 🍏, Tamara 🛍️, Tabby 💳.
- Render 4-installment breakdown for SAR & AED.
- Enforce Cairo/Tajawal fonts, RTL directionality, CSS logical properties, and green/gold styling tokens per AGENTS.md.

### Step 5: Implement Comprehensive Test Suite `tests/test_wallet_and_gcc_checkout.py`
- Test cases for:
  1. `update_wallet` atomic crediting + ledger insertion.
  2. `update_wallet` idempotency with duplicate `tx_id`.
  3. `deduct_wallet` successful debit vs. insufficient funds rejection.
  4. Concurrent debit race condition resistance (preventing balance < 0).
  5. Dual-mode calling convention (with connection and standalone keyword args).
  6. GCC localized pricing calculation for SAR, AED, KWD, QAR with VAT.
  7. Tamara & Tabby BNPL installment calculation.
  8. GCC checkout session generation for all 5 payment methods (Mada, KNET, Apple Pay, Tamara, Tabby).
  9. GCC webhook signature verification (HMAC-SHA256) and replay protection.
  10. FastAPI endpoints integration (`/api/v2/checkout/gcc-session`, `/api/v2/checkout/gcc-webhook`, `/api/pricing/localized`).

---

## 5. Verification Method

To verify the implementation independently:

1. **Execute Project Test Suite**:
   ```bash
   python -m pytest tests/test_gcc_billing.py tests/test_gcc_and_roi_calculator.py tests/test_wallet_and_gcc_checkout.py -v
   ```
2. **Files to Inspect**:
   - `web/shared.py` (check `update_wallet` and `deduct_wallet` implementations)
   - `core/gcc_unified_checkout.py` (check Tamara, Tabby, Mada, KNET, Apple Pay handlers)
   - `web/routers/gcc_billing_router.py` (check `/api/v2/checkout/gcc-session` & `/api/v2/checkout/gcc-webhook`)
   - `web/templates/checkout_v3.html` (verify GCC payment options and RTL styling)
   - `tests/test_wallet_and_gcc_checkout.py` (verify 100% test pass rate)
3. **Invalidation Conditions**:
   - Any test failure in `pytest`.
   - `wallet_balance` going below 0.0 under concurrent deductions.
   - Duplicate `tx_id` causing balance to increase twice.
   - Non-compliant CSS properties (e.g. `margin-left` instead of `margin-inline-start`).
