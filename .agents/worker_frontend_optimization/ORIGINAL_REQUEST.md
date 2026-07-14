## 2026-07-14T07:48:36Z
You are the Frontend Optimization Worker for JobHunt Pro.
Your working directory is: C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_frontend_optimization

Your task is to implement the frontend UI/UX compliance changes:

1. RTL Font-Size Overrides (in `frontend/src/app/globals.css`):
   - Add explicit RTL selectors to force `.btn-gold`, `.input-field`, and the SVG chart labels `.text-\[14px\]` to render at `16px` (e.g. `font-size: 16px !important;` or `1rem !important;`) in RTL mode (`[dir="rtl"]`), fulfilling the minimum 16px font-size Arabic script legibility requirement.

2. CSS Logical Sizing (in `frontend/src/components/SkeletonLoader.tsx`):
   - Replace the Tailwind physical width class `w-full` on lines 31 and 43 with inline styles `style={{ inlineSize: "100%" }}` to adhere strictly to CSS logical property layout guidelines.

3. Lint Warnings (in `frontend/next.config.ts`):
   - Add `/* eslint-disable @typescript-eslint/no-require-imports */` at the top of the file, or convert the `require` calls to standard ES module `import` statements to clear build-time linter warnings.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

After making the edits, run the build/tests (using `npm run build` and `npm test` or `pytest`) to verify all frontend styles compile correctly, eslint has zero warnings, and unit tests pass with zero regressions. Save a summary of your changes and test/build verification commands and outputs in C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_frontend_optimization\handoff.md.
Once complete, send a message back to the parent (id: 50dfdad3-d1a1-4c62-9adb-8213270599fb) with the path to your handoff.md and a brief summary of your verification results.
