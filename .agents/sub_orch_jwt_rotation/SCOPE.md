# Scope: M1: Multi-Key JWT Secret Rotation

## Architecture
- Auth engine (`backend/auth.py`)
- Auth tests (`tests/test_auth.py` or similar auth test file)

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: Multi-Key JWT Secret Rotation | Implement dynamic JWT verification using list of secrets, write unit tests, run all tests. | None | DONE |

## Interface Contracts
- `backend/auth.py`: `verify_token` or equivalent validates signature against any secret from `JWT_SECRET_KEYS`.
