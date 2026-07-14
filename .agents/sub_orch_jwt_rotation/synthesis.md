# Synthesis Report: Multi-Key JWT Secret Rotation (Milestone 1)

This document reconciles and synthesizes the findings and design recommendations from Explorer 1, 2, and 3.

## 1. Consensus & Key Discoveries

All three Explorers independently identified:
1. **Target File (`backend/auth.py`)**: Current logic relies on a single `JWT_SECRET_KEY`.
2. **Environment Variable Configuration**:
   - Parse `JWT_SECRET_KEYS` as a comma-separated list of keys.
   - If missing, fall back to `JWT_SECRET_KEY`.
   - If that is also missing, fall back to `"jobhunt-pro-secret-key-32bytes-ok!!"` if in test mode, or raise a `ValueError` in production.
3. **Primary Key Alignment**: The first key in `JWT_SECRET_KEYS` is the primary key used to sign new tokens.
4. **Fallback Verification**:
   - Loop through `JWT_SECRET_KEYS`.
   - If decoding succeeds, return payload.
   - If `ExpiredSignatureError` is raised, raise it immediately because the signature is valid for that key, but expired.
   - For `InvalidSignatureError` / `InvalidTokenError`, proceed to the next key.
5. **Direct Dependency Points**:
   - `backend/main.py` WebSocket auth (lines 567-569) manually imports `JWT_SECRET_KEY` and decodes. This must be refactored to use the multi-key decode helper.
   - `web/app_v2.py` (lines 98-107, 120-131, 8475) duplicates the JWT configuration and verification. These must be updated to align with multi-key parsing/decoding.
6. **Testing & Validation**:
   - Add new tests to `tests/test_jwt_rotation.py` to prevent E2E file pollution and test config parsing, key rotation fallback, invalid key rejection, and expired token behavior.
   - Run `pytest` to execute tests.

## 2. Implementation Steps

The Worker should perform the following changes:

### Step 1: Modify `backend/auth.py`
- Replace single key loading with list parsing logic:
  ```python
  raw_keys = os.environ.get("JWT_SECRET_KEYS")
  if raw_keys:
      JWT_SECRET_KEYS = [k.strip() for k in raw_keys.split(",") if k.strip()]
  else:
      single_key = os.environ.get("JWT_SECRET_KEY")
      if not single_key:
          if os.getenv("TESTING") == "true" or "pytest" in sys.modules or "unittest" in sys.modules:
              single_key = "jobhunt-pro-secret-key-32bytes-ok!!"
          else:
              raise ValueError("JWT_SECRET_KEYS or JWT_SECRET_KEY environment variable is not set in production context.")
      JWT_SECRET_KEYS = [single_key]

  JWT_SECRET_KEY = JWT_SECRET_KEYS[0]
  ```
- Implement `decode_jwt_token(token: str) -> dict`:
  ```python
  def decode_jwt_token(token: str) -> dict:
      token_expired = False
      for key in JWT_SECRET_KEYS:
          try:
              return jwt.decode(token, key, algorithms=[JWT_ALGORITHM])
          except jwt.ExpiredSignatureError:
              token_expired = True
              break
          except jwt.InvalidSignatureError:
              continue
          except jwt.InvalidTokenError:
              break
      if token_expired:
          raise jwt.ExpiredSignatureError("Token has expired")
      raise jwt.InvalidTokenError("Invalid token")
  ```
- Update `verify_jwt` in `backend/auth.py` to use `decode_jwt_token`.

### Step 2: Modify `backend/main.py`
- Import `decode_jwt_token` from `backend.auth`.
- Replace manual `jwt.decode` in the WebSocket route with `decode_jwt_token`.

### Step 3: Modify `web/app_v2.py`
- Sync configuration parsing of `JWT_SECRET_KEYS` and `JWT_SECRET_KEY`.
- Refactor its internal `verify_jwt` and manual token decode logic (e.g. line 8475) to support trying multiple keys.

### Step 4: Write Unit Tests
- Create `tests/test_jwt_rotation.py` with:
  1. Config parsing tests (`test_load_jwt_secrets_config_parsing`).
  2. Fallback verification test (`test_jwt_rotation_verification_success`).
  3. Invalid key rejection test (`test_jwt_rotation_verification_invalid_key_rejected`).
  4. Expired token verification test (`test_jwt_rotation_expired_token_raises_expired`).
