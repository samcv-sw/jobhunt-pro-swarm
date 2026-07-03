# Plan - Frontend RTL & Glassmorphism Optimization

This plan outlines the steps for auditing and modifying CSS logical properties, refining glassmorphism UX, and validating the build of the Next.js app in `frontend/`.

## Phase 1: CSS Logical Properties Audit (Milestone 1)
1. **Explore**:
   - Spawn Explorer agents to locate physical directional CSS properties (e.g., `margin-left`, `margin-right`, `padding-left`, `padding-right`, `left`, `right`, `text-left`, `text-right`, `border-l`, `border-r`, etc.) in Tailwind classes and custom stylesheets within `frontend/src/`.
   - Explorer will propose transition mappings to CSS Logical Properties.
2. **Implement**:
   - Spawn a Worker agent to replace physical directional styles with logical properties (e.g., `margin-inline-start`, `padding-inline-end`, `inset-inline-start`, etc., and Tailwind equivalents like `ms-`, `pe-`, `ps-`, `me-`, `start-`, `end-`).
3. **Review**:
   - Spawn Reviewer agents to verify that no physical directional CSS properties are left and changes comply with code layout.
4. **Challenge**:
   - Spawn Challenger agents to test rendering under RTL layout context.
5. **Audit**:
   - Spawn a Forensic Auditor to ensure no cheating / hardcoding and that logical properties are authentically implemented.

## Phase 2: Glassmorphism UX Polish (Milestone 2)
1. **Explore**:
   - Spawn Explorer agents to inspect glassmorphism styles and fonts in `frontend/src/` to ensure Cairo/Tajawal fonts are used, minimum font size is 16px (14px min where allowed, but 16px recommended), line-height is 1.6-2.0, and form inputs use `dir="auto"`.
2. **Implement**:
   - Spawn a Worker agent to apply these enhancements.
3. **Review**:
   - Spawn Reviewer agents to check compliance with the Gulf cultural styling, RTL, and typography rules in `AGENTS.md`.
4. **Challenge**:
   - Spawn Challenger agents to verify readability and alignment.
5. **Audit**:
   - Spawn a Forensic Auditor to verify integrity and correctness.

## Phase 3: Build Validation (Milestone 3)
1. **Build & Verify**:
   - Run `npm run build` via a Worker to ensure the Next.js application builds cleanly.
2. **Review & Audit**:
   - Verify build outputs and run the final Forensic Auditor.
