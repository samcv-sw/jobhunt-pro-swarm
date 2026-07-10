# RTL and Localization Compliance Audit Report

This report presents findings from an audit of the Jinja2 templates (in `web/templates/` and `web/templates/en/`) and Python web application code (primarily `web/app_v2.py`) for RTL (Right-to-Left) and localization compliance.

---

## Executive Summary
The application has done an excellent job of using CSS logical properties (`margin-inline-start`, `inset-inline-end`, etc.) and enforcing `dir="auto"` on all static inputs and textareas. However, there are a few physical styling rules remaining in CSS transitions and inline Python HTML builders, and several templates do not meet the minimum Arabic readability threshold for line height (1.7 - 2.0).

---

## 1. Physical Styling Rules
We searched for physical styling keywords (`margin-left`, `margin-right`, `padding-left`, `padding-right`, `left`, `right`, `text-align: left`, `text-align: right`) in style attributes and `<style>` blocks.

### 1.1 Mismatched CSS Transition Properties
Several templates utilize logical properties for positioning, but their corresponding CSS transition properties still reference physical properties. This leads to inactive or broken transitions when direction changes:
- **`btn-submit` Hover Shine Effect:**
  - Files:
    - `web/templates/forgot_password.html` (Line 176)
    - `web/templates/en/forgot_password.html` (Line 171)
    - `web/templates/login.html` (Line 78)
    - `web/templates/en/login.html` (Line 76)
    - `web/templates/reset_password.html` (Line 190)
    - `web/templates/en/reset_password.html` (Line 183)
  - Code:
    ```css
    .btn-submit::before {
        position: absolute; top: 0; inset-inline-start: -100%; ...
        transition: left 0.5s ease; /* Physical transition on logical property! */
    }
    .btn-submit:hover::before { inset-inline-start: 100%; }
    ```
  - Fix: Change to `transition: inset-inline-start 0.5s ease;` (or `transition: all 0.5s ease;`).

- **`notif-panel` Slide Effect:**
  - File: `web/templates/en/_sidebar_head.html` (Line 1136)
  - Code:
    ```css
    .notif-panel {
        position: fixed; top: 0; inset-inline-end: -380px; ...
        transition: right .3s ease; /* Physical transition on logical property! */
    }
    ```
  - Fix: Change to `transition: inset-inline-end 0.3s ease;` (which is correctly done in the default Arabic version `web/templates/_sidebar_head.html` line 1171).

### 1.2 Inline HTML Styles in Python Code (`web/app_v2.py`)
A significant number of physical styling rules are hardcoded inside Python-based HTML builders:
- **`margin-left` and `margin-right`:**
  - Line 2711: `.srv-price { margin-left: 16px; }`
  - Line 2972 & 3019: `<a href="/" ... style="margin-left:12px;">`
  - Line 4962: `<p style="... margin-left: auto; margin-right: auto;">` (should be `margin-inline: auto;`)
- **`padding-left`:**
  - Line 2689: `.pricing-card ul li { padding-left: 20px; }` (should be `padding-inline-start: 20px;`)
  - Line 2952: `<ul style="line-height:2;padding-left:20px;">` (should be `padding-inline-start: 20px;`)
  - Line 6657: `<ul style='margin:0;padding-left:16px'>` (should be `padding-inline-start: 16px;`)
  - Line 6664: `<ul style='padding-left:20px;margin:12px 0'>` (should be `padding-inline-start: 20px;`)
  - Line 6772: `<ul style="margin:0;padding-left:16px">` (should be `padding-inline-start: 16px;`)
  - Line 6782: `<ul style='padding-left:20px;margin:12px 0'>` (should be `padding-inline-start: 20px;`)
- **`text-align: left` and `text-align: right`:**
  - Line 2995, 2996, 2997: `<th style="text-align:left;padding:8px;color:#64748b;">` (should be `text-align: start;`)
  - Line 3034, 3041, 3048: `<div class="card" style="text-align:left; ...">` (should be `text-align: start;`)
  - Line 4963: `<div style="... text-align:left; ...">` (should be `text-align: start;`)
  - Line 6352, 6373, 6394, 6547: `<td style="text-align:right; ...">` (should be `text-align: end;`)
  - Line 7910: `label { text-align: left; }` (should be `text-align: start;`)
  - Line 8148: `th { text-align: left; }` (should be `text-align: start;`)
- **`border-right`:**
  - Line 6414, 6417, 6420, 6765: `<td style="... border-right:1px solid #e2e8f0">` (should be `border-inline-end: 1px solid #e2e8f0;`)

### 1.3 Other Script Files
- **`web/_build_index.py` (Line 88):** `.featured-grid { margin-left: auto; margin-right: auto; }` (should be `margin-inline: auto;`)
- **`web/_build_templates.py` (Line 69):** `.jc-time { text-align: right; }` (should be `text-align: end;`)

---

## 2. Arabic Font Styling and Readability
- **Font Face:** Arabic text uses `Cairo` and `Tajawal` fallback styles correctly.
- **Letter-Spacing:** Zero letter-spacing constraints are fully respected. No letter-spacing is applied to Arabic templates.
- **Line Heights (Audit Failure):**
  - **Global Dashboard:** In `web/templates/_sidebar_head.html` (Line 71), the global html/body line height is set to `1.65`, which is below the minimum Gulf region standard of `1.7`.
  - **Component Level:** Numerous elements across various Arabic HTML templates explicitly set or fall back to `line-height: 1.5` or `line-height: 1.6` for paragraphs and list items. Affected files include:
    - `checkout.html`, `checkout_v2.html`, `checkout_v3.html`
    - `email_test.html`
    - `employer_track.html`
    - `funnel_analytics.html`
    - `index_v2.html`, `index_v3.html`
    - `interview_prep.html`
    - `my_purchases.html`
    - `offers.html`
    - `pricing.html`, `pricing_v2.html`, `pricing_v3.html`
    - `referrals.html`
    - `services.html`
    - `terms.html`
    - `privacy.html`
- **Monospace Font Mismatch:**
  - In `web/templates/_dashboard_shell.html` (Lines 27 and 90), Arabic text (like "رصيد" and "حالة النظام: ممتاز ●") is wrapped inside elements styled with `font-family: monospace;`.

---

## 3. Dynamic and Static `dir="auto"` Compliance
- **JavaScript Injection:** `web/templates/_base_tailwind.html` (Lines 131-140) correctly implements a dynamic runtime injection of `dir="auto"` to form input and textarea elements at DOM load time.
- **Static Integrity:** An audit of all HTML files under `web/templates` and `web/templates/en` using negative lookahead regular expressions confirms that **100% of all static `<input>` and `<textarea>` elements already contain the `dir="auto"` attribute**.

---

## 4. Concrete Fix Strategy

We recommend applying the following fixes:

1. **Fix CSS Transitions in Templates:**
   - Update `transition: left 0.5s ease;` to `transition: inset-inline-start 0.5s ease;` in `forgot_password.html`, `login.html`, and `reset_password.html` (both Arabic and English templates).
   - Update `transition: right .3s ease;` to `transition: inset-inline-end 0.3s ease;` in `web/templates/en/_sidebar_head.html`.

2. **Refactor Hardcoded Styles in Python Code (`web/app_v2.py`):**
   - Replace physical properties with logical properties in all inline HTML templates as follows:
     - `padding-left` -> `padding-inline-start`
     - `margin-left` / `margin-right` -> `margin-inline-start` / `margin-inline-end` (or `margin-inline`)
     - `text-align: left` -> `text-align: start`
     - `text-align: right` -> `text-align: end`
     - `border-right` -> `border-inline-end`

3. **Improve Arabic Readability (Line Heights & Fonts):**
   - Update `web/templates/_sidebar_head.html` (Line 71) to set `line-height: 1.7;` (or `1.8;`).
   - Audit and modify component styles in the Arabic templates to ensure all body text, paragraphs, and list items have a line-height between `1.7` and `2.0`.
   - Isolate Arabic strings inside `_dashboard_shell.html` (Lines 27 and 90) so that they do not inherit `font-family: monospace;` but instead default to the clean `Cairo` font.
