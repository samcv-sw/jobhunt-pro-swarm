# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 3.x (main) | ✅ Yes |
| 2.x | ❌ No |

## Reporting a Vulnerability

**Please do NOT open a public GitHub issue for security vulnerabilities.**

Instead, email: **security@jobhuntpro.app** with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fix (optional)

You can expect a response within **48 hours** and a patch within **7 days** for critical issues.

## Security Architecture

### Authentication
- All `/api/v1/*` endpoints require a valid JWT Bearer token
- Tokens expire after 1 hour
- Expired, tampered, and missing tokens return `401 Unauthorized`
- JWT secret key must be set via `JWT_SECRET_KEY` env variable (never hardcoded)

### Environment Variables
- Secrets are loaded exclusively from environment variables
- Never commit `.env` to version control (blocked by `.gitignore`)
- Use `.env.example` as a template with placeholder values only

### Email Security
- BanShield enforces per-provider rate limits to prevent account bans
- No credentials are stored in the database — only in environment variables
- Gmail OAuth2 is used instead of plain passwords where possible

### Data
- Local SQLite databases (`.db` files) are excluded from git
- PostgreSQL credentials loaded via `DATABASE_URL` env var only
