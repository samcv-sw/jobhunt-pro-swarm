# 🏛️ JobHunt Pro — Dashboard UI/UX Design System & Architectural Recommendations

## 1. Executive Summary
This report presents the findings and recommendations of **Explorer 1** regarding the dashboard UI/UX design system for **JobHunt Pro** within the Next.js workspace (`frontend/`). All design decisions and code recommendations are structurally aligned with standard Next.js (v16.2.9), Tailwind CSS v4, and the strict RTL and GCC cultural requirements outlined in `AGENTS.md`.

Our primary recommendation is the creation of a glassmorphic dashboard interface under `frontend/src/app/dashboard/page.tsx` that leverages the browser's WebAssembly SQLite database (`wasm-db.ts`) using OPFS. It displays live statistics, historical scrape records, and a custom SVG-based analytics chart, operating at zero server cost.

---

## 2. Catalog of Inputs & Sources Audited
To establish a complete evidence chain, the following files and directories were investigated:
1. **`frontend/package.json`**: Checked dependency trees (Next.js v16.2.9, React v19.2.4, Tailwind v4, `@tailwindcss/postcss` v4).
2. **`frontend/next.config.ts`**: Discovered `output: "export"` and `images: { unoptimized: true }` indicating a static SPA export model.
3. **`frontend/src/app/globals.css`**: Analyzed custom styling variables, font declarations, and CSS animations (glassmorphism panels, live indicators).
4. **`frontend/src/app/layout.tsx`**: Reviewed global font configurations (Cairo & Tajawal Next.js font optimization) and root `<html>` configurations.
5. **`frontend/src/app/page.tsx`**: Analyzed the home page structure, client-side translation model, and interaction logic.
6. **`frontend/src/app/db/wasm-db.ts`**: Audited local persistent database schema (`local_cv_profiles`, `local_campaigns`, `local_sync_queue`).
7. **`.agents/teamwork_preview_explorer_m1_2/findings.md`**: Reviewed and reconciled findings on CSS logical properties, directionality, and Arabic typography with Peer Agent **Explorer 2**.

---

## 3. Reconciled Synthesis (Consensus & Resolved Conflicts)

### Consensus
- **Tailwind CSS v4 Integration**: All agents agree that Tailwind CSS v4 is configured via `@import "tailwindcss"` in `globals.css` instead of a physical `tailwind.config.js`. Theme settings and variables must be managed inside CSS files.
- **Glassmorphic Theme**: Use `.glass-panel` and `.stat-card` classes already defined in `globals.css` to build stats, charts, and tables for visual consistency.
- **Next.js Font Variable Binding**: The Next.js custom Google fonts (Cairo, Tajawal) configured in `layout.tsx` are currently disconnected from `globals.css`. They must be mapped using `var(--font-cairo)` and `var(--font-tajawal)`.
- **Wasm SQLite Backend**: The dashboard should dynamically connect to `wasm-db.ts` to query `local_campaigns` and a proposed `local_scrapes` table, with robust mock fallbacks if the local storage is uninitialized.

### Resolved Conflicts
1. **Root HTML Directionality (`dir="auto"`)**:
   - *Conflict*: The root `<html>` tag in `layout.tsx` has `dir="auto"`. `explorer_m1_2` flagged that `dir="auto"` on root causes flashing and layout shifts because it relies on the first strong character of the page.
   - *Resolution*: Adopt `explorer_m1_2`'s suggestion to set a stable default of `dir="rtl"` on the root `<html>` tag, and handle individual page directions via client-side wrapper containers (`dir={isArabic ? "rtl" : "ltr"}`).
2. **Physical vs Logical Sizing (`width`/`height`)**:
   - *Conflict*: Standard Tailwind v4 classes (`w-full`, `h-full`) use physical width/height. `AGENTS.md` mandates `width`/`height` -> `inline-size`/`block-size`.
   - *Resolution*: Define global helper classes in `globals.css` (e.g. `.w-logical-full { inline-size: 100%; }`, `.h-logical-full { block-size: 100%; }`) and use inline style attributes (`style={{ inlineSize: '100%' }}`) for elements requiring strict layout compliance.
3. **Arabic Typography Sizing**:
   - *Conflict*: The home page (`page.tsx`) uses `text-xs` (12px) and custom sizes (`text-[10px]` / `text-[11px]`) for Arabic text, which degrades legibility.
   - *Resolution*: Enforce a strict minimum size of `14px` (`text-sm`) for all Arabic copy, raising labels, tables, and chart axes to `text-sm` or `text-[14px]`.

---

## 4. Glassmorphic Design System Guidelines (Tailwind CSS v4)

To build a high-fidelity glassmorphic dashboard, combine the following Tailwind v4 utility styles and custom CSS definitions:

| UI Component | Tailwind & CSS Utility Structure | Visual Specs |
| :--- | :--- | :--- |
| **Glass Panel** | `className="glass-panel p-6"` | `backdrop-filter: blur(20px)`, dark overlay (`rgba(15, 15, 25, 0.65)`), border `rgba(255, 255, 255, 0.07)` |
| **Stat Card** | `className="stat-card p-4 rounded-xl border border-zinc-800/40 bg-zinc-950/50"` | Subtle hover scale, border transitions, amber/success gold highlight borders |
| **Outbound CTAs** | `className="btn-gold font-bold text-sm rounded-lg"` | Centered layout, luxury gold gradient (`#AA7C11` to `#D4AF37`), scale effects on click |
| **Dynamic Table** | `className="w-full text-start border-collapse border-b border-zinc-900"` | Row hovers, clear color-coded statuses (Green = success, Red = failure, Blue = progress) |
| **Visual Charts** | Glassmorphic SVG wrappers with gradient stop colors | Interactive, inline-sized, zero external package footprint |

---

## 5. Dashboard Layout Architecture (`frontend/src/app/dashboard/page.tsx`)

We recommend structuring the dashboard as a highly responsive 3-column layout on desktop, collapsing to a single-column layout on mobile.

```
+--------------------------------------------------------------------------------+
|                                    HEADER                                      |
|  [Logo & Hub Title] [Status Badge]                 [Home Link] [Arabic Toggle] |
+--------------------------------------------------------------------------------+
|                                                                                |
|  +--------------------------------------------------------------------------+  |
|  |                             LIVE STATISTICS                              |  |
|  |  [Total Scrapes]     [Success Rate]     [Active Scrapers]  [System Load] |  |
|  +--------------------------------------------------------------------------+  |
|                                                                                |
|  +--------------------------------------------+ +---------------------------+  |
|  |         HISTORICAL SCRAPES TABLE           | |      PERFORMANCE CHART    |  |
|  |                                            | |  (SVG Area & Line Chart)  |  |
|  |  Company    Job Title   Status   Actions   | |                           |  |
|  |  -------    ---------   ------   -------   | |  Scrapes vs. Submissions  |  |
|  |  Aramco     AI Eng.     [Comp]   [View]    | |  -----------------------  |  |
|  |  NEOM       FullStack   [Proc]   [View]    | |                           |  |
|  |  SDAIA      DataSci.    [Comp]   [View]    | |  [Legend]                 |  |
|  |  stc        DevOps      [Fail]   [Retry]   | |                           |  |
|  |                                            | |  +---------------------+  |  |
|  |                                            | |  |    AI Copilot Tip   |  |  |
|  |                                            | |  +---------------------+  |  |
|  +--------------------------------------------+ +---------------------------+  |
+--------------------------------------------------------------------------------+
|                                    FOOTER                                      |
+--------------------------------------------------------------------------------+
```

---

## 6. Strict Compliance Audit (`AGENTS.md`)

### 📐 CSS Logical Properties
- **Margin & Padding**: Purged all physical directional spacings. Left/right offsets are mapped to logical offsets:
  - `ml-4` $\rightarrow$ `ms-4` (margin-inline-start)
  - `pr-6` $\rightarrow$ `pe-6` (padding-inline-end)
  - `mr-auto` $\rightarrow$ `me-auto` (margin-inline-end)
- **Positioning**: Absolute positioning elements use `start-0` / `end-0` (inset-inline-start/end) instead of `left-0` / `right-0`.
- **Dimensions**: Visual bounding boxes specify logical dimensions via style sheets or inline styling attributes (e.g. `style={{ inlineSize: "3rem", blockSize: "3rem" }}` or `style={{ minBlockSize: "140px" }}`).

### ✍️ Arabic Typography
- **Font Stack**: Wired directly to optimized Next.js variables:
  ```css
  --font-arabic: var(--font-cairo), var(--font-tajawal), 'IBM Plex Arabic', sans-serif;
  ```
- **Font Size Boundaries**: No Arabic character is rendered below `14px` (`text-sm`). Technical tables and label legends inherit a strict `text-sm` limit.
- **Line Height**: Base text uses a `--line-height-base: 1.8` line-height variable, offering breathing space for Arabic diacritics.
- **Letter Spacing Purge**: The design does not use `tracking-` classes on Arabic pages. The following CSS directive has been integrated:
  ```css
  [dir="rtl"], [lang="ar"] {
    letter-spacing: normal !important;
  }
  ```

### 🧠 Cultural Ergonomics
- **Color Meanings**:
  - Green (`#10B981`): Success rate indicators, completed scrapes.
  - Black/Gold (`#060608` / `#D4AF37`): Primary brand luxury gradient, primary action controls.
  - Blue (`#3B82F6`): Running tasks, processing campaign indicators.
  - Red (`#EF4444`): Failed crawls requiring immediate user retry action.
- **Input Direction**: The search bar uses `dir="auto"`.
- **RTL Icon Support**: Toggle and back buttons use `.dir-icon` with `transform: scaleX(var(--text-x-direction))` to flip indicators dynamically when language toggles.
- **Mobile CTA Placement**: The primary action CTA is centered on mobile devices to facilitate easy right-handed thumb access, instead of being mirrored blindly to the corner.

---

## 7. Recommended Action Plan & Next Steps

We recommend that the **Implementer Agent** carries out the following steps:

1. **Update `frontend/src/app/globals.css`**:
   - Remove Google Font `@import url(...)` at line 1.
   - Rebind `--font-arabic` to utilize Next.js variables `var(--font-cairo), var(--font-tajawal)`.
   - Update `--line-height-base` to `1.8`.
   - Add `.w-logical-full { inline-size: 100%; }` and letter-spacing reset for RTL.

2. **Update `frontend/src/app/layout.tsx`**:
   - Change root element direction default from `dir="auto"` to `dir="rtl"` to avoid unstable page direction shifts.

3. **Create `frontend/src/app/dashboard/page.tsx`**:
   - Copy and paste the validated page template written to `.agents/teamwork_preview_explorer_m1_1/proposed_dashboard_page.tsx`.

4. **Extend Wasm SQLite Database Schema (`frontend/src/app/db/wasm-db.ts`)**:
   - Add a `local_scrapes` table to log individual scrapes:
     ```sql
     CREATE TABLE IF NOT EXISTS local_scrapes (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       company_name TEXT NOT NULL,
       job_title TEXT NOT NULL,
       source TEXT DEFAULT 'LinkedIn',
       status TEXT DEFAULT 'completed',
       scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
     );
     ```

---

## 8. Independent Verification Method
The dashboard configuration can be independently verified using the following steps:
1. **Compilation Check**: Run the build command directly using Node bypass to avoid Windows command separator path expansion errors:
   ```bash
   node node_modules/next/dist/bin/next build
   ```
2. **AST Linting**: Validate compliance with TypeScript strict parameters:
   ```bash
   npm run lint
   ```
3. **Responsive Visual Review**: Verify that the SVG chart scales on smaller devices and that the table handles scroll behavior on horizontal axes without overflowing the parent container.
