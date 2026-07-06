## Challenge Summary

**Overall risk assessment**: MEDIUM

## Challenges

### [Medium] Challenge 1 — HTML/Body Direction Contradiction

- **Assumption challenged**: Setting `dir="auto"` on `<body>` will automatically resolve layout alignment for both LTR and RTL content.
- **Attack scenario**: A user loads the website in Arabic. However, the first elements inside the `<body>` that contain text are English (e.g. tracking scripts, developer logging libraries, meta attributes, or inline CSS with unescaped texts). The browser evaluates `<body>` as `ltr`. Because the body has `dir="auto"`, this local setting overrides the inherited `dir="rtl"` dynamic direction from `<html>` (set by `RootHtml`). Consequently, layout elements that do not explicitly force direction (or rely on layout flex/grid direction inheriting from body) align to the left, resulting in broken visual aesthetics or misplaced overlays.
- **Blast radius**: Arabic layouts, global page wrapper spacing, third-party component wrappers.
- **Mitigation**: Remove `dir="auto"` from the `<body>` in `layout.tsx`. Keep `dir="auto"` strictly on forms, inputs, and textareas where dynamic user input requires contextual evaluation.

### [Low] Challenge 2 — Text Scaling / Legibility in Older Browser Versions

- **Assumption challenged**: All font scaling in `globals.css` uses relative typography that adapts gracefully.
- **Attack scenario**: A user is viewing the website on a device with highly customized font accessibility settings or an older mobile webview where Cairo is not loaded properly. The `.btn-gold` class uses `font-size: 0.875rem` (14px). If the browser base font size is changed or default font fallback changes, the text could become illegible or layout overflow could occur on primary action buttons due to lack of minimum line-height or hardcoded button paddings (`padding-inline: 1.25rem`).
- **Blast radius**: Accessibility compliance on primary buttons.
- **Mitigation**: Verify that buttons wrap text correctly and specify responsive/min sizing configurations.

## Stress Test Results

- **Run Next.js Production Build** → Successfully completed without any TypeScript or bundling failures.
- **Run E2E Test Runner** → Completed 115 tests successfully. `test_frontend.py` ran all assertions validating typography rules, physical properties avoidance, and layout logical property checks.

## Unchallenged Areas

- Core backend data structures and database operations were out of scope for this task and not challenged.
