# Detailed UI/UX Baseline Audit Report

## 1. Summary of Findings
- **CSS Logical Properties**: The Jinja2 templates (`web/templates/` and `web/templates/en/`) and Next.js frontend pages (`frontend/src/app/page.tsx` and `globals.css`) have already been extensively refactored to use CSS Logical Properties (such as `margin-inline-start`, `padding-inline-end`, `inset-inline-start`, `inset-inline-end`, `inline-size`, and `block-size`). No physical left/right styling exists in the CSS files themselves.
- **Arabic Font Stack Consistency**: 
  - The correct Arabic font stack (`'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif`) is defined in the root variables for RTL layouts (`globals.css` and `style.css`).
  - However, the Tailwind CDN configuration in `web/templates/_base_tailwind.html` only specifies `['Cairo', 'sans-serif']` and misses `Tajawal` and `'IBM Plex Arabic'`.
  - Many individual Jinja2 templates override the font stack in `<style>` blocks or style attributes using partial stacks like `'Cairo', 'Inter'` or `'Cairo', 'Segoe UI'` instead of the standard Gulf-readability stack.
- **RTL Typography Constraints**: 
  - Font sizes are successfully forced to >= 16px (exceeding the min 14px limit) in RTL viewports via `globals.css`.
  - Line-height is consistently set to `1.8` (meeting the 1.6 to 2.0 range requirement).
  - Letter-spacing is overridden to `normal !important` (zero letter-spacing) for all RTL and Arabic elements in base CSS and inline definitions, preventing cursive joining bugs.
- **Next.js Frontend Analysis**: 
  - Layout is fully logical and direction-independent.
  - It utilizes modern dark glassmorphism styling via the `.glass-panel` class with transitions (opacity, translateY hover animations, border glow) and custom scrollbars.
  - One minor bug discovered in LTR Base: `web/templates/en/base.html` redundantly preloads/imports `index-rtl.css` prior to `index.css`.

---

## 2. Files Requiring Modification

### 2.1 CSS / Template Base Config
1. **`web/templates/_base_tailwind.html`**
   - **Issue**: Tailwind configuration defines `sans: ['Cairo', 'sans-serif']` instead of the full font stack.
   - **Fix**: Update Tailwind `fontFamily` definition to include `Tajawal` and `IBM Plex Arabic`.

2. **`web/templates/en/base.html`**
   - **Issue**: Redundant loading of `index-rtl.css` in an English-only base template.
   - **Fix**: Remove line 23: `<link rel="stylesheet" href="/static/css/index-rtl.css">`.

### 2.2 Template Inline Font Stack Refactoring (37 files)
These files define a custom `font-family` that is incomplete (omitting `Tajawal` or `IBM Plex Arabic`, or adding LTR fonts like `Inter` and `Segoe UI` for text layouts in RTL). The stack must be unified to `'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif` for consistency:
- `web/templates/_dashboard_shell.html` (Lines 27, 91)
- `web/templates/_public_nav.html` (Line 3)
- `web/templates/_public_shell.html` (Lines 84, 136, 139, 185, 232)
- `web/templates/_sidebar_head.html` (Lines 203, 292)
- `web/templates/admin.html` (Lines 6, 49, 56, 99, 208)
- `web/templates/admin_analytics.html` (Line 6)
- `web/templates/admin_user.html` (Lines 6, 26)
- `web/templates/antigravity.html` (Lines 22, 58, 69, 98, 144, 163, 186)
- `web/templates/api_docs.html` (Lines 16, 32, 37, 42, 51, 54, 59)
- `web/templates/battle_station.html` (Lines 28, 52, 204)
- `web/templates/blog.html` (Line 21)
- `web/templates/checkout_v2.html` (Line 363)
- `web/templates/contact.html` (Line 7)
- `web/templates/dashboard_v2.html` (Line 26)
- `web/templates/dashboard_v3.html` (Line 34)
- `web/templates/email_test.html` (Line 10)
- `web/templates/employer_track.html` (Line 22)
- `web/templates/interview_prep.html` (Line 20)
- `web/templates/kanban_board.html` (Line 21)
- `web/templates/login.html` (Line 12)
- `web/templates/my_purchases.html` (Line 21)
- `web/templates/new_campaign_v2.html` (Line 21)
- `web/templates/roast.html` (Line 20)
- `web/templates/stats.html` (Line 16)
- `web/templates/upload_cv_v2.html` (Line 21)
- `web/templates/upload_cv_v3.html` (Line 21)
- `web/templates/wallet.html` (Line 21)
- `web/templates/war_room.html` (Line 21)

---

## 3. Step-by-Step Refactoring Strategy

### Step 1: Clean Up Redundant CSS Reference
Modify `web/templates/en/base.html` to remove the import of `index-rtl.css`, preventing unwanted styling leaks for LTR-only layout.

### Step 2: Update Tailwind Base Configuration Font-Family
Update the inline Tailwind configuration script in `web/templates/_base_tailwind.html` to define the full Arab-Gulf font stack:
```javascript
fontFamily: {
    sans: ['Cairo', 'Tajawal', 'IBM Plex Arabic', 'sans-serif'],
    display: ['Cairo', 'Tajawal', 'IBM Plex Arabic', 'sans-serif'],
    mono: ['Fira Code', 'monospace'],
}
```

### Step 3: Global Search and Replace of Incomplete Font Stacks
Use a script (similar to the existing `web/templates/localize.py`) to parse the HTML templates under `web/templates/` (excluding `/en/`) and update all custom font stack variations:
- Change `'Cairo', sans-serif` -> `'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif`
- Change `'Cairo', 'Inter', sans-serif` -> `'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif`
- Change `'Cairo', 'Segoe UI', sans-serif` -> `'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif`
- Change `'Cairo', 'Tajawal', sans-serif` -> `'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif`

### Step 4: Verification and Visual Review
1. Load both RTL (Arabic) and LTR (English) templates locally.
2. Confirm that there are no layout shifts when toggling languages.
3. Validate that letter-spacing is correctly ignored/zeroed in all Arabic script renders.
4. Verify Next.js page matches these settings.
