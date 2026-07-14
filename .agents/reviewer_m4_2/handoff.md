# Handoff Report: Security Middleware Review

## 1. Observation
I have inspected the codebase and ran the tests on the security middleware changes in `backend/limiter.py`, `backend/main.py`, and `backend/auth.py`.

### Verbatim Code Snippets & File Locations
1. **CORS Subdomain Regex Compilation (`backend/main.py` lines 221–242)**:
   ```python
   def is_origin_allowed(origin: str, allowed_patterns: list[str]) -> bool:
       """Return True if *origin* matches any of the *allowed_patterns*.

       Each pattern is either a literal origin or a subdomain-wildcard like
       ``https://*.example.com``.
       """
       for pattern in allowed_patterns:
           try:
               rx = _build_origin_regex(pattern)
           except ValueError:
               # ...
   ```
2. **Broad Default Trusted Proxies (`backend/auth.py` lines 64–74)**:
   ```python
   def _load_trusted_proxies() -> list:
       """Load trusted proxy CIDR ranges from TRUSTED_PROXIES env var."""
       raw = os.getenv("TRUSTED_PROXIES", "127.0.0.1,10.0.0.0/8")
       networks = []
       for entry in raw.split(","):
           # ...
   ```
3. **Synchronous Full-Dictionary Traversal under Global Lock (`backend/auth.py` lines 106–172)**:
   ```python
   def _check_lockout(ip: str) -> float:
       now = time.monotonic()
       with _rate_lock:
           state = _rate_state.get(ip)
           # ...
           # Clean up all expired records to prevent memory leak
           for key in list(_rate_state.keys()):
               s = _rate_state[key]
               s["failures"] = [t for t in s["failures"] if now - t < _FAIL_WINDOW_SECONDS]
               # ...
               if not s["failures"] and not k_locked:
                   _rate_state.pop(key, None)
   ```
4. **Verification Failure Locking out IP (`backend/auth.py` lines 255–299)**:
   ```python
   async def verify_jwt(
       credentials: HTTPAuthorizationCredentials = Security(security),
       request: Request = None,
   ) -> dict:
       ip = _get_client_ip(request)
       # ...
       if not credentials:
           if not _IS_TESTING:
               _record_failure(ip)
           raise HTTPException(...)
       # ...
       except jwt.ExpiredSignatureError:
           if not _IS_TESTING:
               _record_failure(ip)
           raise HTTPException(...)
   ```

### Test Execution Results
Proposed and ran the pytest test suite:
- Command: `pytest tests/test_hardening_v2.py`
- Result: `17 passed in 1.78s` (successfully verified all unit test coverage).

---

## 2. Logic Chain
1. **CPU Denial of Service (DoS) via Lock Contention**:
   - **Observation**: `verify_jwt` is a FastAPI dependency invoked on almost every API endpoint. It calls `_check_lockout(ip)`.
   - **Observation**: `_check_lockout` acquires a global thread lock `_rate_lock` and runs a `for key in list(_rate_state.keys())` loop to clean up all expired records.
   - **Inference**: Under heavy production traffic or a minor distributed brute-force attempt, the size of `_rate_state` ($N$) will grow to thousands of entries.
   - **Conclusion**: A loop of $O(N)$ operations executed synchronously on the critical path under a global lock for *every* incoming request will serialize request processing, trigger severe CPU/lock contention, and cause service degradation or complete Denial of Service.

2. **IP Spoofing and Arbitrary Lockout Bypass/Abuse**:
   - **Observation**: `_load_trusted_proxies` defaults to `"127.0.0.1,10.0.0.0/8"`.
   - **Observation**: `_get_client_ip` extracts the IP from `X-Forwarded-For` if the connecting IP is a trusted proxy.
   - **Inference**: In typical VPC deployments, `10.0.0.0/8` spans the entire private subnet containing other services, peer nodes, and potentially internal users/VPN clients.
   - **Conclusion**: Any entity capable of sending requests to the backend port directly from within the `10.0.0.0/8` range can spoof the `X-Forwarded-For` header. This allows them to bypass the rate limiter, spoof their IP, or intentionally lock out target legitimate IP addresses by injecting them into `X-Forwarded-For` along with invalid tokens.

3. **NAT User Lockout and High Usability Risk**:
   - **Observation**: Missing credentials or expired JWT tokens trigger a rate-limiting failure record via `_record_failure(ip)`.
   - **Observation**: 5 failures lock out the IP address for 5 minutes.
   - **Inference**: Expired tokens are extremely common client-side occurrences (e.g. background polling before user-refresh completes). Multiple users often share a single NAT public IP (offices, schools, mobile gateways).
   - **Conclusion**: One client device polling with an expired token will trigger a lockout for the shared NAT IP, preventing all other legitimate users behind that NAT from accessing the application. Online brute-forcing of a 32-byte HS256 key is mathematically infeasible, making IP lockout on signature verification unnecessary.

4. **Regex Recompilation Bottleneck**:
   - **Observation**: `is_origin_allowed` calls `_build_origin_regex(pattern)` for each pattern on every incoming request.
   - **Observation**: `_build_origin_regex` compiles the regex via `re.compile(f'^{escaped}$')` on each call.
   - **Conclusion**: Compiling regular expressions dynamically on every HTTP request consumes unnecessary CPU cycles and degrades request latency.

---

## 3. Caveats
- No caveats. I inspected all security middleware files, their dependencies, and executed the hardening test suite.

---

## 4. Conclusion & Review Reports

### Verdict: REQUEST_CHANGES

### Quality Review Report
#### Critical Finding 1: CPU Denial of Service (DoS) / Lock Contention in Lockout Memory Pruning
- **What**: Synchronous iteration over all active IP keys in `_rate_state` occurs on the request path under a global lock.
- **Where**: `backend/auth.py` in `_record_failure` (line 120), `_check_lockout` (line 158), and `_record_success` (line 184).
- **Why**: Under moderate load or active scans, the number of tracked IPs ($N$) grows, turning an $O(1)$ client-IP check into a blocking $O(N)$ full-state traversal, serializing all API requests.
- **Suggestion**: Perform state cleanup asynchronously (e.g. via a background task like `_periodic_cleanup` in the rate limiter) or lazily (only clean up the specific IP's state upon lookup).

#### Major Finding 2: IP Spoofing and Arbitrary IP Lockout Abuse
- **What**: Extremely broad default network mask `10.0.0.0/8` inside `TRUSTED_PROXIES`.
- **Where**: `backend/auth.py` in `_load_trusted_proxies` (line 66).
- **Why**: Allows any internal VPC actor or peer service to spoof `X-Forwarded-For`. An attacker can manipulate this header to bypass lockout limits or lock out legitimate target IPs.
- **Suggestion**: Restrict the default `TRUSTED_PROXIES` list strictly to `127.0.0.1` and require explicit production subnet configurations.

#### Major Finding 3: Inappropriate Lockout Triggering on Missing or Expired JWTs
- **What**: IP lockout triggers on signature expiration and missing headers.
- **Where**: `backend/auth.py` in `verify_jwt` (lines 266–267, 287–288).
- **Why**: Expired tokens occur naturally. Locking out IP addresses on token verification disrupts service for all users behind a shared NAT IP. Online brute-forcing of HS256 signatures is impossible.
- **Suggestion**: Only apply brute-force lockout on initial credentials endpoints (like `/login` or `/token`), not on general API token validation requests.

#### Minor Finding 4: Inefficient Dynamic CORS Regex Compilation
- **What**: Re-compiling origin regexes on every request.
- **Where**: `backend/main.py` in `is_origin_allowed` (line 229).
- **Why**: Adds latency and increases CPU overhead on every CORS-enabled API request.
- **Suggestion**: Compile the allowed origin regex patterns once during `SecureCORSMiddleware` initialization (`__init__`) and store the compiled matchers.

---

### Adversarial Review Challenge Report
#### Overall risk assessment: HIGH

#### Challenges
1. **Lockout Cleanup DoS**:
   - **Assumption challenged**: The number of unique IPs triggering failures is small enough that synchronous cleaning is cheap.
   - **Attack scenario**: An attacker generates thousands of requests spoofing unique IPs (or using a botnet) sending invalid JWT tokens.
   - **Blast radius**: The `_rate_state` size grows to $10,000+$. Every subsequent authenticated request blocks waiting for the global lock, looping over all keys, rendering the entire backend unresponsive.
   - **Mitigation**: Move the cleanup out of the request path.

2. **IP Spoofing / target Lockout**:
   - **Assumption challenged**: Connecting IPs in `10.0.0.0/8` are trusted proxies that do not behave maliciously.
   - **Attack scenario**: A compromised service or malicious user in the same network block sends requests to the backend with `X-Forwarded-For: <legitimate_admin_IP>` and an invalid token.
   - **Blast radius**: The target administrator's IP address gets locked out from all authenticated API endpoints.
   - **Mitigation**: Tighten default `TRUSTED_PROXIES`.

3. **NAT lockout DoS**:
   - **Assumption challenged**: IP lockouts only affect malicious brute-force actors.
   - **Attack scenario**: A user behind a corporate NAT has an expired token and a browser tab polling the server.
   - **Blast radius**: After 5 failed polls, the corporate NAT public IP is locked out. All other employees in the corporate office are blocked from accessing the system.
   - **Mitigation**: Remove brute-force lockout from the JWT validation layer.

---

## 5. Verification Method
1. **Running the Unit Tests**:
   Proactively run the pytest test suite to ensure existing security logic remains active:
   ```bash
   pytest tests/test_hardening_v2.py
   ```
2. **Reviewing Code Paths**:
   Verify code changes in `backend/auth.py` and `backend/main.py` conform to:
   - Async/lazy cleanup of brute-force records.
   - Restricting `TRUSTED_PROXIES` defaults.
   - Pre-compiling CORS subdomain patterns on initialization.
