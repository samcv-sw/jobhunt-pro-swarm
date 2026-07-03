## 2026-07-03T09:41:26Z
You are the Style Refactoring Worker for Milestone 2.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_frontend_m2.
Your task is to refactor core CSS stylesheets to enforce CSS Logical Properties, dynamic LTR/RTL font setup, and premium glassmorphism.

Target Files to refactor:
1. web/static/css/style.css
2. web/static/css/index.css
3. web/static/css/tailwind_overrides.css
4. web/static/css/premium-ui.css

Core Refactoring Requirements:
1. CSS Variables & Typography Setup (in style.css and premium-ui.css):
   - Define `--text-x-direction: 1;` in `:root`.
   - Define `--text-x-direction: -1;` in `[dir="rtl"]`.
   - Define glassmorphism tokens in `:root`:
     `--glass-bg: rgba(255, 255, 255, 0.05);`
     `--glass-border: rgba(255, 255, 255, 0.1);`
     `--glass-blur: blur(12px) saturate(180%);`
     `--glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);`
   - Define font-sans dynamically:
     `:root { --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }`
     `[dir="rtl"] { --font-sans: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif; }`
     Apply `font-family: var(--font-sans);` to body and appropriate selectors.
   - Enforce Arabic Typography constraints:
     - Minimum font-size of 14px (preferably 16px) for selectors displaying Arabic text.
     - Line-height between 1.6 and 2.0.
     - Add the letter-spacing reset to premium-ui.css:
       `[dir="rtl"] *, :lang(ar) *, :lang(ar) { letter-spacing: normal !important; }`
2. CSS Logical Properties:
   - Identify and replace physical layout rules with logical equivalents:
     - margin-left/right -> margin-inline-start/end
     - padding-left/right -> padding-inline-start/end
     - left/right (positioning) -> inset-inline-start/end
     - width/height -> inline-size/block-size
     - border-left/right -> border-inline-start/end
     - text-align: left/right -> text-align: start/end
3. Directional Icons & Micro-animations:
   - Standardize transform: scaleX(var(--text-x-direction)) on .dir-icon and elements representing direction.
   - Ensure premium glassmorphism classes utilize the glass variables and contain subtle hover transition styles (micro-animations).
4. Compilation & Output:
   - Run the Python script: `python web/build_rtl_css.py` from the project root to generate/update style-rtl.css, index-rtl.css, tailwind_overrides-rtl.css, and premium-ui-rtl.css.
   - Double check the generated outputs are compilable and contain logical rules.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

When finished, write a detailed handoff.md in your working directory and notify the sub-orchestrator (Conv ID: d862a488-6582-4ff2-b029-8c5f6e3eff43) via a message.
