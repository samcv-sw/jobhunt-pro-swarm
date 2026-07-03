## 2026-07-03T09:49:09Z

You are the Style Refactoring Worker for Milestone 2 Fixes.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_frontend_m2_fix.
Your mission is to fix the physical property and Arabic typography/legibility constraint violations identified by the Challengers in Milestone 2.

Target Files to modify:
1. web/static/css/index.css
2. web/static/css/style.css
3. web/static/css/premium-ui.css

Core Fix Requirements:
1. Physical Property in index.css (line 107):
   - The `.skeleton` linear gradient background currently uses `linear-gradient(to right, ...)`.
   - To make it logical and free of physical properties:
     - Define `--gradient-dir: to right;` in `:root`.
     - Define `--gradient-dir: to left;` in `[dir="rtl"]`.
     - Modify the linear gradient on line 107 of `index.css` to use `linear-gradient(var(--gradient-dir), ...)`.
2. Arabic Typography Constraints in style.css:
   - Add specific `[dir="rtl"]` overrides at the end of `style.css` to ensure Arabic text has a minimum font-size of 14px and line-height of 1.6 to 2.0.
   - Add overrides for the following selectors:
     - `[dir="rtl"] .blog-card-meta { font-size: 14px; }`
     - `[dir="rtl"] .blog-card h2 { line-height: 1.6; }`
     - `[dir="rtl"] .post-meta { font-size: 14px; }`
     - `[dir="rtl"] .post-header h1 { line-height: 1.6; }`
     - `[dir="rtl"] .topic-badge { font-size: 14px; }`
     - `[dir="rtl"] .related-card p { font-size: 14px; }`
     - `[dir="rtl"] .footer-tagline { font-size: 14px; }`
3. Arabic Typography Constraints in premium-ui.css:
   - Add specific `[dir="rtl"]` overrides at the end of `premium-ui.css` to ensure Arabic text has a minimum font-size of 14px and line-height of 1.6 to 2.0.
   - Add overrides for the following selectors:
     - `[dir="rtl"] h1, [dir="rtl"] h2, [dir="rtl"] h3, [dir="rtl"] h4, [dir="rtl"] h5, [dir="rtl"] h6 { line-height: 1.6; }`
     - `[dir="rtl"] .form-label { font-size: 14px; }`
     - `[dir="rtl"] .stat-value { line-height: 1.6; }`
     - `[dir="rtl"] .stat-label { font-size: 14px; letter-spacing: normal !important; }`
     - `[dir="rtl"] .btn-premium { letter-spacing: normal !important; }`
4. Compilation & Output:
   - Run the Python script: `python web/build_rtl_css.py` from the project root to generate/update the `-rtl.css` files.
   - Double check the generated outputs are compilable and contain logical rules.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

When finished, write a detailed handoff.md in your working directory and notify the sub-orchestrator (Conv ID: d862a488-6582-4ff2-b029-8c5f6e3eff43) via a message. Do not write placeholder code.
