# Task: Implement Next.js Dashboard and Style Overrides

You are Worker 1. Your task is to implement the frontend dashboard view and style overrides for the Next.js workspace under `frontend/` directory.

## Objective
Carry out the following implementations and configurations:
1. **File modifications**:
   - **`frontend/src/app/globals.css`**:
     - Remove the web font `@import url(...)` at the top.
     - Connect Next.js Google font variables to the font stack: `--font-arabic: var(--font-cairo), var(--font-tajawal), 'IBM Plex Arabic', sans-serif;`
     - Enforce line height `--line-height-base: 1.8;`
     - Enforce logical inline dimensions on input elements: `.input-field { inline-size: 100%; ... }` (instead of `width: 100%`).
     - Disable letter spacing on RTL/Arabic elements: `[dir="rtl"], [lang="ar"] { letter-spacing: normal !important; }`.
   - **`frontend/src/app/layout.tsx`**:
     - Modify root `<html>` tag to use default stable direction `dir="rtl"` (instead of `dir="auto"`).
   - **`frontend/src/app/page.tsx`**:
     - Ensure forms and email/password inputs are correctly formatted (e.g. email/password explicitly `dir="ltr"`, name fields `dir="auto"`, text size raised from `text-xs` to `text-sm` for legibility).
   - **`frontend/src/app/dashboard/page.tsx`**:
     - Create this new page. Use the proposed implementation written by Explorer 1 at `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_explorer_m1_1\proposed_dashboard_page.tsx`.
2. **Build and verification**:
     - Compile the application using the ampersand path separator bypass:
       `node node_modules/next/dist/bin/next build` inside the `frontend/` folder.
     - Make sure the build compiles successfully without errors.

## Scope Boundaries
- Do NOT add any external npm packages or UI libraries. Use pure HTML elements and Tailwind classes.
- Ensure all implementations are genuine and follow standard TypeScript patterns. Do not bypass typescript compiler checks or use placeholder code.

## Output Requirements
Write `handoff.md` in your working directory `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\teamwork_preview_worker_m2\` containing:
- Summary of changes made (files modified and created).
- Command executed for build check and verification logs.
- Confirmation that the build succeeded.

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
