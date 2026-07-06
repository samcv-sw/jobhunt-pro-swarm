## 2026-07-05T17:01:01Z
Your role is teamwork_preview_worker for Milestone 4 (Styling Hardening). Your working directory is c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_milestone4_style\.
Your task is to fix the remaining styling physical gradient values and Arabic readability issues (font-sizes and line-heights) identified by Challenger 1 and 2 in the legacy templates stylesheet files (under web/static/css/).

Please execute the following:
1. Refactor web/build_rtl_css.py:
   - Update the conversion logic to swap 'to right' with 'to left' (and vice versa) inside linear-gradient values to mirror gradient directions in RTL.
   - Add a post-process regex translation step to scale up any font sizes below 14px in the generated RTL stylesheets (e.g., replace '12px', '13px' with '14px', and '0.85rem' with '0.875rem').
   - Add a regex translation step to scale up any unitless line-height values below 1.6 in the generated RTL stylesheets (e.g., replace '1.1', '1.3', '1.4' with '1.6').
2. Regenerate CSS:
   - Execute python web/build_rtl_css.py to regenerate all '-rtl.css' files.
3. Verify CSS Correctness:
   - Run python .agents/challenger_m2_2/verify_styles.py to check for physical layout properties and typography violations. Confirm that the number of violations in the target files (style.css, index.css, tailwind_overrides.css, premium-ui.css, and their RTL variants) is reduced to 0.
4. Run Tests:
   - Run python -m pytest tests/e2e/test_frontend.py to verify that all e2e frontend tests pass cleanly.
5. Report:
   - Write your implementation details, regenerated file diff summaries, audit script outcomes, and test results to handoff.md in your working directory. Notify the parent orchestrator via send_message when complete.

MANDATORY INTEGRITY WARNING:
> DO NOT CHEAT. All implementations must be genuine. DO NOT
> hardcode test results, create dummy/facade implementations, or
> circumvent the intended task. A Forensic Auditor will independently
> verify your work. Integrity violations WILL be detected and your
> work WILL be rejected.
