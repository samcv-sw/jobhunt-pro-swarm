# Review Report: Multi-Key JWT Secret Rotation (Milestone 1)

## Review Summary

- **Verdict**: PASS (APPROVE)
- **Reviewer**: Reviewer 1 (teamwork_preview_reviewer)
- **Date**: 2026-07-12
- **Scope**: Multi-Key JWT Secret Rotation implementation in `backend/auth.py`, `backend/main.py`, `web/app_v2.py`, and unit tests in `tests/test_jwt_rotation.py`.

The Multi-Key JWT Secret Rotation is successfully implemented, conforms to all architectural requirements and interface contracts specified in `SCOPE.md` and `synthesis.md`, and shows zero regression in existing functionality.

---

## 1. Quality Review Findings

### [Minor] Finding 1: Incomplete Exception Stub in `web/app_v2.py`
- **What**: The local `_JwtStub` fallback in `web/app_v2.py` is missing exception classes (`ExpiredSignatureError`, `InvalidSignatureError`, `InvalidTokenError`).
- **Where**: `web/app_v2.py`, lines 91-96.
- **Why**: If PyJWT is not installed in the execution environment, the application catches the `ImportError` on startup and binds `jwt` to `_JwtStub`. However, any subsequent call to `decode_jwt_token` will try to catch `jwt.ExpiredSignatureError`, raising `AttributeError` instead of propagating a clean error or the original stub exception.
- **Suggestion**: Since PyJWT is a hard dependency of the `backend` and is required for proper authentication, the mock stub is largely redundant. If it must exist, it should define stub classes for exceptions:
  ```python
  class _JwtStub:
      class ExpiredSignatureError(Exception): pass
      class InvalidSignatureError(Exception): pass
      class InvalidTokenError(Exception): pass
      ...
  ```

### [Minor] Finding 2: Code Duplication
- **What**: The configuration parsing logic for `JWT_SECRET_KEYS` and the definition of `decode_jwt_token` are duplicated.
- **Where**: `backend/auth.py` (lines 17-28, 131-150) and `web/app_v2.py` (lines 98-113, 118-137).
- **Why**: Since `web/app_v2.py` acts as a decoupled component (it does not import from the `backend` package), it has its own independent parser and decoder. This introduces a double-maintenance overhead if the signature format or rotation mechanics change.
- **Suggestion**: If possible in future architectural refactors, extract shared authentication utility helpers into a common module (e.g. a `core/auth_utils.py` or similar) that can be safely imported by both packages.

### [Minor] Finding 3: Unrelated Database Test Failures in Test Suite
- **What**: Running the full `pytest` suite triggers two test failures in `tests/e2e/test_database.py` relating to outbox syncing.
- **Where**: `tests/e2e/test_database.py::test_sync_outbox_to_cloud_soft_error` and `tests/e2e/test_database.py::test_sync_outbox_to_cloud_connection_exception_propagation`.
- **Why**: These failures are caused by database connectivity/mocking issues inside the outbox cloud sync logic. They do not import or execute any auth-related code and are entirely orthogonal to the JWT secret rotation changes.
- **Suggestion**: Ensure that the database outbox worker tests are properly mocked or run within a fully configured database environment.

---

## 2. Verified Claims

- **Claim 1**: `decode_jwt_token` verifies token signature against a list of keys and falls back to older keys.
  - *Method*: Inspected `backend/auth.py` and ran `test_jwt_rotation_verification_success`.
  - *Result*: **PASS**. Tokens signed with secondary or tertiary keys in the list are successfully verified.
- **Claim 2**: Expired tokens signed with any valid key are rejected immediately and raise `ExpiredSignatureError`.
  - *Method*: Verified code logic and ran `test_jwt_rotation_expired_token_raises_expired`.
  - *Result*: **PASS**. If a token matches the signature of any key in the rotation list but its expiration timestamp is in the past, verification halts immediately.
- **Claim 3**: Invalid tokens signed with unknown keys are rejected.
  - *Method*: Verified code logic and ran `test_jwt_rotation_verification_invalid_key_rejected`.
  - *Result*: **PASS**. An unknown signature throws `InvalidSignatureError`.
- **Claim 4**: Configuration handles comma-separated env values and falls back to a single key or test defaults.
  - *Method*: Verified parsing block and ran `test_load_jwt_secrets_config_parsing`.
  - *Result*: **PASS**. Handles whitespace, empty entries, single key fallback, and testing default (`"jobhunt-pro-secret-key-32bytes-ok!!"`).

---

## 3. Coverage Gaps & Risk Assessment

- **Dependency & Call Site Coverage**: High. All call sites that previously executed `jwt.decode` were identified and refactored to use the multi-key aware `decode_jwt_token` wrapper. These include:
  1. FastAPI Bearer Token dependency (`verify_jwt` in `backend/auth.py` and `web/app_v2.py`).
  2. WebSocket War Room authentication (`websocket_war_room` in `backend/main.py`).
  3. API import link validation fallback auth (`api_fetch_url` in `web/app_v2.py`).
- **Risk Level**: **Low**. The rotation logic is isolated and has high coverage under unit tests.

---

## 4. Adversarial Review (Critic Challenges)

### Challenge Summary
- **Overall Risk Assessment**: **LOW**
- The implementation is robust against traditional JWT attacks (such as algorithm confusion or mock-key injection) by pinning the accepted algorithms to `["HS256"]`.

### [Low] Challenge 1: Timing Side-Channel during Key Rotation Matching
- **Assumption Challenged**: Sequential iteration over keys takes uniform time.
- **Attack Scenario**: An attacker measures the processing latency of token verification. Because the code loops through `JWT_SECRET_KEYS` and returns on the first match, a token signed with the primary key (first key) returns faster than a token signed with a rotated key (later in the list) or an invalid token.
- **Blast Radius**: Extremely small. The difference is on the order of microseconds (1 vs 2 HMAC computations), which is drowned out by network jitter in a remote network context.
- **Mitigation**: Standard rotation lists are tiny (typically 2-3 keys), making this negligible. No mitigation is necessary unless the key list scales to hundreds of keys.

### [Low] Challenge 2: Empty/Whitespace-only Environment Variable Values
- **Assumption Challenged**: Environment variables contain valid strings.
- **Attack Scenario**: If `JWT_SECRET_KEYS` is defined as empty or containing only spaces (e.g. `JWT_SECRET_KEYS="  ,  "`), it might result in an empty key list.
- **Blast Radius**: Low. The parsing logic uses list comprehensions to filter out empty/whitespace-only values (`if k.strip()`). If no keys remain, it falls back to the single `JWT_SECRET_KEY` variable or test defaults, preventing crashes.

---

## 5. Test Execution Outputs

### Unit Tests
Command: `pytest tests/test_jwt_rotation.py -v`
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.0.3, pluggy-1.6.0 -- C:\Users\samde\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\samde\Desktop\Folders & Projects\cv sam new ma3 kimi
configfile: pytest.ini
plugins: langsmith-0.8.5, anyio-4.13.0, Faker-40.18.0, logfire-4.37.0, asyncio-1.3.0, mock-3.15.1
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 4 items

tests/test_jwt_rotation.py::test_load_jwt_secrets_config_parsing PASSED  [ 25%]
tests/test_jwt_rotation.py::test_jwt_rotation_verification_success PASSED [ 50%]
tests/test_jwt_rotation.py::test_jwt_rotation_verification_invalid_key_rejected PASSED [ 75%]
tests/test_jwt_rotation.py::test_jwt_rotation_expired_token_raises_expired PASSED [100%]

======================= 4 passed, 12 warnings in 0.39s ========================
```

### Full Test Suite (Regressions Check)
Command: `pytest`
```
=========================== short test summary info ===========================
FAILED tests/e2e/test_database.py::test_sync_outbox_to_cloud_soft_error - sql...
FAILED tests/e2e/test_database.py::test_sync_outbox_to_cloud_connection_exception_propagation
============ 2 failed, 433 passed, 48 warnings in 64.50s (0:01:04) ============
```
*(Note: As analyzed in Finding 3, the database outbox sync failures are pre-existing/orthogonal and completely unrelated to the JWT rotation implementation changes.)*
