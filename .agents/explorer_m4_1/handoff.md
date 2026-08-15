# M4 Milestone Exploration Report: Crypto Invoicing, On-Chain RPC Verification & HMAC-SHA512 IPN Webhook Security

**Target Features**: Features 14, 15, 16 (Milestone M4, Iteration 1)  
**Investigator**: Explorer Agent M4.1  
**Status**: Investigation Complete — Ready for Worker Implementation  

---

## 1. Observation

Direct code observations across existing payment files, routers, schemas, and configurations:

### Feature 14: Non-Custodial Multi-Chain Crypto Invoicing (USDT/USDC on TRC20, Polygon, TON)
- **`payments/nowpayments.py` (lines 35, 210-254)**:
  - `SUPPORTED_CURRENCIES` lists 12 coins (`["BTC", "ETH", "USDT", "LTC", "BNB", "MATIC", "SOL", "TRX", "ADA", "DOT", "DAI", "BUSD"]`), but lacks explicit stablecoin multi-chain entries for USDT-Polygon (`usdtmatic`), USDC-Polygon (`usdcmatic`), USDC-TRC20 (`usdctrc20`), TON (`ton`), and USDT-TON (`usdton`).
  - `create_crypto_invoice()` only maps aliases for `usdttrc20` (lines 211-217):
    ```python
    curr = (pay_currency or "").lower().strip()
    if curr in ("usdt", "usdttrc20", "usdt-trc20", "usdt (trc20)"):
        target_currency = "usdttrc20"
    ```
    Missing Polygon USDT/USDC (`usdtmatic`, `usdcmatic`), TON USDT (`usdton`), and explicit network routing.
  - Invoicing flags: `is_fixed_rate=True` and `is_fee_paid_by_user=True` are partially present in `create_invoice()` (line 134-135) but need consistent enforcement for zero merchant fees.
- **`payments/gateway.py` (lines 23-28, 148-156)**:
  - Direct non-custodial fallback addresses only define:
    ```python
    self.wallets = {
        "btc": os.getenv("CRYPTO_BTC_ADDRESS", "bc1q0e68d76d8dc303249a1992405ac2879f97fa8f"),
        "eth": os.getenv("CRYPTO_ETH_ADDRESS", "0x0e68d76d8dc303249a1992405ac2879f97fa8fec"),
        "usdt": os.getenv("CRYPTO_USDT_ADDRESS", "0xc303249a1992405ac2879f97fa8fec34c72be2f8"),
        "ltc": os.getenv("CRYPTO_LTC_ADDRESS", "ltc1q0e68d76d8dc303249a1992405ac2879f97fa8f"),
    }
    ```
    Missing non-custodial sovereign wallet addresses for TRC20 (`CRYPTO_USDT_TRC20_ADDRESS` / `CRYPTO_TRON_ADDRESS`), Polygon (`CRYPTO_POLYGON_ADDRESS`), and TON (`CRYPTO_TON_ADDRESS`).
- **`payments/__init__.py` (lines 64-75, 86-90)**:
  - `get_payment_addresses()` and `record_payment()` hardcode currency validation to `("BTC", "ETH", "USDT", "LTC")` and reject other network identifiers.

### Feature 15: On-Chain Double-Spend & Replay Verification (TronGrid, Polygon, TON with 12+ Confirmations)
- **`payments/crypto_verifier.py`**:
  - Currently **does not exist**.
- **`core/stripe_crypto.py` (lines 36-65)**:
  - Contains mock stubs for blockchain verification:
    ```python
    def verify_ton_transaction(self, tx_hash: str, user_id: str, plan: str = "pro") -> Dict[str, Any]:
        """Verifies TON blockchain transaction hash and credits user account."""
        plan_info = TIER_PLANS.get(plan, TIER_PLANS["pro"])
        # Mock TON blockchain verification
        is_valid = len(tx_hash) >= 10
        ...
    def verify_usdt_trc20_payment(self, tx_hash: str, user_id: str, plan: str = "pro") -> Dict[str, Any]:
        """Verifies USDT TRC20 transaction hash on Tron/EVM network."""
        plan_info = TIER_PLANS.get(plan, TIER_PLANS["pro"])
        return { "status": "success", ... }
    ```
  - Lacks real RPC/REST calls to TronGrid, Polygon POS RPC, or TON API.
  - Lacks confirmation depth check (`confirmations >= 12`).
  - Lacks recipient wallet verification (confirming recipient is our system wallet).
  - Lacks transferred amount verification (confirming `transferred_amount >= expected_amount`).
- **Replay / Double-Spend Protection**:
  - No `crypto_processed_txs` database table or replay cache exists in `infra/init.sql` or SQLite schema. Any transaction hash can currently be submitted multiple times without rejection.

### Feature 16: Mandatory HMAC SHA-512 IPN Webhook Security Validation & Replay Protection
- **`payments/nowpayments.py` (lines 156-191, 256-326)**:
  - Line 170: `body = json.dumps(ipn_data, sort_keys=True).encode()` does not use standard compact JSON separators `separators=(',', ':')`, which can lead to signature verification failures when NOWPayments sends compact JSON without space after colons.
  - `process_ipn_callback(ipn_data: dict, headers: dict) -> bool` (line 256) returns a single boolean.
- **`web/routers/payments.py` (lines 579-598)**:
  - Calls `success, order_id, amount_usd = process_ipn_callback(body, headers)` on line 586:
    ```python
    @router.post("/api/v2/nowpayments-ipn")
    async def api_nowpayments_ipn(request: Request):
        ...
        body = await request.body()
        headers = dict(request.headers)
        success, order_id, amount_usd = process_ipn_callback(body, headers)
    ```
    This causes a **CRITICAL RUNTIME CRASH** (`ValueError: too many values to unpack (expected 3, got 1)`) and passes raw bytes `body` where `nowpayments.py` expects a `dict`.
- **IPN Replay Protection**:
  - Missing webhook deduplication / replay tracking. If an IPN for an already-completed order is re-delivered, multiple wallet top-ups could occur if status check is bypassed or concurrent requests arrive.

---

## 2. Logic Chain

1. **Multi-Chain Expansion**:
   - Customers across GCC / MENA need zero-merchant-fee USDT & USDC payment options on TRC20, Polygon, and TON.
   - For gateway checkout: `NOWPaymentsClient.create_invoice()` and `create_crypto_invoice()` must correctly route currency codes (`usdttrc20`, `usdtmatic`, `usdcmatic`, `usdctrc20`, `ton`, `usdton`) with `is_fee_paid_by_user=True` and `is_fixed_rate=True`.
   - For direct non-custodial checkout: `payments/gateway.py` and `payments/__init__.py` must expose sovereign addresses configured via `CRYPTO_USDT_TRC20_ADDRESS`, `CRYPTO_POLYGON_ADDRESS`, `CRYPTO_TON_ADDRESS`, etc., allowing direct $0-fee transfers.
2. **On-Chain Verification Mechanism (`payments/crypto_verifier.py`)**:
   - When users submit blockchain transaction proofs (via `/api/payments/crypto/verify` or direct invoice verification), we must query legitimate public RPCs/APIs:
     - **TronGrid API** (`https://api.trongrid.io` or `TRONGRID_API_URL`): Query `/wallet/gettransactioninfobyid` + `/wallet/getnowblock`. Verify contract result is `SUCCESS`, contract type is TRC20 transfer (or TRX transfer), target address matches configured Tron recipient, amount transferred >= expected amount, and block confirmations `current_block - tx_block >= 12`.
     - **Polygon RPC** (`https://polygon-rpc.com` or `POLYGON_RPC_URL`): Query `eth_getTransactionByHash`, `eth_getTransactionReceipt`, and `eth_blockNumber`. Verify receipt status `0x1`, decode ERC-20 transfer calldata (`0xa9059cbb`), verify recipient matches configured Polygon address, amount >= expected amount, and confirmations `current_block - tx_block >= 12`.
     - **TON API** (`https://toncenter.com/api/v2` or `TON_API_URL`): Query transaction details, check destination address, value, and successful completion.
   - **Double-Spend / Replay Defense**:
     - Maintain `crypto_processed_txs` in SQLite/Postgres with a `UNIQUE` constraint on `tx_hash`.
     - Check before RPC query: if `tx_hash` exists in `crypto_processed_txs` or `wallet_transactions`, reject immediately with `(False, "Replay attack detected: transaction hash already processed")`.
     - After successful on-chain verification, record `tx_hash`, `network`, `amount_usd`, `recipient`, `user_id`, `order_id`, and `confirmations` atomically inside `crypto_processed_txs`.
   - **Offline / Test Mode Resilience**:
     - Implement deterministic test doubles for `mock_tron_*`, `mock_poly_*`, and `mock_ton_*` transactions so pytest runs cleanly without network dependencies.
3. **HMAC SHA-512 IPN Security & Webhook Unification**:
   - Standardize HMAC SHA-512 calculation:
     - Sort dictionary keys in ascending order.
     - Serialize using `json.dumps(sorted_dict, separators=(',', ':'), sort_keys=True)`.
     - Compute HMAC-SHA512 with `NOWPAYMENTS_IPN_SECRET`.
     - Compare using `hmac.compare_digest(computed, received_sig)`.
     - Reject with 403 if signature is missing or invalid.
   - Fix interface mismatch in `payments/nowpayments.py` & `web/routers/payments.py`:
     - Update `process_ipn_callback(raw_body: bytes | str | dict, headers: dict) -> tuple[bool, str, float, str]`.
     - Handle parsing of raw bytes or dict safely.
     - Ensure `/api/v2/nowpayments-ipn` in `web/routers/payments.py` unpacks the tuple, verifies order status is `pending`, completes order, and atomically updates wallet via `update_wallet`.
     - Add webhook replay cache to ensure repeated IPN notifications for already completed orders are handled idempotently (return 200 OK without re-crediting wallet).

---

## 3. Caveats

1. **Network Connectivity & Rate Limits**: Public RPC endpoints (`api.trongrid.io`, `polygon-rpc.com`) may have rate limits under heavy traffic. The implementation must include configurable RPC URLs (`TRONGRID_API_URL`, `POLYGON_RPC_URL`, `TON_API_URL`) and timeout handling (e.g. 5-10s timeout with graceful error return rather than crashing).
2. **Decimal Precision**: USDT on Tron (TRC20) and Polygon (ERC20) uses 6 decimals (`1 USDT = 1,000,000 sun/units`). Polygon native POL/MATIC and ETH use 18 decimals (`10^18 wei`). TON uses 9 decimals (`10^9 nanotons`). The parser must handle decimal conversions accurately.
3. **Database Dialect Compatibility**: Schema updates must run cleanly across both SQLite (local development / tests) and PostgreSQL (production Neon serverless) through `core/pg_sqlite_shim.py`.

---

## 4. Conclusion & Worker Implementation Strategy

The Worker should implement the following step-by-step changes:

### Step 1: Create `payments/crypto_verifier.py` (`OnChainVerifier`)
Create `payments/crypto_verifier.py` implementing:
```python
class OnChainVerifier:
    def verify_tx(
        self,
        network: str,
        tx_hash: str,
        expected_amount: float,
        recipient: str = "",
        user_id: str = "",
        order_id: str = ""
    ) -> tuple[bool, str]:
        ...
```
- Validate network (`trc20` / `tron`, `polygon` / `matic`, `ton`).
- Check double-spend / replay cache in `crypto_processed_txs` & `wallet_transactions`.
- Check if running in test mode / mock hash (`mock_tron_*`, `mock_poly_*`, `mock_ton_*`).
- For Tron: Query TronGrid API (`/wallet/gettransactioninfobyid` & `/wallet/getnowblock`), verify contract execution success, destination address, transferred amount, and confirmations >= 12.
- For Polygon: Query Polygon RPC (`eth_getTransactionByHash`, `eth_getTransactionReceipt`, `eth_blockNumber`), verify receipt status `0x1`, decode transfer calldata, verify recipient & amount, and confirmations >= 12.
- For TON: Query TON API endpoint, verify transaction status, recipient, and amount.
- Atomically insert verified tx into `crypto_processed_txs`.

### Step 2: Upgrade `payments/nowpayments.py` & `payments/gateway.py`
1. In `payments/nowpayments.py`:
   - Expand supported currency mapping for `usdttrc20`, `usdtmatic`, `usdcmatic`, `usdctrc20`, `ton`, `usdton`.
   - Update `verify_ipn(ipn_data: dict, headers: dict) -> bool` with canonical compact JSON key sorting `json.dumps(sorted_dict, separators=(',', ':'))`.
   - Fix `process_ipn_callback(body: bytes | str | dict, headers: dict) -> tuple[bool, str, float, str]` to accept raw body, verify signature, prevent replay, and return `(success, order_id, actually_paid, message)`.
2. In `payments/gateway.py`:
   - Expand `self.wallets` with `usdt_trc20`, `usdt_polygon`, `usdc_polygon`, `ton`, `btc`, `eth`, `ltc`.
   - Update `create_invoice()` to pass currency and network parameters.
   - Update `get_payment_addresses()` to return all multi-chain sovereign addresses with $0 merchant fees.
3. In `payments/__init__.py`:
   - Update `get_payment_addresses()` to include TRC20, Polygon, TON, BTC, ETH, LTC.
   - Update `record_payment()` to support all multi-chain currency codes.

### Step 3: Upgrade Database Schema & `core/stripe_crypto.py`
1. Ensure table `crypto_processed_txs` is initialized on startup:
   ```sql
   CREATE TABLE IF NOT EXISTS crypto_processed_txs (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       tx_hash TEXT UNIQUE NOT NULL,
       network TEXT NOT NULL,
       amount_usd REAL NOT NULL,
       recipient TEXT NOT NULL,
       user_id TEXT,
       order_id TEXT,
       confirmations INTEGER DEFAULT 12,
       verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   CREATE UNIQUE INDEX IF NOT EXISTS idx_crypto_tx_hash ON crypto_processed_txs(tx_hash);
   ```
2. Update `core/stripe_crypto.py`:
   - Replace mock verification with calls to `OnChainVerifier` for TRC20, Polygon, and TON.
   - Link with atomic wallet ledger `update_wallet`.

### Step 4: Upgrade `web/routers/payments.py`
1. Update `/api/v2/nowpayments-ipn` to handle `process_ipn_callback` return tuple safely:
   - Verify HMAC SHA-512 signature.
   - Check if order is already completed (idempotency / replay protection).
   - If pending: update order status to `completed` and call `update_wallet(conn, user_id, amount_usd, description, "deposit")`.
   - Return appropriate JSON response and status codes (200, 400, 403).
2. Update `/api/payments/crypto/verify`:
   - Route to `OnChainVerifier.verify_tx()`.
   - On success: credit user wallet and mark order completed atomically.
   - Return detailed verification status, confirmations count, and new balance.
3. Update `/api/v2/nowpayments/create-invoice` and `/wallet/deposit/create` to support multi-chain currency selections (`USDT-TRC20`, `USDT-POLYGON`, `USDC-POLYGON`, `TON`).

### Step 5: Create Comprehensive Test Suite
Create `tests/test_crypto_payments_m4.py` covering:
1. Multi-chain invoice creation (TRC20, Polygon, TON) with $0 merchant fees.
2. HMAC SHA-512 IPN signature verification (valid signature, invalid signature, missing header, tampered payload).
3. IPN callback idempotency and replay protection.
4. On-chain RPC verification for TronGrid, Polygon, and TON (mocking transport responses, validating 12+ confirmations, verifying recipient address and amount).
5. Double-spend rejection (attempting to verify identical transaction hash twice).
6. Atomic wallet crediting and transaction logging.

---

## 5. Verification Method

### Test Execution Commands
1. Run crypto payments test suite:
   ```bash
   pytest tests/test_crypto_payments_m4.py -v
   ```
2. Run related billing & payments tests:
   ```bash
   pytest tests/test_gcc_billing.py -v
   ```
3. Run Python import verification:
   ```bash
   python -c "import payments.crypto_verifier, payments.nowpayments, payments.gateway, core.stripe_crypto; print('Crypto payments modules verified successfully')"
   ```

### Files to Inspect
- `payments/crypto_verifier.py`
- `payments/nowpayments.py`
- `payments/gateway.py`
- `payments/__init__.py`
- `core/stripe_crypto.py`
- `web/routers/payments.py`
- `tests/test_crypto_payments_m4.py`

### Invalidation Conditions
- An IPN callback with a valid HMAC signature fails to verify or crashes the endpoint.
- An unverified or tampered IPN payload is accepted.
- A duplicate or previously processed transaction hash is accepted a second time (double-spend / replay bug).
- A transaction with fewer than 12 confirmations is accepted as confirmed.
- Transaction sent to an external/foreign recipient address is credited to our system.
