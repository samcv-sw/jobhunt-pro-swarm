# Project: JobHunt Pro SaaS

## Architecture
JobHunt Pro SaaS is an AI-powered automated recruitment and career acceleration platform featuring:
- **Web Application & REST API**: FastAPI (`web/app_v2.py`, `backend/main.py`) with Jinja2 glassmorphism/RTL templates and Next.js 16 frontend.
- **Database & Storage Layer**: Dual-dialect database architecture (`core/pg_sqlite_shim.py`) with automatic switching between Neon PostgreSQL (with PgBouncer pooling and 280s connection recycling) and local SQLite (`data/jobhunt_saas_v2.db`).
- **Zero-Cost Keep-Alive Resilience**: <5ms zero-DB `/healthz` and `/ping` probes integrated with supervisor ping daemons, Cloudflare Workers cron (`*/4 * * * *`), and GitHub Actions (`*/5 * * * *`).
- **Deliverability & Anti-Spam Shield**: Multi-tier DNS MX caching (Memory -> DB -> DNS/DoH with 80+ pre-warmed enterprise domains), ScamDetector with 300+ regexes and Groq AI fallback, 365-day cooldown deduplication across 4 tables, and strict zero-synthetic email filters.
- **17-Provider LLM Arbitrage & L1 Semantic Cache**: Free-tier provider rotation (Cerebras, Groq, Gemini 2.0 Flash, SambaNova) with sub-1ms rate limit reset parsing, KeyRing LRU, exact SHA-256 caching, and 768-dim embeddings yielding >98.5% gross margin.
- **B2B SDR Recruiter Swarm & Multi-Tenant Platform**: Multi-channel lead discovery (LinkedIn, GitHub, Reddit, HN), isolated tenant campaigns, white-label portals, and harmonized $149 - $499/mo subscription tiers.
- **Multi-Gateway Checkout**: GCC Mada, Apple Pay, Tamara/Tabby BNPL (`web/routers/gcc_billing_router.py`), Telegram Stars (`web/routers/payments.py`), On-Chain USDT across Tron/Polygon/TON (`payments/crypto_verifier.py`), and L402 Lightning Satoshis (`core/x402_lightning_protocol.py`).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Zero-DB Health Sentinels | `/healthz` and `/ping` return in <5ms without database load | M1 | Survey R1 |
| 2 | Neon PgBouncer & Pool Management | Bounded connection pool (1-3 conns), 280s connection recycling, PgBouncer `-pooler` injection | M1 | Survey R1 |
| 3 | Dual-Dialect SQL Transpiler | SQLite <-> PostgreSQL query transpilation and runtime automatic fallback on `OperationalError` | M1 | Survey R1 |
| 4 | Unified `FORCE_SQLITE` Env Handling | Align default in `web/app_v2.py` with `config.py` to prevent accidental shadowing of PostgreSQL | M1 | Survey R1 |
| 5 | Immutable Static Asset Caching | 1-year immutable caching headers (`public, max-age=31536000, immutable`) | M1 | Survey R1 |
| 6 | Live MX Verification & Caching | 3-tier DNS MX caching (Memory -> DB -> DNS/DoH) with 80+ enterprise domains | M2 | Survey R2 |
| 7 | ScamDetector & Fraud Rules | Precompiled regexes, suspicious TLD rejection, salary sanity, and zero-shot AI fallback | M2 | Survey R2 |
| 8 | 365-Day Cooldown Deduplication | Sliding window deduplication across `campaign_emails`, `multi_platform_apps`, `jobs`, `applications` | M2 | Survey R2 |
| 9 | PostgreSQL Schema Introspection Fix | Update `_table_exists` in `check_365_cooldown_dedup` to support PostgreSQL `information_schema.tables` | M2 | Survey R2 |
| 10 | Zero Synthetic Email Filter | Reject `careers-[HEX]@...`, `test@...`, and resolve prefix collision in `continuous_dispatcher.py` | M2 | Survey R2 |
| 11 | 17-Provider LLM Arbitrage & L1 Cache | Multi-provider rotation with KeyRing LRU, sub-1ms reset parsing, and semantic cache with placeholder guard | M2 | Survey R2 |
| 12 | Spintax Engine & Jaccard Diversity | Recursive spintax expansion and pairwise Jaccard distance >= 0.25 anti-fingerprinting | M2 | Survey R2 |
| 13 | Viral Growth Funnels | Free ATS Resume Roast (`/roast`), Golden Ticket Hongbao referral loops (`/redeem`), Telegram Mini App | M2 | Survey R2 |
| 14 | Native Telegram Stars (XTR) Checkout | Telegram Stars invoice generation (`createInvoiceLink`) for 1-click in-app checkout | M2 | Survey R2 |
| 15 | B2B SDR Recruiter Lead Swarm | Multi-channel lead discovery (LinkedIn, GitHub, Reddit, HN) with live MX verification | M3 | Survey R3 |
| 16 | Harmonized Recruiter Tiers | $149 Starter, $299 Agency Swarm, $499 Enterprise Sovereign tiers across endpoints | M3 | Survey R3 |
| 17 | Multi-Tenant Recruiter Isolation | Isolated tenant campaigns, custom subdomains, dedicated SMTP pools, and ATS candidate search | M3 | Survey R3 |
| 18 | Multi-Gateway Instant Provisioning | GCC Mada, Apple Pay, Telegram Stars, On-Chain USDT (Tron/Polygon/TON), and L402 Lightning Satoshis | M3 | Survey R3 |
| 19 | Test Suite Asyncio & Mount Fixes | Resolve fixture scope in `test_telegram_miniapp.py` and router mounts across test files | M4 | Survey R3 |
| 20 | Test Suite Concurrency & Mock Hardening | WAL mode pragmas in stress test fixtures and network mocks for external egress in edge tests | M4 | Survey R3 |
| 21 | 100% Test Pass Rate Guarantee | Full 2,026-test suite execution and clean verification | M4 | Survey R3 |
| 22 | Full E2E Test Suite Execution | Pass 100% of Tiers 1-4 E2E test suite | M5 | Project Pattern |
| 23 | Tier 5 Adversarial Coverage Hardening | White-box stress testing, gap elimination, and forensic integrity audit | M5 | Project Pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | R1: Deployment & DB Resilience | Features 1–5 (Zero-DB health, Neon pooling, SQL transpiler, `FORCE_SQLITE` fix, static cache) | none | **DONE** |
| M2 | R2: Deliverability, AI & Spintax | Features 6–14 (Live MX, ScamDetector, 365-day dedup, Postgres fix, anti-synthetic, LLM pool, Spintax, Viral hooks, Telegram Stars) | M1 | **DONE** |
| M3 | R3: B2B Swarm, Tiers & Gateways | Features 15–18 (SDR swarm, $149-$499 tiers, multi-tenant isolation, multi-gateway checkout) | M1, M2 | **DONE** |
| M4 | Test Suite Hardening & 100% Pass | Features 19–21 (Asyncio fixtures, router mounts, WAL pragmas, network mocks, full 2,026 test pass) | M1, M2, M3 | **DONE** |
| M5 | Final E2E Pass & Tier 5 Hardening | Features 22–23 (Pass 100% E2E test suite, Challenger Tier 5 hardening, Forensic Integrity Audit) | M4 | **DONE** |

## Interface Contracts
### `core/email_verifier.py` ↔ `backend/routers/*.py` & `core/continuous_dispatcher.py`
- `is_deliverable_email(email: str) -> bool`
  - Returns `True` only if email passes syntax validation, typo checks, suppression check, anti-synthetic regexes, and has valid DNS MX / DoH records.
- `check_365_cooldown_dedup(user_id: str, email: str, db_path: Optional[str] = None) -> bool`
  - Returns `True` if email was contacted within 365 days in `campaign_emails`, `multi_platform_apps`, `jobs`, or `applications`. Compatible with both SQLite and PostgreSQL.

### `core/pg_sqlite_shim.py` ↔ `backend/database.py` & `web/app_v2.py`
- `convert_sql(sql: str) -> str`
  - Transpiles SQLite SQL to PostgreSQL syntax (placeholders, date arithmetic, conflict clauses, returning IDs).
- `get_db_connection(db_path: Optional[str] = None)`
  - Returns thread-safe connection with Neon PgBouncer pooling, automatic 280s recycling, and SQLite fallback on `OperationalError`.

### `backend/routers/b2b_recruiter_swarm.py` ↔ `services/tenant_service.py` & Frontend
- `GET /api/b2b-recruiter/subscriptions/tiers`
  - Returns standardized tiers:
    - Starter: `$149/mo`, 50 unlocks, 100 SDR credits
    - Agency Swarm: `$299/mo`, 250 unlocks, 500 SDR credits, 3 seats
    - Enterprise Sovereign: `$499/mo`, unlimited unlocks, 1,500 SDR credits, white-label

## Code Layout
- `web/app_v2.py`: Main FastAPI application, middleware, and route registrations.
- `backend/main.py`: REST API backend and microservice entry points.
- `backend/routers/`: Domain routers (`b2b_recruiter_swarm.py`, `ai_sdr_outreach.py`, `multi_tenant_portal.py`, `telegram_app.py`).
- `web/routers/`: Web endpoints (`gcc_billing_router.py`, `payments.py`, `roast.py`, `growth.py`, `tenants.py`).
- `core/`: Core shared libraries (`pg_sqlite_shim.py`, `email_verifier.py`, `scam_detector.py`, `spintax_engine.py`, `llm_provider_pool.py`, `semantic_cache.py`, `swarm_leads.py`, `multi_tenant.py`, `gcc_unified_checkout.py`, `x402_lightning_protocol.py`).
- `payments/`: Payment processors (`crypto_verifier.py`, `nowpayments.py`).
- `telegram_miniapp/`: Static Telegram Mini App frontend.
- `frontend/`: Next.js 16 frontend.
- `tests/`: 2,026 pytest cases across 152+ test files.
