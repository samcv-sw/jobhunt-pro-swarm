# BRIEFING — 2026-08-14T12:38:00Z

## Mission
Investigate codebase for M4 Features 14, 15, 16 (Crypto Invoicing, On-chain double-spend/replay verification with RPC & 12+ confirmations, HMAC SHA-512 IPN webhook security) and produce a comprehensive Worker implementation handoff.

## 🔒 My Identity
- Archetype: explorer
- Roles: read-only investigation, codebase analysis, architectural gap analysis, synthesis
- Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m4_1
- Original parent: 1a88d940-650d-405f-a7dd-88b2f8b9a304
- Milestone: M4 (Iteration 1)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement directly
- Strictly follow token economy guidelines
- Output comprehensive 5-component handoff report

## Current Parent
- Conversation ID: 1a88d940-650d-405f-a7dd-88b2f8b9a304
- Updated: 2026-08-14T12:38:00Z

## Investigation State
- **Explored paths**:
  - `payments/nowpayments.py`, `payments/gateway.py`, `payments/__init__.py`
  - `web/routers/payments.py`, `web/app_v2.py`, `web/shared.py`, `web/templates/wallet.html`
  - `core/stripe_crypto.py`, `core/gcc_billing.py`, `infra/init.sql`, `config.py`
  - `olympus_webhook/src/index.js`, `cloudflare/payment_queue_worker.js`
- **Key findings**:
  - Feature 14: Multi-chain support for USDT/USDC across TRC20, Polygon, TON with $0 merchant fees is partially mocked/stubbed and missing explicit multi-chain currency mapping & sovereign wallet fallbacks.
  - Feature 15: `payments/crypto_verifier.py` (`OnChainVerifier`) is missing. Existing `core/stripe_crypto.py` contains stubs without real TronGrid/Polygon/TON RPC queries, 12+ confirmations check, recipient address check, or replay cache.
  - Feature 16: `payments/nowpayments.py` HMAC SHA-512 signature computation uses `json.dumps(ipn_data, sort_keys=True)` instead of canonical compact JSON (`separators=(',', ':')`), and `process_ipn_callback` returns 1 boolean while `web/routers/payments.py` unpacks 3 values (`success, order_id, amount_usd`), which causes a runtime crash on IPN callback.
- **Unexplored areas**: None for Features 14, 15, 16.

## Key Decisions Made
- Outlined complete architectural specification for `payments/crypto_verifier.py`, `payments/nowpayments.py`, `payments/gateway.py`, `web/routers/payments.py`, `config.py`, and `infra/init.sql`.

## Artifact Index
- DISPATCH.md — incoming dispatch records
- BRIEFING.md — situational awareness
- progress.md — liveness heartbeat
- handoff.md — final analysis report
