## 2026-07-22T09:46:06Z
Perform targeted remediation for CORS regex anchoring and Cloudflare Pages Worker WebSocket fetch handling.

Your working directory is `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_remediation`.

### Target Fixes:
1. **`web/app_v2.py`**:
   - Update `CORSMiddleware` `allow_origin_regex` to strictly anchored regex:
     `r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^chrome-extension://[a-z]+$|^https?://[a-zA-Z0-9-]+\.pages\.dev$|^https?://[a-zA-Z0-9-]+\.koyeb\.app$"`
   - Ensure `https://attacker.pages.dev.com` and `http://localhost.attacker.com` fail matching.

2. **`frontend/public/_worker.js`**:
   - Do NOT convert scheme from `http/https` to `ws/wss` before passing to `fetch()`, because `fetch()` in Cloudflare Workers requires `http/https` scheme even for WebSocket upgraded requests.
   - Use case-insensitive `Upgrade` header check: `request.headers.get('Upgrade')?.toLowerCase() === 'websocket'`.

3. Run `pytest tests/test_milestone1_resilience.py` to verify tests pass cleanly. Write handoff summary to `handoff.md` and report back via send_message to parent.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. A Forensic Auditor will independently verify your work.
