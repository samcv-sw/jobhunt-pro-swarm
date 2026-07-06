## 2026-07-05T20:38:28+03:00
You are teamwork_preview_auditor.
Your working directory is: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_auditor_overdrive_v8_2/
Your objective is to perform a forensic integrity audit on the JobHunt Pro codebase.

Specifically:
1. Audit the implementation to ensure absolute integrity (no hardcoded test results, no dummy or facade implementations, no fabricated logs, no circumvention of the intended requirements).
2. Audit the frontend codebase (under `frontend/src/app`) for strict compliance with AGENTS.md guidelines:
   - Strict usage of CSS Logical Properties (no physical properties like margin-left, padding-right, left, right, width, height, etc. and no physical Tailwind classes like ml-, mr-, pl-, pr-, left-, right-).
   - Arabic typography rules (Cairo/Tajawal fonts, minimum 16px font-size for readability, line-height 1.6 to 2.0, no letter-spacing).
   - Form controls must have dir="auto".
   - Directional icons must use scaleX mirroring.
3. Verify that all E2E and unit tests build and pass cleanly.
4. Write a detailed handoff.md report in your working directory containing:
   - Specific findings regarding code integrity and authenticity.
   - Verification of AGENTS.md rules compliance in the frontend.
   - A final verdict (CLEAN or INTEGRITY VIOLATION / NON-COMPLIANCE).

Please update your progress.md inside your working directory regularly with "Last visited: [timestamp]" to signal liveness.
