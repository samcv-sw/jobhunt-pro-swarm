# E2E Test Infra: JobHunt Pro SaaS

## Test Philosophy
- **Requirement-Driven & Opaque-Box**: Tests exercise the full system from external API, CLI, and HTTP interfaces without assuming internal implementation details.
- **Methodology**: 4-Tier Progressive Testing (Tier 1: Feature Isolation, Tier 2: Boundary & Corner Cases, Tier 3: Pairwise Combinations, Tier 4: Real-World Workloads) followed by Tier 5 Adversarial Coverage Hardening.

## Feature Inventory & Test Matrix
| # | Feature | Requirement Source | Tier 1 (≥5) | Tier 2 (≥5) | Tier 3 (Pairwise) |
|---|---------|-------------------|:-----------:|:-----------:|:-----------------:|
| F1 | Zero-DB Fast Health Probe (`/healthz`, `/ping`) | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| F2 | Neon PgBouncer & SQLite Auto-Fallback | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ |
| F3 | Live MX DNS & DoH Email Verification | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F4 | 365-Day Sliding Cooldown Deduplication | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F5 | Anti-Synthetic Email & ScamDetector | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F6 | 17-Provider LLM Arbitrage & Semantic Cache | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F7 | Recursive Spintax & Jaccard Diversity | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F8 | Viral ATS Roast & Golden Ticket Loops | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F9 | Telegram Stars & Mini App Checkout | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ |
| F10 | B2B SDR Lead Swarm & Discovery | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F11 | Multi-Tenant Recruiter Isolation & Tiers | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |
| F12 | Multi-Gateway (Mada, Apple Pay, USDT, L402) | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ |

## Test Architecture
- **Test Runner**: Pytest (`pytest -q --tb=short`).
- **Test Invocations**:
  - Full Test Suite: `pytest -q --tb=short` (2,026 tests)
  - Core Milestone Verification: `pytest tests/test_b2b_recruiter_swarm.py tests/test_scam_detector.py tests/test_multi_tenant.py tests/test_gcc_billing.py tests/test_x402_lightning_protocol.py tests/test_telegram_miniapp.py tests/test_spintax_engine.py -q`
  - Adversarial Benchmarks: `python tests/stress_deliverability_suite.py` & `python tests/standalone_adversarial_p1_p4_benchmark.py`
- **Pass/Fail Semantics**: 100% exit code 0, 0 unhandled exceptions, zero integrity violations.

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Full Recruiter Cold Outreach Campaign: Lead extraction -> Live MX filter -> 365-day dedup check -> Spintax generation -> Dispatch | F3, F4, F5, F7, F10, F11 | High |
| 2 | High-Concurrency Health Sentinel & Failover: 100 concurrent pings during database failover simulation | F1, F2 | Medium |
| 3 | Viral Lead-to-Customer Funnel: Free ATS Resume Roast -> Lead capture alert -> Telegram Mini App checkout (Stars / USDT) -> Token credit | F8, F9, F12 | High |
| 4 | Multi-Tenant Enterprise Whitelabel & Seat Provisioning: Subdomain creation -> Custom branding -> Member RBAC -> Campaign execution | F10, F11 | High |
| 5 | GCC Cross-Border Payment & ZATCA Invoicing: Mada / Apple Pay checkout -> Webhook verification -> ZATCA QR invoice generation -> Instant activation | F12 | Medium |

## Coverage Thresholds
- Tier 1: ≥ 60 test cases (≥5 per feature across 12 features)
- Tier 2: ≥ 60 test cases (boundary limits, malformed emails, offline DNS, invalid tokens)
- Tier 3: ≥ 25 pairwise combination test cases
- Tier 4: ≥ 5 end-to-end real-world workload scenarios
- Tier 5: White-box adversarial stress tests & zero-gap coverage hardening
