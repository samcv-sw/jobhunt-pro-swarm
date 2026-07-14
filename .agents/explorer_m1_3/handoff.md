# Handoff Report: Security Middleware Audit of `backend/`

## 1. Observation

### A. Rate Limiter IP Spoofing Vulnerability
In `backend/limiter.py` (lines 93–106), client IP resolution is implemented as follows:
```python
    async def __call__(self, request: Request):
        # Resolve client IP checking X-Forwarded-For or X-Real-IP
        client_ip = None
        xff = request.headers.get("x-forwarded-for")
        if xff:
            client_ip = xff.split(",")[0].strip()
        else:
            xri = request.headers.get("x-real-ip")
            if xri:
                client_ip = xri.strip()

        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"
```
Conversely, `backend/auth.py` (lines 86–101) implements trusted proxy checks for IP extraction:
```python
def _get_client_ip(request: Request | None) -> str:
    """Extract the real client IP, only trusting X-Forwarded-For from verified proxies.

    IMP-008: Validates the connecting IP against TRUSTED_PROXIES before
    honouring X-Forwarded-For, preventing header-spoofing rate-limit bypass.
    """
    if request is None:
        return "unknown"
    connecting_ip = request.client.host if request.client else None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for and connecting_ip and _is_trusted_proxy(connecting_ip):
        # Only take the first (leftmost = real client) IP
        return forwarded_for.split(",")[0].strip()
    if connecting_ip:
        return connecting_ip
    return "unknown"
```

### B. CORS Wildcard on Public Suffix
In `backend/main.py` (lines 300–302), a wildcard origin is automatically appended to `origins`:
```python
if "https://*.pages.dev" not in origins:
    origins.append("https://*.pages.dev")
```
It is subsequently loaded into `SecureCORSMiddleware` with credentials enabled (lines 310–314):
```python
    app.add_middleware(
        SecureCORSMiddleware,
        allowed_patterns=origins,
        allow_credentials=True,
    )
```

### C. CORS Subdomain Validation TLD Escape
In `backend/main.py` (lines 209–214), wildcard pattern format verification is performed using:
```python
    if not re.match(r'^https?://\*\.[a-zA-Z0-9-]+(\.[a-zA-Z]{2,})*$', pattern):
        raise ValueError(
            f"Unsupported wildcard origin pattern '{pattern}'. "
            "Wildcards are only allowed at the subdomain level, e.g. "
            "'https://*.example.com'."
        )
```

### D. WebSocket Authentication Lockout Bypass
In `backend/main.py` (lines 886–910), the `/ws/war-room` route parses and decodes incoming tokens directly:
```python
    from .auth import decode_jwt_token
    try:
        claims = decode_jwt_token(token)
        sub = claims.get("sub")
        if not sub:
            logger.warning("WebSocket connection rejected: invalid JWT subject.")
            await websocket.close(code=4001)
            return

        async with async_session() as session:
            result = await session.execute(
                text("SELECT is_active FROM users WHERE user_id = :user_id"),
                {"user_id": sub}
            )
            row = result.fetchone()
            if not row or not row[0]:
                logger.warning(f"WebSocket connection rejected: user {sub} is inactive or missing.")
                await websocket.close(code=4001)
                return
    except Exception as jwt_err:
        logger.error(f"WebSocket authentication error: {jwt_err}")
        await websocket.close(code=4001)
        return
```
No calls to `_check_lockout` or `_record_failure` are made.

### E. Brute-Force Tracker Memory Leak
In `backend/auth.py` (lines 54–55), the state tracker is declared as:
```python
# { ip: {"failures": [timestamp, ...], "locked_until": float | None} }
_rate_state: dict = defaultdict(lambda: {"failures": [], "locked_until": None})
```
No logic exists in `_record_failure`, `_check_lockout`, or `_record_success` to delete keys from the dictionary once their failures or lockouts expire.

---

## 2. Logic Chain

### A. Rate Limiter Bypass
1. `backend/limiter.py` reads `x-forwarded-for` and `x-real-ip` headers unconditionally.
2. It does not verify if the request was routed through a trusted gateway/proxy.
3. Consequently, any attacker can send custom `X-Forwarded-For` headers with randomized IP values to completely evade the `RateLimiter`.

### B. CORS Public Suffix Permissive Wildcard
1. Cloudflare Pages (`pages.dev`) is a public suffix platform where any user can register and deploy arbitrary static sites (e.g., `attacker.pages.dev`).
2. Allowing `https://*.pages.dev` with `allow_credentials=True` enables any site hosted on `pages.dev` to execute cross-origin requests targeting the backend, attaching valid session credentials.

### C. CORS Subdomain Validation TLD Escape
1. The regex pattern `^https?://\*\.[a-zA-Z0-9-]+(\.[a-zA-Z]{2,})*$` matches inputs that have only one domain component after the wildcard prefix.
2. For instance, `https://*.com` matches because `[a-zA-Z0-9-]+` matches `com` and `(\.[a-zA-Z]{2,})*` matches the empty string.
3. If evaluated, `https://*.com` translates to `^https://[a-zA-Z0-9-]+\.com$`, exposing the backend to all `.com` domains.

### D. WebSocket Lockout Bypass
1. The endpoint `/ws/war-room` directly calls `decode_jwt_token` instead of using FastAPI's dependency injection via `Depends(verify_jwt)`.
2. It does not verify if the connecting client's IP is locked out, nor does it record verification failures.
3. An attacker can repeatedly attempt connections with bad/guessed tokens without triggering the IP brute-force lockout.

### E. Brute-Force Tracker Memory Leak
1. `_rate_state` is an in-memory `defaultdict` mapped by client IP.
2. When an IP encounters validation failures, an entry is added or updated.
3. Over time, as distinct malicious scanner IPs request the system, new keys are created.
4. Because expired records are never pruned or deleted from the dictionary (only their list values are cleared), memory usage grows monotonically (unbounded growth, CWE-400).

---

## 3. Caveats
- No caveats. The audit covers the security middleware logic and configuration files directly.

---

## 4. Conclusion
The security middleware in the `backend/` directory suffers from five distinct vulnerabilities:
1. **IP spoofing bypass** in the rate-limiting decorator (`limiter.py`).
2. **Insecure CORS wildcard definition** allowing all subdomains under `pages.dev`.
3. **TLD wildcard escape** in the CORS pattern matcher.
4. **Lockout bypass** in the WebSocket `/ws/war-room` handler.
5. **Slow memory leak** in the JWT brute-force blocker state tracker (`auth.py`).

**Actionable Proposals**:
1. **Fix Rate Limiter IP parsing**: Refactor `backend/limiter.py` to import and use the safe `_get_client_ip` function from `backend/auth.py` (which verifies `TRUSTED_PROXIES`).
2. **Secure CORS Wildcards**: Replace the global `*.pages.dev` with the exact deployed subdomains (or crosscheck against a static whitelist). Ensure TLD wildcards like `*.com` are rejected by requiring at least two dot-separated labels after the wildcard in `_build_origin_regex`.
3. **WebSocket Protection**: Integrate the lockout checks (`_check_lockout`, `_record_failure`) from `backend/auth.py` into the `/ws/war-room` WebSocket route.
4. **State Cleanup**: Implement an eviction or cleanup mechanism in `backend/auth.py` for the `_rate_state` dictionary to purge entries with no active failures or lockouts.

---

## 5. Verification Method

- **Run security test suite**:
  Execute `pytest tests/test_cors_validation.py tests/test_hardening_v2.py tests/test_security_hardening.py` to verify that existing test validations remain stable.
- **Inspect affected files**:
  - `backend/limiter.py`: verify that the connection IP resolution trusts headers only from verified proxies.
  - `backend/main.py`: verify that dynamic CORS wildcard validation prevents single-label TLD patterns and public suffix wildcards.
  - `backend/auth.py`: verify `_rate_state` cleanup.
