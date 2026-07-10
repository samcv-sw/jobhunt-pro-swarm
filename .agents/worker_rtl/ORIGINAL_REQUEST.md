## 2026-07-10T18:49:39Z

You are the Worker. Your working directory is c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_rtl.
Your task is to implement the RTL & Localization Optimization fixes for JobHunt Pro.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Detailed requirements:

1. Jinja2 Templates:
   - In forgot_password.html, login.html, reset_password.html (both root templates and the 'en/' variants), update the `.btn-submit::before` transition style property from `transition: left 0.5s ease;` to `transition: inset-inline-start 0.5s ease;` to fix transitions when layout direction changes.
   - In `web/templates/en/_sidebar_head.html`, update `.notif-panel` transition from `transition: right .3s ease;` to `transition: inset-inline-end 0.3s ease;`.
   - Update `web/templates/_sidebar_head.html` to set global line-height to `1.7` (or `1.8`) for `[dir="rtl"]` / Arabic context, and ensure list items and paragraph blocks in Arabic templates use `1.7-2.0` line height instead of LTR values (like `1.45`, `1.5`, `1.6`).
   - In `_dashboard_shell.html`, wrap Arabic strings (like "رصيد" and "حالة النظام: ممتاز ●") in elements that override `font-family: monospace` to use `'Cairo', 'Tajawal', sans-serif` instead.
   - Replace hardcoded unicode arrows (`←`, `→`) in templates (`tracking_analytics.html`, `track_application.html`, `trust.html`, `_dashboard_shell.html`) with Lucide icons using `class="lucide-dir-aware"` (e.g. `<i data-lucide="arrow-left" class="lucide-dir-aware inline-block w-4 h-4 align-middle"></i>` or `<i data-lucide="arrow-right" class="lucide-dir-aware inline-block w-4 h-4 align-middle"></i>`).

2. Inline HTML in Python files:
   - In `web/app_v2.py`, replace physical spacing/border/alignment rules in inline HTML builders with CSS Logical Properties:
     - `margin-left: 16px;` -> `margin-inline-start: 16px;`
     - `margin-left:12px;` -> `margin-inline-start:12px;`
     - `margin-left: auto; margin-right: auto;` -> `margin-inline: auto;`
     - `padding-left: 20px;` -> `padding-inline-start: 20px;`
     - `padding-left:16px` -> `padding-inline-start:16px`
     - `text-align:left;` -> `text-align: start;`
     - `text-align:right;` -> `text-align: end;`
     - `border-right:1px solid #e2e8f0` -> `border-inline-end:1px solid #e2e8f0`
   - In `web/_build_index.py`, replace `margin-left:auto;margin-right:auto` with `margin-inline:auto` (Line 88).
   - In `web/_build_templates.py`, replace `text-align: right` with `text-align: end` (Line 69).

3. Vue Frontend (frontend-vue/):
   - In `App.vue`:
     - Convert `margin: 0;` (in body) to `margin-block: 0; margin-inline: 0;`.
     - Remove `font-family: 'Inter', 'Roboto', sans-serif;` from `App.vue` to allow global font fallbacks.
   - In `views/Dashboard.vue`:
     - Refactor scoped styles block:
       - `padding: 2rem;` -> `padding-block: 2rem; padding-inline: 2rem;`
       - `max-width: 1200px;` -> `max-inline-size: 1200px;`
       - `margin: 0 auto;` -> `margin-block: 0; margin-inline: auto;`
       - `margin-bottom: 2rem;` -> `margin-block-end: 2rem;`
       - `margin-bottom: 0.5rem;` -> `margin-block-end: 0.5rem;`
       - `padding: 1.5rem;` -> `padding-block: 1.5rem; padding-inline: 1.5rem;`
       - `margin: 0 0 1rem 0;` -> `margin-block: 0 1rem; margin-inline: 0;`
       - `height: 500px;` -> `block-size: 500px;`
       - `width: 100%;` -> `inline-size: 100%;`
       - `height: 100%;` -> `block-size: 100%;`
     - Implement dynamic LTR/RTL configuration for ECharts in `views/Dashboard.vue` by reading `document.documentElement.dir === 'rtl'` to set alignment properties (like title alignment `left`/`right`, etc.).
   - In `frontend-vue/src/style.css`:
     - Set up the global direction flipping variable:
       ```css
       :root {
         --text-x-direction: 1;
       }
       [dir="rtl"] {
         --text-x-direction: -1;
       }
       ```
     - Mirror directional icons by adding:
       ```css
       .icon.directional {
         transform: scaleX(var(--text-x-direction));
       }
       ```
     - Add:
       ```css
       :root:lang(ar),
       [dir="rtl"] {
         --sans: 'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif;
         --heading: 'Cairo', 'Tajawal', 'IBM Plex Arabic', sans-serif;
         font: 18px/1.8 var(--sans);
         letter-spacing: 0;
       }
       ```
   - In `HelloWorld.vue`, add the `directional` class to the documentation chevron icon.

4. Global Stylesheets (web/static/css/):
   - In `auth-v2.css`, `cyberpunk.css`, `dashboard-v4.css`, `landing-v4.css`:
     - Add the `[dir="rtl"]` font override block:
       ```css
       [dir="rtl"] {
         --font-sans: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif;
         --font-display: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif;
         --cyber-font-display: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif;
         font-size: 16px;
         line-height: 1.8;
       }
       [dir="rtl"] h1, [dir="rtl"] h2, [dir="rtl"] h3, [dir="rtl"] h4, [dir="rtl"] h5, [dir="rtl"] h6 {
         line-height: 1.6;
       }
       ```
   - In `landing-v4.css` (Line 2204), replace `transition: left 0.5s` with `transition: inset-inline-start 0.5s`.
   - In `auth-v2.css` (Line 311), replace `margin: -10px 0 0 -10px` with logical margins: `margin-block-start: -10px; margin-inline-start: -10px;`.
   - In transition animations inside `dashboard-v4.css`, `cyberpunk.css`, and `landing-v4.css`, update `transform: translateX(...)` values to use `calc(... * var(--text-x-direction))`.
     - In `dashboard-v4.css` (Lines 135, 148, 226, 244, 287, 298, 896), `landing-v4.css` (Lines 285, 298, 336, 347, 541, 549), `cyberpunk.css` (Lines 1133, 1137, 1377), and `auth-v2.css` (Lines 358–370).
     - Define `--text-x-direction` variable in `:root` (`1`) and `[dir="rtl"]` (`-1`) in these stylesheets.
   - For all stylesheets, replace hardcoded degrees or directions in `linear-gradient` calls with `var(--gradient-dir)` where appropriate. Let's make sure:
     - In `:root`, `--gradient-dir` defaults to `to right` (or standard angle like `90deg` or `135deg`).
     - In `[dir="rtl"]`, `--gradient-dir` is overridden to `to left` (or negative angles like `-90deg` or `-135deg`).

5. CSS Generation and Testing:
   - Run the CSS build/rtl compilation script `web/build_rtl_css.py` to regenerate the `-rtl.css` files, and ensure they compile successfully.
   - Run the Next.js/Vue build if applicable or run `pytest` to make sure we didn't break any backend routes.

Write your changes and verification logs in `changes.md` and `handoff.md`. Notify the parent when complete.
Do not use placeholder code or dummy implementations. Ensure all modifications are fully functional.
