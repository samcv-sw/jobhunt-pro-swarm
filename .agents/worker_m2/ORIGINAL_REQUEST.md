## 2026-07-06T09:25:50Z
Identity: You are teamwork_preview_worker.
Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m2

Task:
Implement the fixes and enhancements based on the findings from the Explorers' audits to fulfill requirements R1, R2, R3, R4, R5, and R6:

1. Fix Jinja2 syntax corruptions:
   - In `web/templates/pricing_v3.html` line 489: fix the malformed Jinja statement (e.g. `discount="" if="" {%="" > 0 %}`) to standard `{% if discount > 0 %}style="border-color:rgba(239,68,68,0.3);"{% endif %}`.
   - In `web/templates/pricing_v2.html` line 425: fix the malformed Jinja statement to `{% if discount > 0 %}style="border-color:rgba(239,68,68,.3);"{% endif %}`.

2. Resolve FastAPI route collision:
   - In `web/app_v2.py`, find the two routes handling `/referral`. Keep `/referral` for the public referral landing page (renders public referral template / handles referral tracking code).
   - Change the logged-in user referrals statistics page route to `/referrals`.
   - Update `web/templates/_sidebar.html` (and any other files referencing `/referral` for logged-in users) to point to `/referrals`.

3. Fix missing template context variables in `web/app_v2.py`:
   - Pass `request=request` to `render_template` in the `_public_shell` function.
   - Pass `now=datetime.now(timezone.utc)` (or local timezone equivalent) in the `/admin` route context when rendering `admin.html`.

4. Visual styling & UI Polish (RTL/Arabic and LTR/English):
   - Update form `<select>` and `<input>` elements that lack `dir="auto"`:
     - `web/templates/for_employers.html` (line 360): add `dir="auto"` to `<select id="category">`.
     - `web/templates/contact.html` (line 104): add `dir="auto"` to `<select id="subject">`.
     - `web/templates/dashboard_v3.html` (line 477): add `dir="auto"` to `<select id="smtpProvider">`.
     - `web/templates/en/for_employers.html` (line 372): add `dir="auto"` to `<select id="category">`.
     - `web/templates/en/contact.html` (line 109): add `dir="auto"` to `<select id="subject">`.
     - `web/templates/en/dashboard_v3.html` (lines 435, 442, 446): add `dir="auto"` to the SMTP provider select, email input, and password input.
   - Typography fixes:
     - Remove `tracking-wider` and `tracking-widest` classes on Arabic text blocks in `web/templates/dashboard_v3.html` and `web/templates/war_room.html`.
     - Standardize Arabic content to use Cairo/Tajawal fonts with a minimum size of 16px (upgrade any `text-xs` (12px) and `text-sm` (14px) elements containing Arabic text to `text-base` or equivalent).
     - Fix English typography font overrides: remove non-standard font declarations in `web/templates/en/index_v3.html` (JetBrains Mono) and `web/templates/en/resume_tailor.html` (Georgia, Times New Roman), ensuring base Inter/Outfit fonts are used.
   - Glassmorphism & premium feel:
     - Ensure all pages use dark gradient backgrounds. For pages lacking them, add appropriate background classes or inline styles.
     - Add premium glassmorphism card styling (using `backdrop-filter: blur(...)` or the `.glass` class) in `web/templates/en/for_employers.html` and `web/templates/en/resume_tailor.html`.
   - Hover animations & transitions:
     - Add `hover:scale-105 hover:shadow-lg transition-all` or corresponding CSS rules for all buttons and call-to-action anchors across both Arabic and English templates.
   - Refactor physical CSS properties to logical CSS properties:
     - Convert physical `left: 50%` alignments to logical alignments in `pricing_v3.html` (line 190), `for_employers.html` (line 47), `trust.html` (line 62), and English templates (`left`, `right`, `text-align: left/right`, `float: left/right` should be converted to logical equivalents).

5. Performance and SEO:
   - Ensure `dir="ltr"` and `lang="en"` are defined on the `<html>` element of all English pages in `web/templates/en/`.
   - Add structured JSON-LD schemas: `FAQPage` schema on `faq.html` and `Product` schema on `pricing_v3.html`.
   - Verify robots.txt and sitemap.xml.
   
6. Verification & Validation:
   - Run `python qa_audit_r4.py` to check for any CSS physical violations. Ensure there are 0 violations.
   - Run `python qa_spider.py` (or check files) to ensure there are no 404 links.
   - Test pages locally by running the server, checking for Jinja2 template loading issues, and scanning logs.
   - Run pytest to verify all 253 tests pass.
