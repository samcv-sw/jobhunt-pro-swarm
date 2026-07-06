# Backend Route, Performance, and SEO Audit Report

**Date**: July 6, 2026  
**Auditor Persona**: Teamwork Preview Explorer (Explorer 3)  
**Workspace**: `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi`

---

## Executive Summary
This report presents a comprehensive audit of the backend routes, template variables, log files, broken navigation links, and SEO/performance elements for the CV project. 

The audit identified several critical issues:
1. **Template Syntax Corruption**: `pricing_v2.html` and `pricing_v3.html` contain HTML parsing corruptions that cause Jinja2 compilation failures.
2. **FastAPI Route Collision**: Duplicate `@app.get("/referral")` endpoints prevent logged-in users from ever viewing their referrals dashboard, redirecting them to `/dashboard` instead.
3. **Missing Template Context Variables**: Key variables (`request` in public shell, `now` in admin panel) are referenced in templates but missing from backend contexts.
4. **Local vs. Remote Link Desync**: Local code has corrected 404 links (`/press`, `/partners`, `/gdpr`) but the remote live deployment is outdated.
5. **SEO Opportunities**: Pricing and FAQ pages lack page-specific structured data (JSON-LD).

---

## 1. Backend Route Variables & Jinja2 Template Mismatches

By statically parsing all templates and cross-referencing them with the keyword arguments passed to `render_template` in `web/app_v2.py`, we identified the following discrepancies:

### A. Template Compilation Errors (Critical)
* **Target Files**: `web/templates/pricing_v2.html` (Line 425) & `web/templates/pricing_v3.html` (Line 489)
* **Observations**:
  * In `pricing_v2.html`: 
    `class="pricing-card ... " ... discount="" if="" {%=""> 0 %}style="border-color:rgba(239,68,68,.3);"{% endif %}>`
  * In `pricing_v3.html`: 
    `class="pricing-card-v3 ... " ... discount="" if="" {%=""> 0 %}style="border-color:rgba(239,68,68,0.3);"{% endif %}>`
  * **Jinja Error**: `tag name expected` (compilation fails).
  * **Cause**: An automated HTML formatter/parser likely corrupted the Jinja control block `{% if discount > 0 %}` into attributes `discount="" if="" {%=""`.
  * **Proposed Fix**:
    * Change line 425 in `pricing_v2.html` to:
      `{% if discount > 0 %}style="border-color:rgba(239,68,68,.3);"{% endif %}`
    * Change line 489 in `pricing_v3.html` to:
      `{% if discount > 0 %}style="border-color:rgba(239,68,68,0.3);"{% endif %}`

### B. Missing Context Variables
* **Template**: `_public_shell.html` (Missing: `request`)
  * **Observation**: Used at line 13: `href="https://jhfguf.pythonanywhere.com{{ request.url.path if request else '' }}"`.
  * **Cause**: Inside `_public_shell` function (Line 189 in `web/app_v2.py`), the `request` variable is received as a function parameter but is never passed to `render_template`.
  * **Proposed Fix**: Pass `request=request` inside the `render_template` call of `_public_shell`.
* **Template**: `admin.html` (Missing: `now`)
  * **Observation**: Used at line 244: `{% if s.active and s.end_time and s.end_time > now %}`.
  * **Cause**: The `/admin` route in `web/app_v2.py` (Line 7669) fetches flash sales but does not pass the current time (`now`) to the template context.
  * **Proposed Fix**: Pass `now=datetime.now(timezone.utc)` (or local time matching database formats) in the `render_template` call of `admin.html`.

### C. Mismatched Templates & Contexts
* **Template**: `referral.html`
  * **Observation**: The logged-in referrals route at Line 5780 (`referral_page`) queries databases for `referrals_count`, `wallet_balance`, `referral_link`, and share links, passing all of them to `referral.html`. However, the template `referral.html` is merely a public invitation card ("You are invited...") and does not use or display any of these dashboard variables.
  * **Proposed Fix**: Ensure the stats referrals template is implemented or create a dedicated dashboard-level referrals template (e.g., `referrals_dashboard.html`).

### D. Wasted Queries / Unused Variables
* **Template**: `dashboard_v3.html`
  * **Observation**: The backend passes 16 unused variables (e.g., `profile_count`, `profiles`, `transactions`, `referrals`, `login_streak`, etc.) which are ignored by the template. This represents wasted SQL query overhead in the `/dashboard` route.

---

## 2. Server Log Audit (`_pa_server.log`)

A complete scan of the 95MB `_pa_server.log` revealed several backend exceptions and system warnings:

### A. Critical Failures
* **SQLite Fallback Database Access Errors**:
  * **Error log**: `sqlite3.OperationalError: disk I/O error` & `sqlite3.DatabaseError: file is not a database` on `PRAGMA journal_mode=WAL` call.
  * **Context**: Occurred on 2026-06-29 around `/pricing` and `/home` routes when trying to fallback to `/home/JHFGUF/jobhunt/jobhunt_saas_v2.db`. Indicates database file corruption or permission locking.
* **Missing Dependency Exception**:
  * **Error log**: `Failed to load Iron Cloak: No module named 'core.iron_cloak'`
  * **Context**: Raised repeatedly during startup/middleware execution. Indicates a broken import or missing repository file.

### B. Recurring Network/API Warnings
* **Telegram Notifications**:
  * **Warning**: `Telegram send failed: HTTP 429 — {"ok":false,"error_code":429,"description":"Too Many Requests..."}` due to bot throttling.
  * **Warning**: `ProxyError('Unable to connect to proxy', OSError('Tunnel connection failed: 503 Service Unavailable'))` indicating pythonanywhere proxy outages.
* **Gmail SMTP Mailer**:
  * **Warning**: `(535, b'5.7.8 Username and Password not accepted...')` indicating bad credentials for automated email accounts.
  * **Warning**: `[Errno 101] Network is unreachable` indicating firewall or outgoing network blocks.
* **Indeed RSS Scrapers**:
  * **Warning**: `Indeed RSS [...] error: Tunnel connection failed: 403 Forbidden` and `XML parse error` caused by Cloudflare blocks.

---

## 3. Link Checker & Routing Collision Audit

### A. 404 Links (From Crawler)
The existing `qa_report.json` generated by `qa_spider.py` crawled 29 public URLs and identified 3 broken links returning HTTP 404:
1. `/press`
2. `/partners`
3. `/gdpr`

* **Status**: A local code audit shows that the script `fix_links.py` has already run locally, removing these tags from `index_v4.html` and `_public_footer.html`. However, the live pythonanywhere server has not been updated with these fixes, explaining why the crawler (targeting the remote host) still encounters them.
* **Resolution**: Redeploy the local changes to the pythonanywhere host.

### B. FastAPI Route Collision (Major Bug)
* **Route 1**: Line 2599
  ```python
  @app.get("/referral", response_class=HTMLResponse)
  def referral_page(request: Request, ref: str = ""):
      # Redirects logged in users to /dashboard
  ```
* **Route 2**: Line 5779
  ```python
  @app.get("/referral", response_class=HTMLResponse)
  def referral_page(request: Request):
      # Renders referral stats for logged-in users
  ```
* **Consequence**: Since both handlers register GET `/referral`, FastAPI matching rules will resolve all requests to the first handler (Line 2599). Logged-in users clicking "Referrals" in the sidebar (which links to `/referral` in `_sidebar.html`) are redirected to `/dashboard` and can **never** view their stats dashboard.
* **Proposed Fix**: Rename the second route's path to `@app.get("/referrals")` (with an "s"), and update the link in `_sidebar.html` from `/referral` to `/referrals`.

---

## 4. Performance & Performance Audits (Images & Preloads)

### A. Image Lazy Loading
* **Observation**: Audited all templates. 100% of the `<img>` tags in both Arabic and English templates contain `loading="lazy"`. 

### B. Resource Preloads
* **Observation**: The system uses extensive preload hints to boost page loading speeds and prevent layouts shifting:
  * Critical stylesheets (`premium-ui.css`, `cyberpunk-rtl.css`) are preloaded:
    `<link rel="preload" href="/static/css/premium-ui.css" as="style">`
  * Critical web fonts (Google Fonts Cairo, Inter, Outfit, Space Grotesk) are preloaded:
    `<link href="https://fonts.googleapis.com/...display=swap" rel="preload" as="style" onload="this.rel='stylesheet'">`

---

## 5. SEO & Structured Data Audits

### A. HTML Lang & Dir Attributes
* **Base Dynamic Shell**: `_base_tailwind.html` implements standard dynamic tags:
  `lang="{{ lang | default('ar') }}"` and `dir="{{ 'rtl' if (lang | default('ar')) in ['ar', 'he', 'fa', 'ur'] else 'ltr' }}"`.
* **Public Shells/Templates**: Arabic templates have correct hardcoded attributes: `lang="ar" dir="rtl"`.
* **Issue**: English templates under `en/` (e.g., `en/_base_tailwind.html`, `en/_public_shell.html`) set `lang="en"`, but completely omit `dir="ltr"`. 
* **Proposed Fix**: Add `dir="ltr"` to all English templates' `<html>` tags for standards compliance.

### B. JSON-LD Structured Data
* **Landing Page**: Contains valid `SoftwareApplication` schema with price range aggregates and rating aggregates.
* **Organization Schema**: Mapped globally via `_public_shell.html`.
* **Issues**: 
  * **Pricing Page (`pricing_v3.html`)**: Omits specific Product/Offer schema.
  * **FAQ Page (`faq.html`)**: Omits specific FAQPage schema.
* **Proposed Fix**: 
  * Inject FAQPage schema (mapping questions/answers) in `faq.html`.
  * Inject Product schemas (mapping the tiers) in `pricing_v3.html`.

### C. Sitemap.xml & Robots.txt
* Both are served dynamically using FastAPI endpoints:
  * `/sitemap.xml`: Correctly structures public URLs. However, it lists `/referral` (which redirects logged-in users) but does not list public alternatives correctly.
  * `/robots.txt`: Correctly configures crawling parameters, disallows internal panels (`/admin`, `/dashboard`, `/wallet`, `/checkout`), defines a 5s crawl delay, and points to the sitemap location.
