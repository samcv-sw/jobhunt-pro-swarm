# Handoff Report — RTL and Localization Audit

## 1. Observation
We ran several recursive grep searches across the `web/templates/` and `web/templates/en/` HTML files and python files in `web/` using ripgrep. Below are direct observations:

- **CSS Transition Mismatch (Physical vs Logical):**
  - In `web/templates/forgot_password.html` (Line 176):
    ```css
    .btn-submit::before {
      content: '';
      position: absolute; top: 0; inset-inline-start: -100%; width: 200%; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
      transition: left 0.5s ease;
    }
    ```
    *(Repeated in `web/templates/en/forgot_password.html:171`, `web/templates/login.html:78`, `web/templates/en/login.html:76`, `web/templates/reset_password.html:190`, `web/templates/en/reset_password.html:183`)*
  - In `web/templates/en/_sidebar_head.html` (Line 1136):
    ```css
    .notif-panel{position:fixed;top:0;inset-inline-end:-380px;width:360px;max-width:90vw;height:100vh;background:#080812;border-inline-start:1px solid rgba(255,255,255,.08);z-index:250;transition:right .3s ease;display:flex;flex-direction:column;overflow:hidden;box-shadow:-8px 0 30px rgba(0,0,0,.5);}
    ```

- **Physical Styles in Python HTML Builders (`web/app_v2.py`):**
  - Line 2689: `.pricing-card ul li{{font-size:12px;color:#94a3b8;padding-left:20px;position:relative;line-height:1.4}}`
  - Line 2711: `.srv-price{{font-size:16px;font-weight:800;color:#60a5fa;flex-shrink:0;margin-left:16px}}`
  - Line 2952: `<ul style="line-height:2;padding-left:20px;">`
  - Line 2972 & 3019: `<a href="/" class="btn btn-outline" style="margin-left:12px;">Back to Home</a>`
  - Line 2995, 2996, 2997: `<th style="text-align:left;padding:8px;color:#64748b;">`
  - Line 3034, 3041, 3048: `<div class="card" style="text-align:left;margin-bottom:16px;">`
  - Line 4962: `<p style="... margin-left: auto; margin-right: auto;">`
  - Line 4963: `<div style="... text-align:left; ...">`
  - Line 6352, 6373, 6394, 6547: `<td style="text-align:right; ...">`
  - Line 6414, 6417, 6420, 6765: `<td style="... border-right:1px solid #e2e8f0">`
  - Line 6657, 6772: `<ul style="margin:0;padding-left:16px">`
  - Line 6664, 6782: `<ul style='padding-left:20px;margin:12px 0'>`
  - Line 7910: `label { display: block; text-align: left; ... }`
  - Line 8148: `th{{text-align:left; ...}}`

- **Secondary Script Files:**
  - `web/_build_index.py` (Line 88): `.featured-grid{...margin-left:auto;margin-right:auto;}`
  - `web/_build_templates.py` (Line 69): `.jc-time{...text-align:right;...}`

- **Arabic Typography & Line Height:**
  - `web/templates/_sidebar_head.html` (Line 71):
    ```css
    html, body {
      font-family: 'Cairo', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      ...
      line-height: 1.65;
    }
    ```
  - `web/templates/_dashboard_shell.html` (Lines 27 and 90):
    ```html
    <p style="font-size:11px;color:#f0c040;font-family:monospace;margin-block-start:2px;">${{ "%.2f"|format(user.wallet_balance|default(0)) }} رصيد</p>
    <p style="font-size:11px;color:#00d4aa;font-family:monospace;margin:0;">حالة النظام: <span style="font-weight:700;">ممتاز ●</span></p>
    ```

- **`dir="auto"` Presence:**
  - We ran a negative lookahead regex search `IsRegex: true` with `<input(?![^>]*dir=["']auto["'])[^>]*>` and `<textarea(?![^>]*dir=["']auto["'])[^>]*>` in `web/templates/`. Result: `No results found`.

---

## 2. Logic Chain
- **Step 1:** The `btn-submit::before` selector specifies `inset-inline-start` for start positioning but uses `transition: left`. Since the `left` property is not actively set, the transition will not operate correctly under standard browser interpretation.
- **Step 2:** The `notif-panel` selector in `en/_sidebar_head.html` sets logical end-positioning `inset-inline-end: -380px` but specifies `transition: right`. This creates a layout bug because direction-aware properties should transition via their logical counterparts.
- **Step 3:** The inline HTML strings in `web/app_v2.py` generate complete HTML pages (such as the refund policy, cookies page, careers page, and client email dashboards) with hardcoded CSS styling. Using physical properties like `padding-left`, `margin-left`, `text-align: left/right`, and `border-right` inside these strings directly overrides any dynamic LTR/RTL stylesheet adaptations, creating display bugs for Arabic users.
- **Step 4:** Gulf region typography standards require a line-height between `1.7` and `2.0` for Arabic text (e.g. `Cairo` or `Tajawal` font) to guarantee readability. The default template body sets `line-height: 1.65;` in `_sidebar_head.html`, which fails this threshold. Multiple elements also fallback or explicitly declare `1.5` or `1.6`.
- **Step 5:** The dynamic `dir="auto"` DOM script in `_base_tailwind.html` serves as a fallback. Since 100% of static input and textarea tags explicitly define `dir="auto"`, the forms are fully compliant at render time.

---

## 3. Caveats
- No active test suite runs CSS or layout checks automatically. Layout verification was performed visually and through code inspection.
- The templates are split between generic (Arabic) and English-specific folders (`en/`). Changes to logical properties will benefit both layouts, but care should be taken that any overrides do not affect explicit alignment rules intended for English-only layouts.

---

## 4. Conclusion
The codebase is mostly logical property-compliant but contains critical legacy styling errors:
1. Mismatched property transitions on `.btn-submit` and `.notif-panel`.
2. Hardcoded physical styling in `web/app_v2.py` inline HTML string templates.
3. Insufficient line heights (under `1.7`) for Arabic pages and dashboards.
4. Monospace styling wrapping Arabic characters in `_dashboard_shell.html`.

The compliance of `<input>` and `<textarea>` elements with `dir="auto"` is perfect.

---

## 5. Verification Method
- **Inspection Files:** Inspect `web/templates/forgot_password.html:176`, `web/templates/en/_sidebar_head.html:1136`, and `web/app_v2.py:2952`.
- **Testing Layout:** Once fixed, run the web application, inspect the login/reset buttons, toggle the notifications panel in English/Arabic modes, and ensure the CSS slide/glow animations execute without shifts.
