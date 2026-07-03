# Adversarial Style Review — Milestone 2

## Challenge Summary

**Overall risk assessment**: MEDIUM
- **Logical Properties**: **PASS** for the requested files (`style.css`, `index.css`, `tailwind_overrides.css`, and `premium-ui.css`), which are completely free of physical directional properties. However, **FAIL** on optional files (`auth-v2.css`, `dashboard-v4.css`, `landing-v4.css`) which still contain physical layout properties (`margin-left`, `margin-right`, `left`, `right`).
- **Arabic Typography & Constraints**: **FAIL**. Multiple components (e.g. `.blog-card-meta`, `.post-meta`, `.topic-badge`, `.footer-tagline` in `style-rtl.css` and `.form-label`, `.stat-label` in `premium-ui-rtl.css`) have explicit `font-size` declarations below `14px` (specifically 12px or 13px) and `line-height` below `1.6` (specifically 1.3 or 1.4). This violates the Arabic legibility constraints defined in `AGENTS.md`.

---

## Challenges

### [Medium] Challenge 1: Inherited Arabic Font Size & Line Height Overridden by Specific Selectors
- **Assumption challenged**: That setting `font-size: 16px; line-height: 1.8;` on the `[dir="rtl"]` root selector is sufficient to enforce the Arabic typography constraints.
- **Attack scenario**: Specific selectors like `.blog-card-meta` (12px), `.post-meta` (13px), and `.topic-badge` (12px) declare their own `font-size` and `line-height`. Due to CSS specificity rules, these specific rules override the root container inherited properties. When rendered in Arabic, these text elements will display at 12px/13px, causing poor legibility.
- **Blast radius**: Low-level text elements, tags, badges, and metadata containers across the blog and dashboard layouts will be rendered in illegible/cramped Arabic script.
- **Mitigation**: Add a utility reset for RTL text elements to scale up their font sizes to a minimum of 14px and line-heights to 1.6 - 2.0, or update the specific selectors to use relative units (`em`/`rem`) and scale them appropriately in RTL stylesheets.

### [Medium] Challenge 2: Letter Spacing Applied to Arabic Buttons and Labels
- **Assumption challenged**: That setting letter-spacing to `normal !important` on `[dir="rtl"] *` is a foolproof way to prevent letter-spacing on Arabic text.
- **Attack scenario**: Properties like `.btn-premium` and `.stat-label` in `premium-ui.css` declare `letter-spacing: 1px`. In RTL mode, although overridden by the `!important` reset, this introduces a dependency on the global reset selector running last and not being overridden by more specific selectors. Furthermore, some tools or users might remove the `[dir="rtl"] *` rule to optimize performance, immediately breaking Arabic cursive letter connections.
- **Blast radius**: Cursive letters in Arabic buttons and labels will decouple/separate, rendering the text incorrect and highly unprofessional.
- **Mitigation**: Remove physical `letter-spacing` declarations from shared stylesheets or explicitly declare `letter-spacing: 0` or `letter-spacing: normal` within the `.btn-premium` and `.stat-label` selectors when targeted under RTL scopes.

### [Low] Challenge 3: Physical Properties Remaining in Optional/Non-refactored Stylesheets
- **Assumption challenged**: That the refactoring of Milestone 2 was complete for the entire styling directory.
- **Attack scenario**: Code from `auth-v2.css`, `dashboard-v4.css`, and `landing-v4.css` still uses physical `margin-left`, `margin-right`, `left`, and `right` coordinates. Under RTL layout execution, these components will not align properly, leading to layout breakage or overlapping elements.
- **Blast radius**: Authentication screens, dashboards, and landing page sections will suffer from misaligned cards, overlapping input toggles, and uneven margins.
- **Mitigation**: Convert the remaining stylesheets (`auth-v2.css`, `dashboard-v4.css`, `landing-v4.css`) to use CSS Logical Properties (`margin-inline`, `padding-inline`, `inset-inline-start`, `inset-inline-end`).

---

## Stress Test Results

- **LTR logical property conversion** → Checked requested files (`style.css`, `index.css`, `tailwind_overrides.css`, `premium-ui.css`) → Found `0` physical directional properties → **PASS**
- **Arabic minimum font-size (>= 14px)** → Checked elements inside RTL files → Found violations in `.blog-card-meta` (12px), `.post-meta` (13px), `.topic-badge` (12px), `.related-card p` (13px), `.footer-tagline` (12px), `.form-label` (13.6px/0.85rem), and `.stat-label` (13.6px/0.85rem) → **FAIL**
- **Arabic line-height (1.6 to 2.0)** → Checked elements inside RTL files → Found violations in `.blog-card h2` (1.4), `.post-header h1` (1.3), `h1, h2, h3, h4, h5, h6` (1.3), and `.stat-value` (1.1) → **FAIL**
- **Arabic letter-spacing reset** → Checked elements inside RTL files → Found `letter-spacing: 1px` declarations in `.btn-premium` and `.stat-label` → **FAIL** (mitigated only by `!important` global reset)

---

## Unchallenged Areas

- **Dynamic JavaScript-driven style injections** — Insufficient context / out of scope. We only parsed static `.css` stylesheets.
