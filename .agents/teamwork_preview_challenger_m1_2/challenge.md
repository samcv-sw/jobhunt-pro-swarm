# Challenge Report: Cloudflare Pages Deployment Verification (Milestone 1)

## Challenge Summary

**Overall risk assessment**: MEDIUM

Milestone 1: Cloudflare Pages Deployment has been empirically verified. The static frontend route compilation outputs, Cloudflare Pages Worker proxy logic, and CORS configurations were stress-tested and audited. 

While the general compilation, routing, and websocket upgrading logic function correctly and securely, we identified security and correctness concerns regarding wide wildcard CORS permissions, incomplete route proxying, and slashless endpoint failures.

---

## Challenges

### [Medium] Challenge 1: Wildcard Subdomain CORS Exposure (Potential Hijack)

- **Assumption challenged**: Permitting all subdomains under `*.pages.dev` and `*.koyeb.app` for CORS requests is secure for preview and staging deployment.
- **Attack scenario**: Cloudflare Pages (`pages.dev`) and Koyeb (`koyeb.app`) are public PaaS systems. Anyone can register a free account and spin up subdomains (e.g. `malicious-attacker.pages.dev` or `attacker-app.koyeb.app`). Because `web/app_v2.py` specifies `allow_origin_regex=r"https?://.*\.pages\.dev|https?://.*\.koyeb\.app"`, the backend allows cross-origin requests from ANY project hosted on these platforms. 
  If a user is logged in, and their credentials/tokens are transmitted, the attacker's script on `attacker.pages.dev` can make authenticated API requests to the backend and extract their data.
- **Blast radius**: Unauthorized cross-origin reads/writes of sensitive backend data via CORS by any malicious site on pages.dev/koyeb.app.
- **Mitigation**: Tighten the regex in production to permit only specific subdomains (e.g. `https://jobhunt-pro.pages.dev` and local preview patterns like `https://preview-[a-z0-9]+.jobhunt-pro.pages.dev`), rather than a broad platform-wide wildcard.

### [Low] Challenge 2: Incomplete Route Proxying in `_worker.js`

- **Assumption challenged**: All required backend endpoints are grouped under the `['/api/', '/ws/', '/_/pa/', '/scrape', '/health']` paths.
- **Attack scenario**: The backend application (`web/app_v2.py`) registers several routes that do not start with any of the proxy prefixes. Examples include:
  - `/export/applications`
  - `/debug-db`
  - `/pricing_v2`
  - `/refund`
  - `/cookies`
  - `/careers`
  When accessed through the front-facing Cloudflare Pages domain (e.g., `https://pages-domain.com/export/applications`), the request is not matched by `PROXY_PATHS` and falls through to Pages static assets (`env.ASSETS.fetch`), resulting in a `404 Not Found` response because the frontend does not statically export these pages.
- **Blast radius**: Users visiting these functional routes from the frontend domain will experience 404 errors.
- **Mitigation**: Update the `PROXY_PATHS` in `_worker.js` to include all functional backend-rendered endpoints or rewrite them to reside under `/api/`.

### [Low] Challenge 3: Slashless API Routing Failures

- **Assumption challenged**: API calls will always use correct trailing slashes (`/api/`) or complete routes.
- **Attack scenario**: A client or legacy script calls `https://pages-domain.com/api` or `https://pages-domain.com/ws` without the trailing slash. Since the prefix matching is done via `path.startsWith('/api/')` or `path.startsWith('/ws/')`, the route `/api` does not match, and is passed to `env.ASSETS.fetch` which returns a 404 instead of forwarding it to the backend.
- **Blast radius**: Intermittent 404 errors for slashless requests.
- **Mitigation**: Normalize paths in `_worker.js` prior to matching, or check for exact matches without the trailing slash (e.g., `path === '/api' || path.startsWith('/api/')`).

---

## Stress Test Results

We ran empirical tests verifying these behaviors.

| Scenario | Expected Behavior | Actual Behavior | Verdict |
|----------|-------------------|-----------------|---------|
| Request to `/api/v1/jobs` | Forwarded to backend | Correctly forwarded (Host changed to `jhfguf.pythonanywhere.com`) | **PASS** |
| Request to `/api` (slashless) | Forwarded to backend or normalized | Falls back to static assets (results in 404) | **FAIL** (Expected normalization) |
| WebSocket Upgrade `/ws/connect` | Forwarded to `wss://` target | Protocol rewrote to `wss://` | **PASS** |
| CORS Option check for `https://attacker.pages.dev.evil.com` | Blocked | Blocked (returns no Access-Control headers) | **PASS** |
| CORS Option check for `https://attacker.pages.dev` | Blocked or restricted | Allowed (matched by `.*\.pages\.dev`) | **WARNING** (PaaS-wide trust) |
| Request to `/export/applications` | Forwarded to backend | Falls back to static assets (results in 404) | **FAIL** (Route not proxied) |

---

## Unchallenged Areas

- **Production network latency and rate-limiting rules** — Reason not challenged: Operating in `CODE_ONLY` network mode; live Cloudflare edge environments cannot be directly measured.
