# Scope: Frontend UI/UX, Glassmorphism, & RTL Polish

## Overview
Polish frontend layouts, styles, and typography in `frontend/src/` to ensure full logical spacing compliance, smooth transitions, premium glassmorphism effects, and responsiveness on all devices.

## Requirements & Fixes
1. **Logical Sizing utilities**: Audit files (like `frontend/src/app/page.tsx`, `frontend/src/app/dashboard/page.tsx`, `frontend/src/app/layout.tsx`) and replace physical sizing classes (`w-*`, `h-*`) with logical dimension counterparts using CSS inline styles (e.g. `style={{ inlineSize: "...", blockSize: "..." }}`) or custom Tailwind logical sizing utilities.
2. **Arabic Typography Guidelines**:
   - Scale up any sub-16px Arabic text elements (such as status badges, info boxes, metric metadata timestamps, recommendation text) to at least 14px (preferably 16px).
   - Set logical line-heights explicitly to `1.8 - 2.0` (using Tailwind class `leading-[1.8]` or custom rules) for these elements.
   - Remove `tracking-tight` from any heading or span containers holding Arabic text.
3. **Form Directionality**: Add `dir="auto"` to the outer `<form>` elements (such as the SMTP form in `page.tsx`).
4. **HTML Lang Attribute**: In `layout.tsx`, ensure the `<html>` root element dynamically adjusts `lang` (e.g., `lang={locale}`) and direction based on the current user locale state instead of remaining static.
5. **Glassmorphism Paint Performance**: Modify `globals.css` to animate hover shadow overlays using the GPU compositor (by transitioning `opacity` of a `::after` pseudo-element) rather than transitioning the `box-shadow` directly, which triggers CPU paint cycles.

## Complete Criteria
- Zero physical sizing/layout styling in templates/stylesheets.
- Next.js successfully compiles without shell errors (`node node_modules/next/dist/bin/next build` inside `frontend/`).
