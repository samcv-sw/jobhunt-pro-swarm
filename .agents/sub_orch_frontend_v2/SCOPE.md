# Scope: Frontend Dashboard Improvements (R2)

## Architecture
- **Framework**: Next.js (App Router setup under `frontend/src/app/`)
- **Styling**: Tailwind CSS, logical CSS properties for LTR/RTL support, Arabic typography (Cairo/Tajawal fonts).
- **Views**:
  - `frontend/src/app/dashboard/page.tsx` - Dedicated dashboard with glassmorphism design. Displays live statistics (e.g., jobs scraped, success rate, system load), historical scrapes, and user analytics.
  - Tailwind/CSS variables for global font configuration and minimum sizes.
- **Interfaces**:
  - The dashboard is a Next.js client/server component fetching from mock data or existing API endpoints as needed.
  - Seamless responsive integration with the rest of the application layout.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | Exploration & Design | Codebase search, path mapping, and glassmorphism styling plan. | None | DONE |
| 2 | Dashboard Implementation | Create `frontend/src/app/dashboard/page.tsx` with statistics, historical scrapes, and analytics; ensure successful build. | M1 | DONE (Conv ID: d572b5eb-3de8-4029-9aeb-3e9a88e047e9) |
| 3 | Quality & Verification | Validate responsive layouts, CSS logical properties, Arabic typography, and perform security/integrity checks. | M2 | IN_PROGRESS (Conv IDs: cb964a69-60fc-469f-bccc-2e189a9b2e64, 207bcb39-c7cd-4b1f-90d4-0481abb40b85, edb5099a-0889-4908-b3f1-183f699e3ebe, 12759a97-13bc-464f-a680-3295105405d5, 586dca95-49ea-4da1-8908-cae783708d84) |

## Interface Contracts
### Dashboard ↔ API Data Flow
- Statistics structure: `totalScraped: number`, `successRate: number`, `activeScrapers: number`, `systemLoad: number`.
- Historical scrapes: Array of `{ id: string, targetSite: string, timestamp: string, status: 'success' | 'failed', count: number }`.
- User analytics: Array of monthly/weekly activity data for charting/tables.
- RTL/LTR Compatibility: Relies on `html[dir="rtl"]` or `html[dir="ltr"]` wrapping, and pure CSS logical properties (e.g., `margin-inline-start`, `padding-inline-end`).
- Arabic font fallback stack: Cairo/Tajawal.
