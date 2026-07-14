## 2026-07-14T11:10:12Z

Your task is to implement the requested security and performance changes to address the code review findings:

1. LAZY & THROTTLED LOCKOUT CLEANUP (in `backend/auth.py`):
   - Replace the full-dictionary traversal inside request-critical functions (`_check_lockout`, `_record_failure`, `_record_success`).
   - Implement lazy pruning: when any of these functions is called for a specific IP, prune only that IP's failures list, update its lockout state, and if it has no failures and no lockout, evict it from `_rate_state` (i.e. `_rate_state.pop(ip, None)`).
   - Implement a throttled global cleanup: track `_last_prune_time` globally. If `len(_rate_state) > 1000` and `now - _last_prune_time > 60.0`, traverse and clean up all expired records in the dictionary, then update `_last_prune_time = now`.
   - Ensure all dictionary read/write operations on `_rate_state` are protected by the existing `_rate_lock`.

2. RESTRICT TRUSTED PROXIES (in `backend/auth.py`):
   - Restrict the default fallback value of the `TRUSTED_PROXIES` environment variable inside `_load_trusted_proxies` to `"127.0.0.1"` (remove `"10.0.0.0/8"`).

3. NO LOCKOUT ON API JWT VERIFICATION (in `backend/auth.py` and `backend/main.py`):
   - Expired signatures or missing credentials should not trigger IP rate limit lockouts.
   - Remove all calls to `_record_failure(ip)` from `verify_jwt` in `backend/auth.py` and from `/ws/war-room` in `backend/main.py`.
   - Retain `_check_lockout(ip)` checks inside `verify_jwt` and `/ws/war-room` to enforce lockouts if an IP has been locked out elsewhere.

4. CORS REGEX PRE-COMPILATION (in `backend/main.py`):
   - Pre-compile CORS origin patterns once on initialization rather than on every HTTP request.
   - In `SecureCORSMiddleware.__init__`, compile the allowed patterns list into a list of tuples `(pattern_str, compiled_regex_or_none)` using `_build_origin_regex(pattern)` and store it in `self._compiled_patterns`.
   - In `SecureCORSMiddleware.dispatch`, perform origin matching by iterating over `self._compiled_patterns` without re-compiling them.

5. VERIFICATION:
   - Run `pytest` via `uv run pytest` to ensure all tests pass (including `tests/test_hardening_v2.py`).
   - Run `verify_integrity.py` to ensure all checks pass.
   - Verify the Next.js frontend builds successfully.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write a structured handoff.md inside your working directory summarizing your changes, test outcomes, and verification results.
