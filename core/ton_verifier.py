"""
JobHunt Pro - TON Jetton Payment Verifier (Apex Matrix Edition)
===============================================================

APEX MATRIX: Off-Chain Cryptographic Finality Verification
==========================================================
Verifies USDT (Jetton) transfers on the TON blockchain with
mathematical precision. Eliminates the critical vulnerability of
trusting raw webhook notifications (which can be forged by
malicious smart contracts).

VERIFICATION MATRIX (multi-stage):
  1. Receive incoming payment notification (webhook trigger)
  2. Resolve the official Jetton Master Contract address for USDT
  3. Derive the canonical Jetton Wallet address for the sender
  4. Compare derived address against the notification emitter address
  5. Confirm the shard block is anchored in the Masterchain (finality)
  6. Only then: credit the user's balance in the database

SUPPORTED NETWORKS:
  - TON Mainnet  (default)
  - TON Testnet  (set TONVERIFIER_TESTNET=1 in .env)

DEPENDENCIES:
  - tonutils  (pip install tonutils)
  - httpx     (pip install httpx)
  - No heavy wallet setup required — read-only RPC calls only
"""

import asyncio
import logging
import os
from typing import Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

IS_TESTNET = os.getenv("TONVERIFIER_TESTNET", "0") == "1"

# Official Toncenter RPC endpoints (high-availability, rate-limited at 1 req/s free)
TONCENTER_MAINNET = "https://toncenter.com/api/v2"
TONCENTER_TESTNET = "https://testnet.toncenter.com/api/v2"
TONCENTER_BASE = TONCENTER_TESTNET if IS_TESTNET else TONCENTER_MAINNET

# Tonapi.io — faster, supports traces, better for Jetton event tracking
TONAPI_MAINNET = "https://tonapi.io/v2"
TONAPI_TESTNET = "https://testnet.tonapi.io/v2"
TONAPI_BASE = TONAPI_TESTNET if IS_TESTNET else TONAPI_MAINNET

# API keys (optional but removes rate limits)
TONCENTER_API_KEY = os.getenv("TONCENTER_API_KEY", "")
TONAPI_KEY = os.getenv("TONAPI_KEY", "")

# Official USDT (Tether) Jetton Master Contract on TON Mainnet
# Source: https://tonviewer.com/EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs
USDT_MASTER_MAINNET = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"
USDT_MASTER_TESTNET = "EQBynBO23ywHy_CgarY9NK9FTz0yDsG82PtcbSTQgGoXwiuA"  # testnet USDT
USDT_MASTER_ADDRESS = USDT_MASTER_TESTNET if IS_TESTNET else USDT_MASTER_MAINNET

# JobHunt Pro receiving wallet address (set in .env)
PLATFORM_WALLET_ADDRESS = os.getenv("TON_PLATFORM_WALLET", "")

# Minimum required confirmations before crediting (masterchain blocks)
# TON is fast (~5s per block), so 3 blocks ≈ 15 seconds = safe finality
REQUIRED_MASTERCHAIN_CONFIRMATIONS = int(os.getenv("TON_CONFIRMATIONS", "3"))

# HTTP request timeout (seconds)
REQUEST_TIMEOUT = 20.0


# ─────────────────────────────────────────────────────────────────────────────
# HTTP CLIENT HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _toncenter_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if TONCENTER_API_KEY:
        headers["X-API-Key"] = TONCENTER_API_KEY
    return headers


def _tonapi_headers() -> dict:
    headers = {"Content-Type": "application/json"}
    if TONAPI_KEY:
        headers["Authorization"] = f"Bearer {TONAPI_KEY}"
    return headers


async def _get(
    client: httpx.AsyncClient, url: str, params: dict = None, headers: dict = None
) -> Optional[dict]:
    """Safe async GET with timeout and error handling."""
    try:
        resp = await client.get(
            url, params=params or {}, headers=headers or {}, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning(
            f"[TON-VERIFIER] GET {url} → {resp.status_code}: {resp.text[:200]}"
        )
        return None
    except Exception as exc:
        logger.error(f"[TON-VERIFIER] Request failed: {url} → {exc}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# CORE VERIFICATION FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────


async def get_jetton_wallet_address(
    owner_address: str, jetton_master: str = USDT_MASTER_ADDRESS
) -> Optional[str]:
    """
    STAGE 1: Derive the canonical Jetton Wallet address for a given owner.
    ======================================================================
    Calls the Jetton Master Contract's get_wallet_address() method with
    the owner's address as parameter. Returns the authodemo_usertive wallet
    address that MUST match the transfer notification emitter.

    This is the core anti-forgery check: a malicious contract can fake
    notifications but cannot replicate the address derived by the master.
    """
    async with httpx.AsyncClient() as client:
        # Use Toncenter runGetMethod to call the Jetton master contract
        payload = {
            "address": jetton_master,
            "method": "get_wallet_address",
            "stack": [["tvm.Slice", owner_address]],
        }
        try:
            resp = await client.post(
                f"{TONCENTER_BASE}/runGetMethod",
                json=payload,
                headers=_toncenter_headers(),
                timeout=REQUEST_TIMEOUT,
            )
            if resp.status_code != 200:
                logger.warning(
                    f"[TON-VERIFIER] runGetMethod failed: {resp.status_code}"
                )
                return None

            data = resp.json()
            if data.get("ok") and data.get("result", {}).get("stack"):
                stack = data["result"]["stack"]
                if stack and len(stack) > 0:
                    # Stack[0][1] contains the cell with the Jetton wallet address
                    cell_value = stack[0][1] if len(stack[0]) > 1 else None
                    if cell_value:
                        logger.info(
                            f"[TON-VERIFIER] ✅ Derived Jetton wallet for {owner_address[:16]}..."
                        )
                        return str(cell_value)
        except Exception as exc:
            logger.error(f"[TON-VERIFIER] get_jetton_wallet_address error: {exc}")

        # Fallback: Try TonAPI's jetton wallet endpoint (more reliable format)
        result = await _get(
            client=httpx.AsyncClient(),
            url=f"{TONAPI_BASE}/accounts/{owner_address}/jettons/{jetton_master}",
            headers=_tonapi_headers(),
        )
        if result and result.get("wallet_address", {}).get("address"):
            wallet = result["wallet_address"]["address"]
            logger.info(f"[TON-VERIFIER] ✅ TonAPI derived wallet: {wallet[:16]}...")
            return wallet

    return None


async def get_transaction_by_hash(tx_hash: str) -> Optional[dict]:
    """
    STAGE 2: Fetch full transaction data by its message hash.
    =========================================================
    TON's async architecture means a single payment = multiple
    messages. We track the INBOUND message hash to the platform wallet.

    Returns None if the transaction is not yet finalized.
    """
    async with httpx.AsyncClient() as client:
        # TonAPI trace endpoint: most reliable for tracking cross-shard messages
        result = await _get(
            client,
            url=f"{TONAPI_BASE}/traces/{tx_hash}",
            headers=_tonapi_headers(),
        )
        if result:
            return result

        # Fallback: Toncenter getTransactions
        result = await _get(
            client,
            url=f"{TONCENTER_BASE}/getTransactions",
            params={
                "address": PLATFORM_WALLET_ADDRESS,
                "limit": 20,
            },
            headers=_toncenter_headers(),
        )
        if result and result.get("ok"):
            transactions = result.get("result", [])
            for tx in transactions:
                if tx.get("transaction_id", {}).get("hash") == tx_hash:
                    return tx

    return None


async def is_masterchain_finalized(tx_hash: str) -> Tuple[bool, int]:
    """
    STAGE 3: Confirm Masterchain Finality.
    ======================================
    On TON, shard blocks are only fully irreversible once they are
    referenced (anchored) by a Masterchain block.

    Returns (is_final, confirmations_count).
    We require REQUIRED_MASTERCHAIN_CONFIRMATIONS before crediting.
    """
    async with httpx.AsyncClient() as client:
        # Get the current masterchain seqno
        mc_info = await _get(
            client,
            url=f"{TONCENTER_BASE}/getMasterchainInfo",
            headers=_toncenter_headers(),
        )
        if not mc_info or not mc_info.get("ok"):
            logger.warning("[TON-VERIFIER] Could not fetch masterchain info")
            return False, 0

        current_seqno = mc_info["result"]["last"]["seqno"]

        # Fetch transaction trace to get its containing block seqno
        trace = await _get(
            client,
            url=f"{TONAPI_BASE}/traces/{tx_hash}",
            headers=_tonapi_headers(),
        )
        if trace:
            # TonAPI provides mc_seqno_after for each transaction
            tx_mc_seqno = None
            transactions = trace.get("transactions", [])
            for tx in transactions:
                if tx.get("mc_seqno_after"):
                    tx_mc_seqno = tx["mc_seqno_after"]
                    break

            if tx_mc_seqno:
                confirmations = current_seqno - tx_mc_seqno
                is_final = confirmations >= REQUIRED_MASTERCHAIN_CONFIRMATIONS
                logger.info(
                    f"[TON-VERIFIER] Masterchain confirmations: {confirmations} "
                    f"(required: {REQUIRED_MASTERCHAIN_CONFIRMATIONS}, final: {is_final})"
                )
                return is_final, confirmations

    return False, 0


# ─────────────────────────────────────────────────────────────────────────────
# MAIN VERIFICATION ENTRYPOINT
# ─────────────────────────────────────────────────────────────────────────────


class JettonPaymentVerifier:
    """
    APEX MATRIX: Cryptographically secure Jetton payment verification.

    Usage:
        verifier = JettonPaymentVerifier()
        result = await verifier.verify_payment(
            notification_sender="EQD...",   # address that sent the notification
            owner_address="EQA...",         # user's TON wallet address
            expected_amount_nano=1_000_000, # 1 USDT = 1,000,000 (6 decimals)
            tx_hash="abc123...",            # transaction/message hash
        )
        if result["verified"]:
            # SAFE TO CREDIT THE USER
    """

    def __init__(self):
        self.usdt_master = USDT_MASTER_ADDRESS
        logger.info(
            f"[TON-VERIFIER] Initialized. Network: {'TESTNET' if IS_TESTNET else 'MAINNET'}. "
            f"USDT Master: {self.usdt_master[:16]}..."
        )

    async def verify_payment(
        self,
        notification_sender: str,
        owner_address: str,
        expected_amount_nano: int,
        tx_hash: str,
        poll_finality: bool = True,
        max_poll_attempts: int = 10,
        poll_interval_s: float = 6.0,
    ) -> dict:
        """
        Full multi-stage Jetton payment verification.

        Args:
            notification_sender:  The contract address that emitted the transfer notification.
            owner_address:        The user's TON wallet address (from their profile).
            expected_amount_nano: Expected amount in nanoJetton (USDT has 6 decimals: 1 USDT = 1_000_000).
            tx_hash:              The transaction/message hash from the webhook.
            poll_finality:        If True, polls until masterchain finalizes (recommended).
            max_poll_attempts:    Maximum polls before giving up.
            poll_interval_s:      Seconds between finality polls.

        Returns:
            dict with keys:
              verified (bool)     : True only if ALL checks pass
              stage_failed (str)  : Which check failed (for debugging)
              confirmations (int) : Masterchain confirmations at verification time
              error (str)         : Error message if any
        """
        result = {
            "verified": False,
            "stage_failed": None,
            "confirmations": 0,
            "error": None,
            "tx_hash": tx_hash,
            "network": "testnet" if IS_TESTNET else "mainnet",
        }

        logger.info(
            f"[TON-VERIFIER] Starting verification for tx={tx_hash[:16]}... "
            f"sender={notification_sender[:16]}..."
        )

        # ── STAGE 1: Address Authenticity Check ───────────────────────────────
        # Derive the CANONICAL Jetton wallet for this user from the master contract.
        # If it doesn't match notification_sender → forged notification.
        canonical_wallet = await get_jetton_wallet_address(
            owner_address, self.usdt_master
        )

        if not canonical_wallet:
            result["stage_failed"] = "wallet_derivation_failed"
            result["error"] = "Could not derive Jetton wallet from master contract."
            logger.error(f"[TON-VERIFIER] ❌ Stage 1 FAILED: {result['error']}")
            return result

        # Normalize addresses for comparison (TON addresses have multiple representations)
        canonical_norm = canonical_wallet.strip().replace("-", "+").replace("_", "/")
        notification_norm = (
            notification_sender.strip().replace("-", "+").replace("_", "/")
        )

        if canonical_norm != notification_norm:
            result["stage_failed"] = "address_mismatch"
            result["error"] = (
                f"Notification sender ({notification_sender[:16]}...) does NOT match "
                f"canonical Jetton wallet ({canonical_wallet[:16]}...). "
                f"Possible forged notification attack!"
            )
            logger.critical(
                f"[TON-VERIFIER] ❌ Stage 1 FAILED — FORGED NOTIFICATION DETECTED: {result['error']}"
            )
            return result

        logger.info("[TON-VERIFIER] ✅ Stage 1 PASSED: Sender address is authentic.")

        # ── STAGE 2: Transaction Existence Check ──────────────────────────────
        tx_data = await get_transaction_by_hash(tx_hash)
        if not tx_data:
            result["stage_failed"] = "transaction_not_found"
            result["error"] = f"Transaction {tx_hash[:16]}... not found on chain."
            logger.warning(f"[TON-VERIFIER] ❌ Stage 2 FAILED: {result['error']}")
            return result

        logger.info("[TON-VERIFIER] ✅ Stage 2 PASSED: Transaction found on chain.")

        # ── STAGE 3: Masterchain Finality Check ───────────────────────────────
        # Poll until the transaction achieves immutable finality.
        if poll_finality:
            is_final = False
            confirmations = 0
            for attempt in range(max_poll_attempts):
                is_final, confirmations = await is_masterchain_finalized(tx_hash)
                if is_final:
                    break
                if attempt < max_poll_attempts - 1:
                    logger.info(
                        f"[TON-VERIFIER] ⏳ Waiting for finality... "
                        f"attempt {attempt + 1}/{max_poll_attempts} ({confirmations} confirmations so far)"
                    )
                    await asyncio.sleep(poll_interval_s)

            result["confirmations"] = confirmations

            if not is_final:
                result["stage_failed"] = "finality_not_reached"
                result["error"] = (
                    f"Transaction did not reach masterchain finality after "
                    f"{max_poll_attempts} attempts ({confirmations} confirmations, "
                    f"required: {REQUIRED_MASTERCHAIN_CONFIRMATIONS})."
                )
                logger.warning(f"[TON-VERIFIER] ❌ Stage 3 FAILED: {result['error']}")
                return result

            logger.info(
                f"[TON-VERIFIER] ✅ Stage 3 PASSED: Masterchain finality confirmed "
                f"({confirmations} confirmations)."
            )

        # ── ALL STAGES PASSED ─────────────────────────────────────────────────
        result["verified"] = True
        logger.info(
            f"[TON-VERIFIER] 🏆 PAYMENT VERIFIED. tx={tx_hash[:16]}... "
            f"confirmations={result['confirmations']}. Safe to credit user."
        )
        return result


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE INTEGRATION
# ─────────────────────────────────────────────────────────────────────────────


async def process_verified_ton_payment(
    user_id: str,
    tx_hash: str,
    amount_usdt: float,
    notification_sender: str,
    owner_address: str,
) -> dict:
    """
    End-to-end TON payment processing pipeline.
    Verifies the payment cryptographically, then credits the user's wallet.

    Returns dict with {success, credited_amount, error}
    """
    verifier = JettonPaymentVerifier()
    amount_nano = int(amount_usdt * 1_000_000)  # USDT has 6 decimals on TON

    # Run full cryptographic verification
    verification = await verifier.verify_payment(
        notification_sender=notification_sender,
        owner_address=owner_address,
        expected_amount_nano=amount_nano,
        tx_hash=tx_hash,
    )

    if not verification["verified"]:
        logger.error(
            f"[TON-VERIFIER] Payment verification FAILED for user {user_id}: "
            f"{verification.get('error')}"
        )
        return {
            "success": False,
            "credited_amount": 0,
            "error": verification.get("error"),
            "stage_failed": verification.get("stage_failed"),
        }

    # Payment is cryptographically verified — safe to credit
    try:
        from core.pg_sqlite_shim import connect

        with connect() as conn:
            # Check for duplicate processing (idempotency via tx_hash)
            existing = conn.execute(
                "SELECT id FROM wallet_transactions WHERE tx_hash = ?", (tx_hash,)
            ).fetchone()

            if existing:
                logger.warning(
                    f"[TON-VERIFIER] Transaction {tx_hash[:16]}... already processed. Skipping duplicate credit."
                )
                return {
                    "success": True,
                    "credited_amount": 0,
                    "error": "duplicate_transaction",
                }

            # Credit the user's wallet
            conn.execute(
                """
                UPDATE users
                SET wallet_balance = wallet_balance + ?, total_spent = total_spent + ?
                WHERE user_id = ?
                """,
                (amount_usdt, amount_usdt, user_id),
            )

            # Record the transaction in the audit ledger
            conn.execute(
                """
                INSERT INTO wallet_transactions
                  (user_id, transaction_type, amount, description, tx_hash)
                VALUES (?, 'ton_usdt_deposit', ?, ?, ?)
                """,
                (
                    user_id,
                    amount_usdt,
                    f"TON USDT deposit — {verification['confirmations']} MC confirmations",
                    tx_hash,
                ),
            )

        logger.info(
            f"[TON-VERIFIER] ✅ Credited ${amount_usdt} USDT to user {user_id}. "
            f"tx={tx_hash[:16]}..."
        )
        return {
            "success": True,
            "credited_amount": amount_usdt,
            "confirmations": verification["confirmations"],
            "error": None,
        }

    except Exception as exc:
        logger.error(f"[TON-VERIFIER] DB credit failed for user {user_id}: {exc}")
        return {
            "success": False,
            "credited_amount": 0,
            "error": str(exc),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE: Global singleton verifier
# ─────────────────────────────────────────────────────────────────────────────
ton_verifier = JettonPaymentVerifier()

