# Handoff Report — Security Hardening Challenger

## 1. Observation
I audited the implemented security controls in `backend/main.py` and `web/app_v2.py` and wrote an adversarial test suite (`tests/test_adversarial_security.py`) to stress-test their limits.

### Rate Limiter Code (`backend/main.py`, lines 18–37):
```python
class RateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.history = defaultdict(list)
        self.lock = asyncio.Lock()

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        async with self.lock:
            now = time.time()
            self.history[client_ip] = [t for t in self.history[client_ip] if now - t < self.window_seconds]
            if len(self.history[client_ip]) >= self.requests_limit:
                raise HTTPException(status_code=429, detail="Too many requests. Rate limit exceeded.")
            self.history[client_ip].append(now)
```

### SSRF Protection Blocklist Code (`web/app_v2.py`, lines 9669–9674):
```python
            blocked = ["localhost", "127.0.0.1", "0.0.0.0", "169.254.169.254", "metadata.google.internal",
                       "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.20.", "172.21.",
                       "172.22.", "172.23.", "172.24.", "172.25.", "172.26.", "172.27.",
                       "172.28.", "172.29.", "172.30.", "172.31.", "192.168."]
            if any(hostname == b or hostname.startswith(b) for b in blocked):
                return JSONResponse({"error": "URL blocked for security"}, status_code=403)
```

### WebSocket Authentication Code (`backend/main.py`, lines 140–176):
```python
@app.websocket("/ws/war-room")
async def websocket_war_room(websocket: WebSocket):
    # Verify JWT Bearer token
    token = websocket.query_params.get("token")
    ...
    if not token:
        await websocket.close(code=4001)
        return

    import jwt
    from .auth import JWT_SECRET_KEY, JWT_ALGORITHM
    try:
        jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except Exception:
        await websocket.close(code=4001)
        return
```

### Execution Logs (`tests/test_adversarial_security.py`):
```cmd
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0
collected 20 items

tests/test_adversarial_security.py::test_rate_limiting_scrape PASSED     [  5%]
tests/test_adversarial_security.py::test_rate_limiting_generate_cover_letter PASSED [ 10%]
tests/test_adversarial_security.py::test_rate_limiting_stream_cover_letter PASSED [ 15%]
tests/test_adversarial_security.py::test_shared_rate_limiting_across_endpoints PASSED [ 20%]
tests/test_adversarial_security.py::test_rate_limiting_proxy_headers_dos_flaw PASSED [ 25%]
tests/test_adversarial_security.py::test_ssrf_direct_bypass_vulnerabilities PASSED [ 30%]
tests/test_adversarial_security.py::test_ssrf_redirect_bypass_to_internal_endpoints PASSED [ 35%]
tests/test_adversarial_security.py::test_websocket_auth_failures PASSED  [ 40%]
tests/test_adversarial_security.py::test_websocket_auth_claim_bypass PASSED [ 45%]
tests/test_adversarial_security.py::test_all_api_v1_endpoints_require_jwt[app0-POST-/api/v1/scrape-payload0] PASSED [ 50%]
tests/test_adversarial_security.py::test_all_api_v1_endpoints_require_jwt[app1-POST-/api/v1/generate-cover-letter-payload1] PASSED [ 55%]
...
======================= 20 passed, 3 warnings in 34.35s =======================
```

---

## 2. Logic Chain

- **Volumetric Rate Limiting**: The rate-limiter utilizes a single instance of `RateLimiter` shared across multiple endpoints (`/api/v1/scrape`, `/api/v1/generate-cover-letter`, and `/api/v1/ai/generate-cover-letter/stream`). I verified that requests on all three routes collectively increment the rate-limiting counter (`test_shared_rate_limiting_across_endpoints`). Additionally, the rate limiter uses `request.client.host` without considering headers like `X-Forwarded-For`. While this blocks headers-spoofing bypasses (`test_rate_limiting_proxy_headers_dos_flaw`), it introduces a major Denial-of-Service flaw where one user behind a corporate/VPN proxy can exhaust the limits for all users sharing that proxy IP.
- **SSRF Redirect Bypass**: The blocklist check in `/api/v1/fetch-url` performs naive string starts-with/equality matching on the parsed hostname string. Consequently:
  - IPv6 loopbacks like `[::1]` parse to hostname `::1`, bypassing the check entirely.
  - Alternative loopback IP space like `127.0.0.2` parses to `127.0.0.2`, bypassing the block which only explicitly lists `127.0.0.1`.
  - Subdomains of localhost like `sub.localhost` parse to `sub.localhost`, bypassing the check.
  - Using redirect hops, an attacker can request a seemingly safe external address which redirects to these local/loopback hostnames. Since the custom redirect loop applies the exact same bypassable blocklist check, the redirected request is followed, resulting in internal data extraction (`test_ssrf_redirect_bypass_to_internal_endpoints`).
- **WebSocket Authentication Bypasses**: The WebSocket endpoint `/ws/war-room` resolves tokens correctly and closes unauthorized sockets with code `4001` (`test_websocket_auth_failures`). However, the authentication logic only checks if the signature is valid; it does not inspect claims (e.g., verifying `sub` exists or mapping connection to a valid user account). I demonstrated this bypass by generating a signed JWT with an empty payload `{}` and successfully connecting and communicating through the WebSocket (`test_websocket_auth_claim_bypass`).
- **JWT API Token Verification**: All defined routes under `/api/v1/*` in both monolith and backend are verified to require a valid token, rejecting unauthorized access with `401 Unauthorized` and successfully allowing authenticated traffic (`test_all_api_v1_endpoints_require_jwt`).

---

## 3. Caveats
- Host name resolution (DNS-level rebinding) was not tested with a real external DNS server due to `CODE_ONLY` network isolation constraints. However, host header resolution bypasses were simulated using custom httpx client mocks and local hostnames.
- The tests assume that `TESTING="true"` correctly dials down rate-limiting thresholds (3 requests per 10 seconds) during evaluation.

---

## 4. Conclusion
While the basic JWT validation and endpoint protections are functionally correct and block obvious attackers, there are several architectural and implementation vulnerabilities:
1. **SSRF Protection Bypass**: String-based host matching is bypassed by `[::1]`, `127.0.0.2`, and `sub.localhost`. Redirect logic follows these bypasses end-to-end.
2. **WebSocket Authorization Flaw**: Validating signatures without checking claims allows unauthenticated/claim-empty connections.
3. **Proxy rate-limit DOS**: Proxy-unaware client-IP resolution makes standard deployments vulnerable to service exhaustion DOS attacks.

---

## 5. Verification Method

To verify these security findings and run the stress-test suite:

1. Setup the environment variable to avoid Cython SQLite extensions issue:
   ```powershell
   $env:DISABLE_SQLALCHEMY_CEXT_RUNTIME="1"
   ```
2. Run pytest targeting the new adversarial tests:
   ```powershell
   test_env\Scripts\python -Xutf8 -m pytest -v tests/test_adversarial_security.py
   ```
3. Observe that all 20 tests pass cleanly, confirming the existence of both the security blocks and the bypasses.
