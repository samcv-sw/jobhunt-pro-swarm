# Adversarial Challenge Report — Milestone 1: Cloudflare Pages Deployment

**Overall risk assessment**: HIGH

---

## Challenge Summary

We performed adversarial analysis and constructed stress-test scenarios to challenge the security model and protocol mechanics introduced in Milestone 1. We confirmed that the CORS dynamic origin matching regex allows full cross-origin domain bypass, and that the Cloudflare Pages Function Proxy script crashes on WebSocket upgrade handshakes due to protocol misuse and case-sensitive header matching.

---

## Challenges

### [Critical] Challenge 1: CORS Dynamic Origin Regex Bypass
- **Assumption challenged**: The regex pattern `r"https?://.*\.pages\.dev"` securely isolates origin access to Cloudflare Pages deployment subdomains.
- **Attack scenario**: An attacker deploys a malicious site on `https://attacker.pages.dev.com` or `http://localhost.attacker.com`. Because Starlette's `CORSMiddleware` performs dynamic matching via `re.match` (prefix matching) and the options lack trailing anchors (`$`), the check passes because the prefix portion matches the allowed patterns.
- **Blast radius**: High. Attackers can execute CSRF attacks, read sensitive database/session information, or perform API transactions on behalf of users.
- **Mitigation**: Change the CORS origin validation regex in `web/app_v2.py` to enforce absolute start and end anchors for each alternation:
  ```python
  allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^chrome-extension://[a-zA-Z0-9_-]+$|^https?://[a-zA-Z0-9-]+\.pages\.dev$|^https?://[a-zA-Z0-9-]+\.koyeb\.app$"
  ```

### [High] Challenge 2: WebSocket Proxy Protocol Replacement Crash
- **Assumption challenged**: Replaced scheme (`ws://` / `wss://`) is valid for standard global `fetch()` calls in Workers.
- **Attack scenario**: When a connection upgrade to `/ws/` is requested, the worker substitutes the URL scheme to `ws://` / `wss://` before executing the `fetch()` handler. The runtime throws `TypeError: fetch failed / unknown scheme`, causing a 502 Bad Gateway to be returned.
- **Blast radius**: High for WebSockets. Connection attempts crash immediately at the proxy layer.
- **Mitigation**: Remove the protocol substitution block in `_worker.js`. Standard HTTP/HTTPS schemes should be kept since `fetch` handles the upgrade protocol transition internally when the headers are set.

### [Medium] Challenge 3: Case-Sensitive Header Upgrade Match
- **Assumption challenged**: The client's `Upgrade` header is always lowercase `websocket`.
- **Attack scenario**: Safari or other mobile clients request a WebSocket handshake sending `Upgrade: WebSocket`. The case-sensitive comparison evaluates to `false`, bypassing proxy routing and breaking WebSocket functionality for those browsers.
- **Mitigation**: Case-insensitively parse the `Upgrade` header value using `.toLowerCase()`.

---

## Stress Test Results

- **CORS Regex Suffix Match** → Tested `https://attacker.pages.dev.com` → Result: **True** (Vulnerability Confirmed)
- **CORS Localhost Suffix Match** → Tested `http://localhost.attacker.com` → Result: **True** (Vulnerability Confirmed)
- **Fetch Protocol Compatibility** → Tested `fetch('ws://example.com')` → Result: Throws `TypeError: fetch failed` (Vulnerability Confirmed)
