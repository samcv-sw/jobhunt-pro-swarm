# Scope: JobHunt Pro Frontend Style Refactor

## Architecture
This sub-orchestrator is responsible for overhauling the CSS stylesheet system for JobHunt Pro. The main objectives are:
1. **Logical Properties Migration**: Eliminate physical directional properties (`margin-left`, `margin-right`, `padding-left`, `padding-right`, `left`, `right`, `width`, `height`) and replace them with logical counterparts (`margin-inline-start/end`, `padding-inline-start/end`, `inset-inline-start/end`, `inline-size`, `block-size`).
2. **Cohesive Glassmorphism Theme**: Define glassmorphism CSS variables and implement premium styling with backdrop-blur, saturate, border-transparency, and micro-animations.
3. **Arabic Typography Constraints**: Enforce Cairo, IBM Plex Arabic, or Tajawal font, minimum font-size of 14px (preferably 16px), line-height 1.6 to 2.0, and disable letter-spacing for Arabic text.
4. **Clean RTL/LTR Switching**: Support direction-aware styles dynamically using CSS variables, logical properties, and a `--text-x-direction` factor (1 for LTR, -1 for RTL).

### Interface CSS Variables
```css
:root {
  --text-x-direction: 1; /* Scaled to -1 in [dir="rtl"] */
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-blur: blur(12px) saturate(180%);
  --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
  --font-arabic: 'Cairo', 'IBM Plex Arabic', 'Tajawal', sans-serif;
}

[dir="rtl"] {
  --text-x-direction: -1;
}
```

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID / Comments |
|---|------|-------|-------------|--------|----------------------------|
| 1 | Exploration & Audit | Perform deep static analysis of CSS files to compile physical property and typography violations. | None | DONE | b9513c49-ec42-4853-b30b-45040293d0af |
| 2 | Core & Variables | Setup CSS variables in `style.css`/`premium-ui.css` and refactor `style.css`, `index.css`, `tailwind_overrides.css`, and their RTL counterparts. | M1 | IN_PROGRESS | |
| 3 | Auth Pages Refactor | Refactor `auth-v2.css` and `auth-v2-rtl.css` for logical layouts and glassmorphism. | M2 | PLANNED | |
| 4 | Landing Page Refactor | Refactor `landing-v4.css` and `landing-v4-rtl.css` with premium visual styles. | M2 | PLANNED | |
| 5 | Dashboard Pages Refactor| Refactor `dashboard-v4.css` and `dashboard-v4-rtl.css` for complex layout logical properties. | M2 | PLANNED | |
| 6 | Cyberpunk Theme Refactor| Refactor `cyberpunk.css` and `cyberpunk-rtl.css` with futuristic styles using logical properties. | M2 | PLANNED | |
| 7 | Integration & Verification| Perform automated auditing, visual sanity checks, and logic compliance verification across all stylesheets. | M3, M4, M5, M6 | PLANNED | |

## Interface Contracts
- **Direction Switching**: Checked via html `[dir]` attribute. The stylesheets must not duplicate styles for RTL unless overrides are absolutely necessary; logical properties should resolve direction natively.
- **Directional Icons**: Apply `transform: scaleX(var(--text-x-direction))` to elements containing arrows, page turns, or directional icons.
