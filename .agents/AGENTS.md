# Multi-Persona Council & AI Context Rules

## Global Constraints
1. **Never use placeholder code** (e.g., `// TODO: implement`). Always provide complete, copy-paste-ready file outputs.
2. **Lazy Loading of Tools**: Use context efficiently. Only load metadata and tools when strictly necessary for the active domain.
3. **No Sycophancy**: Do not blindly agree with the user if their technical request contradicts structural integrity or best practices.
4. **Strict Dispatch & Email Quality Directives (PERMANENT RULE)**:
   - **Zero Synthetic / Demo Emails**: Never generate or allow `careers-[HEX]@...` synthetic emails or truncated domain emails (`[:10]`, `[:15]`).
   - **1-Year Cooldown Deduplication Window**: Deduplication across `campaign_emails`, `jobs`, and `multi_platform_apps` is enforced strictly per user (`user_id`) using a 365-day sliding window (`ce.sent_at >= datetime('now', '-365 days')`). Never scan `campaign_emails` globally without a `user_id` predicate.
   - **Mandatory Live MX & Deliverability Verification**: Every target email MUST pass `is_deliverable_email()` and `ScamDetector` DNS MX checks before selection or dispatch.
   - **Instant Live Auto-Dispatch Pulse**: Visiting `/user-dashboard`, `/sent-emails`, or `/battle-station` MUST trigger an active single-dispatch pulse (`dispatch_single_application(user_id=user_id)`) to ensure candidate metrics and logs update dynamically in real time.
5. **Sovereign MENA & Lebanon Payment Rails Directives (PERMANENT RULE)**:
   - **Zero Stripe Policy**: NEVER suggest, require, or default to Stripe for payments or payouts. Stripe is unsupported in Lebanon.
   - **Supported Payment Engines**:
     1. **NOWPayments**: Direct multi-crypto gateway (USDT TRC20/BEP20, BTC, SOL, ETH) with instant IPN webhook.
     2. **ChangeNOW.io**: Non-custodial instant swap and checkout widget.
     3. **MoonPay**: Direct Card / Apple Pay to Crypto fiat onramp for international clients.
     4. **Redeem Codes & FaKa**: Instant automated digital keys and wallet vouchers.
   - **UI & Checkout Presentation**: All pricing tables, checkout buttons, and upgrade modals must route directly to `/wallet`, `/checkout/crypto`, ChangeNOW, or MoonPay flows without dead-end Stripe prompts.

## Multi-Persona Evaluation Council
For all complex code generation, especially regarding architecture and UI/UX:
1. **Skeptic**: Assume the generated code has hidden bugs or fails to account for edge cases. Identify what is wrong, missing, or overly complex.
2. **Domain Expert**: Review the code from the perspective of a Senior Architect. Are CSS Logical Properties strictly used? Are the typography and cultural colors accurate for the Gulf region?
3. **Adversary**: Construct the strongest argument against the chosen approach. E.g., "This flex layout will break on older browsers" or "This font size is too small for Arabic legibility."
4. **Synthesis Pass**: Combine the initial output with these critiques to produce the final, hardened codebase.

## UI/UX & Layout Directives (Arabic & RTL Focus)
1. **CSS Logical Properties MUST BE USED**:
   - `margin-left` -> `margin-inline-start`
   - `padding-right` -> `padding-inline-end`
   - `left`/`right` -> `inset-inline-start`/`inset-inline-end`
   - `width`/`height` -> `inline-size`/`block-size`
2. **Arabic Typography**:
   - Fonts: `'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif`
   - Min font-size: `14px` (recommended `16px` for readability)
   - Line-height: `1.6` to `2.0`
   - No `letter-spacing` on Arabic text.
3. **Cultural Ergonomics**:
   - Primary action buttons (CTAs) should remain centrally located or naturally positioned for right-handed users on mobile devices, avoiding blind mechanical mirroring.
   - **Colors**: Green for success. Black/Gold for luxury. Blue for trust. Red for strict errors only.
4. **Forms**: All inputs must use `dir="auto"`.
5. **Directional Icons**: Use `transform: scaleX(var(--text-x-direction))` with a `--text-x-direction` variable (`1` for LTR, `-1` for RTL).

---

## ⚡ Token Economy Rules (CRITICAL — Read Every Session)

### Project: JobHunt Pro SaaS
**Stack**: FastAPI (Python) + SQLite/PostgreSQL + Next.js + Jinja2 templates

### 🗺️ Quick Reference — Key Files
| What | Where |
|------|-------|
| Main web app | `web/app_v2.py` |
| Backend REST API | `backend/main.py` |
| Web routers | `web/routers/*.py` |
| Backend routers | `backend/routers/*.py` |
| DB shim | `core/pg_sqlite_shim.py` |
| Config/env | `config.py` |
| Templates | `web/templates/` (70+ Jinja2 files) |
| Frontend | `frontend/` (Next.js 16, TypeScript) |
| Tests | `tests/` (608 pytest cases) |

### ❌ NEVER Read These (Token Wasters)
- `ANTIGRAVITY_STATE_SUMMARY.md` — outdated, 62KB, too large
- `.agents/ORIGINAL_REQUEST.md` — 90KB, historical only
- `.agents/modified_files.txt` — 139KB, git history only
- `.venv/`, `.venv2/`, `node_modules/`, `archive/`, `cache/`
- `*.log`, `*.txt` output files
- `.agents/` subdirectories (145 old agent workspaces)

### ✅ Token-Saving Protocol (Follow Every Time)
1. **Start with `grep_search`** before reading any file
2. **Read only the function/class needed**, not the whole file (use StartLine/EndLine)
3. **Check `.agents/BRIEFING.md`** for task context before starting work
4. **Trust this AGENTS.md** — don't re-read project structure files
5. **Use `list_dir` once per directory**, cache results mentally

### 🔑 Known Patterns (Don't Re-Discover)
- DB queries use `$1/$2` (postgres) auto-translated to `?` via `core/pg_sqlite_shim.py`
- Auth: session cookies + `config.PA_API_TOKEN` for admin routes
- User credits: `users.tokens` column, deduct 1 per AI call in `webhook_bot.py`
- RTL: CSS logical properties only, Cairo/Tajawal fonts
- Tests: run with `.venv\Scripts\activate` then `pytest`

