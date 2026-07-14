# Scope: M2: Secure CORS Dynamic Origin Validation

## Architecture
- FastAPI web server (`backend/main.py`)
- Unit tests (`tests/test_cors_validation.py` or similar)

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M2: Secure CORS Dynamic Origin Validation | Refactor CORS origin validation in backend/main.py to securely validate incoming request origins dynamically using strict regex matching, write unit tests, and run all tests. | None | IN_PROGRESS |

## Interface Contracts
- `backend/main.py`: Dynamic CORS origin matching helper that validates subdomains securely (wildcards allowed only at subdomain level) and rejects malicious origins.
