# Scope: Frontend RTL & Glassmorphism Design System (R1)

## Architecture
- Next.js app located in `frontend/`
- Standard styling is done using Tailwind CSS or CSS files in `frontend/src/`

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| 1 | CSS Logical Properties Audit | Audit and replace all physical directional CSS properties in `frontend/src/` | None | PLANNED |
| 2 | Glassmorphism UX Polish | Enhance glassmorphism components to adhere to AGENTS.md RTL/Arabic guidelines | M1 | PLANNED |
| 3 | Build Validation | Verify `npm run build` succeeds | M2 | PLANNED |

## Interface Contracts
- No physical directional CSS properties should remain in `frontend/src/`.
- Forms must use `dir="auto"`.
- Arabic typography must use Cairo/Tajawal, min font-size 16px, line-height 1.6-2.0, and no letter-spacing.
