# Adversarial Challenge Report — Milestone 1: Cloudflare Pages Deployment

**Overall risk assessment**: HIGH

---

## Challenge Summary

We constructed adversarial test scenarios to challenge the security boundaries and runtime assumptions of the Cloudflare Pages Deployment configurations. We discovered that the CORS regex configuration is critically vulnerable to origin bypass attacks and the WebSocket proxy function is vulnerable to runtime crashes on connection upgrade requests.

---

## Challenges

### [Critical] Challenge 1: CORS Origin Validation Bypass
- **Assumption challenged**: The regex pattern `r"https?://.*\.pages\.dev"` securely limits CORS origins to subdomains under `pages.dev`.
- **Attack scenario**: An attacker registers `attacker.pages.dev.com` or `attackerpages.dev` or builds a domain where `.pages.dev` appears as a prefix path segment. Since Starlette compiles the regex without anchors and evaluates it via prefix matching (`re.match`), it successfully validates the attacker's origin.
- **Blast radius**: High. Attackers can perform cross-origin request forgery (CSRF) or extract sensitive user cookies/session tokens from the backend APIs via standard browser scripts.
- **Mitigation**: Update the CORS allow origin regex to enforce absolute anchors (`^` and `$`) around all options:
  ```python
  allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^chrome-extension://[a-zA-Z0-9_-]+$|^https?://[a-zA-Z0-9-]+\.pages\.dev$|^https?://[a-zA-Z0-9-]+\.koyeb\.app$"
  ```

### [High] Challenge 2: WebSocket Proxy `fetch` Scheme TypeError Crash
- **Assumption challenged**: Changing the target proxy URL's protocol to `ws` or `wss` is correct and required to upgrade WebSocket connections.
- **Attack scenario**: A client initiates a connection to `/ws/` to establish a WebSocket channel. The `_worker.js` script matches the path, sets `isWebSocket = true`, replaces `http` with `ws` in the target URL (resulting in `wss://...`), and calls `fetch(targetUrlStr)`. In both Node.js and Cloudflare Workers, `fetch()` throws a `TypeError: fetch failed / unknown scheme` when passed `ws:` or `wss:` schemes.
- **Blast radius**: Medium-High. The WebSocket proxy crashes completely, returning a 502 Bad Gateway to the client rather than successfully proxying the WebSocket connection.
- **Mitigation**: Remove the protocol replacement block. Keep the URL scheme as `http` or `https` for the `fetch()` call.

### [Medium] Challenge 3: Case-Sensitive Header Upgrade Match
- **Assumption challenged**: All clients and browsers send the `Upgrade` header as lowercase `'websocket'`.
- **Attack scenario**: A client (like Safari or curl) sends `Upgrade: WebSocket` during connection establishment. The check `request.headers.get('Upgrade') === 'websocket'` returns `false`, causing the proxy to treat the request as a normal HTTP request, bypassing the WebSocket handshake and resulting in a handshake failure or connection timeout.
- **Blast radius**: Medium. Intermittent WebSocket handshake failures across Safari browsers and specific mobile clients.
- **Mitigation**: Use `.toLowerCase()` when matching header values.

---

## Stress Test Results

- **CORS Regex Verification** → Tested `https://attacker.pages.dev.com` → Match returned **True** → **FAIL (Vulnerability Confirmed)**
- **CORS Localhost Regex Verification** → Tested `http://localhost.attacker.com` → Match returned **True** → **FAIL (Vulnerability Confirmed)**
- **Fetch Protocol Verification** → Tested `fetch('ws://example.com')` → Throws `TypeError: fetch failed` due to unknown scheme → **FAIL (Vulnerability Confirmed)**
