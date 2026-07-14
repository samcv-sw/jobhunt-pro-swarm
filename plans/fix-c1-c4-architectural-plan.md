# Architectural Plan: Fix Critical Issues C1-C4

## Overview

This plan addresses the 4 critical issues identified in [`plans/polish-before-launch.md`](plans/polish-before-launch.md). After thorough analysis of the actual codebase, several discrepancies between the documented issues and real code were discovered. This plan reflects the **actual** problems found.

---

## C1 — Verify Payment Payload Mismatch

### What the plan doc claimed
Frontend doesn't send `payment_code` in the verify-payment payload.

### What was actually found
The frontend in [`web/templates/checkout_v2.html`](web/templates/checkout_v2.html:429) **does** send `payment_code` and `tx_hash` via JSON:
```javascript
const resp = await fetch('/api/v2/orders/verify-payment', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ order_id: orderId, tx_hash: txHash, payment_code: paymentCode })
});
```

The **real problem** is in [`web/routers/payments.py`](web/routers/payments.py:439):
```python
@router.post("/api/v2/orders/verify-payment")
def api_verify_payment(request: Request, order_id: str = Form(...)):
```
- Backend uses `Form(...)` expecting `application/x-www-form-urlencoded`
- Frontend sends `Content-Type: application/json`
- **Result**: `payment_code` and `tx_hash` are completely ignored by the backend
- A Pydantic model [`OrderVerifyRequest`](web/app_v2.py:7797-7800) already exists but is unused

### Fix
1. Change the endpoint to accept JSON body using the existing `OrderVerifyRequest` model
2. Add actual verification logic: validate `payment_code` against the order's stored code, validate `tx_hash` against `wallet_transactions`
3. Return meaningful status updates to the frontend

### Files to modify
- [`web/routers/payments.py`](web/routers/payments.py:439) — rewrite `api_verify_payment` function

### Risk
Low. The endpoint is isolated, and the existing Pydantic model provides type safety.

---

## C2 — Empty Crypto Wallet Addresses

### What the plan doc claimed
Lines 53-56 in `config.py` have empty string defaults.

### What was actually found
In [`config.py`](config.py:295-299), all 4 crypto wallet addresses default to `""`:
```python
CRYPTO_BTC_ADDRESS = os.getenv("CRYPTO_BTC_ADDRESS", "")
CRYPTO_ETH_ADDRESS = os.getenv("CRYPTO_ETH_ADDRESS", "")
CRYPTO_USDT_ADDRESS = os.getenv("CRYPTO_USDT_ADDRESS", "")
CRYPTO_LTC_ADDRESS = os.getenv("CRYPTO_LTC_ADDRESS", "")
```

However, [`payments/gateway.py`](payments/gateway.py:23-28) has hardcoded fallback addresses that are **not** empty. These should be used as the fallback values in `config.py`.

### Fix
Replace the empty string defaults in `config.py` with the real wallet addresses from `payments/gateway.py`.

### Files to modify
- [`config.py`](config.py:295-299) — update 4 lines with real wallet address defaults

### Risk
Very low. Simple string replacement. Environment variables still take precedence via `os.getenv`.

---

## C3 — Create `services/profit_report.py`

### What the plan doc claimed
File exists at `services/profit_report.py`.

### What was actually found
File does **not** exist anywhere in the workspace. Must be created from scratch.

### Design
Create a new module at [`services/profit_report.py`](services/profit_report.py) following the patterns in:
- [`services/__init__.py`](services/__init__.py)
- [`services/catalog.py`](services/catalog.py)
- [`services/fulfillment.py`](services/fulfillment.py)

The module should:
1. Query `orders` and `wallet_transactions` tables for revenue data
2. Calculate total revenue, profit (revenue minus costs), and trends over configurable periods (daily, weekly, monthly)
3. Provide functions:
   - `get_revenue_summary(start_date, end_date)` — total revenue, order count, avg order value
   - `get_profit_report(start_date, end_date)` — revenue minus costs, with breakdown by payment method
   - `get_trend_data(period)` — daily/weekly/monthly revenue/profit series for charts
   - `export_report(fmt)` — export as JSON or CSV
4. Use the same `get_db()` pattern as other services
5. Include proper error handling and logging

### Files to create
- [`services/profit_report.py`](services/profit_report.py) — new module

### Risk
Low. Standalone module with no existing callers to break.

---

## C4 — Create `services/sell.py`

### What the plan doc claimed
File exists at `services/sell.py`.

### What was actually found
File does **not** exist anywhere in the workspace. Must be created from scratch.

### Design
Create a new module at [`services/sell.py`](services/sell.py) following the same patterns as C3.

The module should handle selling/transferring service subscriptions between users or generating sellable purchase links:
1. Query `orders` and `purchases` tables for sellable items
2. Provide functions:
   - `create_sell_listing(user_id, purchase_id, price)` — list a purchase for resale
   - `buy_listing(buyer_id, listing_id)` — transfer ownership of a purchase
   - `get_user_listings(user_id)` — get all listings by a user
   - `get_available_listings()` — get all available listings for the marketplace
   - `cancel_listing(user_id, listing_id)` — remove a listing
3. Validate ownership before allowing transfers
4. Update database atomically (transfer in a transaction)
5. Use the same `get_db()` pattern as other services

### Files to create
- [`services/sell.py`](services/sell.py) — new module

### Risk
Low. Standalone module with no existing callers to break.

---

## Implementation Order

| Priority | Issue | Complexity | Dependencies |
|----------|-------|-----------|-------------|
| 1 | **C1** — Verify payment payload fix | Medium | None |
| 2 | **C2** — Wallet address defaults | Low | None |
| 3 | **C3** — Create profit_report.py | Medium | Must study existing service patterns |
| 4 | **C4** — Create sell.py | Medium | Must study existing service patterns |

---

## Architecture Diagram

```mermaid
flowchart TD
    subgraph Frontend
        CV[checkout_v2.html]
        VF[verifyPayment function]
    end
    
    subgraph Backend
        EP[/api/v2/orders/verify-payment]
        PR[payments/routers.py]
        OVR[OrderVerifyRequest model]
    end
    
    subgraph Config
        CFG[config.py]
        GW[payments/gateway.py]
    end
    
    subgraph New_Services
        PRF[services/profit_report.py]
        SLL[services/sell.py]
    end
    
    subgraph Database
        ORD[orders table]
        WT[wallet_transactions table]
        PUR[purchases table]
    end
    
    CV -->|JSON payload| VF
    VF -->|POST with payment_code + tx_hash| EP
    EP -->|C1 FIX: accept JSON via OVR| PR
    PR -->|validate payment_code + tx_hash| ORD
    PR -->|validate tx_hash| WT
    
    CFG -->|C2 FIX: real wallet defaults| GW
    
    PRF -->|query revenue data| ORD
    PRF -->|query profit data| WT
    
    SLL -->|query listings| PUR
    SLL -->|transfer ownership| ORD
```

---

## Approval

Once approved, switch to **Code mode** to implement all 4 fixes in the order specified above.
