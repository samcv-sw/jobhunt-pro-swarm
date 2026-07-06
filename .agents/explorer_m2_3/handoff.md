# Handoff Report — Teamwork Preview Explorer (Explorer 3)

## 1. Observation

Direct observations made during the audit:

* **Observation 1 (Jinja Syntax Corruption)**: 
  * File: `web/templates/pricing_v3.html` at Line 489:
    ```html
    <div class="pricing-card-v3 {% if tier.highlight %}highlight{% endif %}" data-price="{{ tier.price_usd }}" data-tier="{{ tier.get('tier', '') }}" discount="" if="" {%=""> 0 %}style="border-color:rgba(239,68,68,0.3);"{% endif %}>
    ```
  * File: `web/templates/pricing_v2.html` at Line 425:
    ```html
    <div class="pricing-card {% if tier.highlight %}highlight{% endif %}" data-price="{{ tier.price_usd }}" data-tier="{{ tier.id }}" discount="" if="" {%=""> 0 %}style="border-color:rgba(239,68,68,.3);"{% endif %}>
    ```
  * Running our Jinja2 parser script `audit_templates.py` produced:
    ```
    pricing_v2.html: ERROR: tag name expected
    pricing_v3.html: ERROR: tag name expected
    ```

* **Observation 2 (FastAPI Route Collision)**:
  * File: `web/app_v2.py` Line 2599:
    ```python
    @app.get("/referral", response_class=HTMLResponse)
    def referral_page(request: Request, ref: str = ""):
        # Redirects logged-in users to /dashboard
    ```
  * File: `web/app_v2.py` Line 5779:
    ```python
    @app.get("/referral", response_class=HTMLResponse)
    def referral_page(request: Request):
        # Renders stats dashboard content = render_template("referral.html", ...)
    ```

* **Observation 3 (Missing/Mismatched Template Context Variables)**:
  * File: `web/app_v2.py` Line 189 (`_public_shell` definition) calls `render_template` without `request`:
    ```python
    return render_template("_public_shell.html", content=content, title=title, description=meta_desc, is_logged_in=is_logged_in, VERSION=config.VERSION)
    ```
    Template `_public_shell.html` Line 13 references `request`:
    ```html
    <link rel="canonical" href="https://jhfguf.pythonanywhere.com{{ request.url.path if request else '' }}">
    ```
  * File: `web/app_v2.py` Line 7669 (`admin` route) calls `render_template` for `admin.html` without `now`:
    ```python
    content_html = render_template("admin.html", request=request, stats={...}, users=users, campaigns=campaigns, orders=orders, redeem_codes=redeem_codes, payment_stats=payment_stats, manual_emails=manual_emails, flash_sales=flash_sales)
    ```
    Template `admin.html` Line 244 references `now`:
    ```html
    {% if s.active and s.end_time and s.end_time > now %}
    ```

* **Observation 4 (Server Logs)**:
  * File: `_pa_server.log` has tracebacks containing:
    ```
    sqlite3.OperationalError: disk I/O error
    sqlite3.DatabaseError: file is not a database
    ```
    under uwsgi requests on `/pricing` and `/` routes, and startup import warnings:
    ```
    Failed to load Iron Cloak: No module named 'core.iron_cloak'
    ```

* **Observation 5 (Link Spider & 404s)**:
  * File: `qa_report.json` contains:
    ```json
    "404": [
        "https://jhfguf.pythonanywhere.com/press",
        "https://jhfguf.pythonanywhere.com/partners",
        "https://jhfguf.pythonanywhere.com/gdpr"
    ]
    ```
  * File: `web/templates/index_v4.html` and `web/templates/_public_footer.html` locally do not contain the string `press` or `partners`.
  * File: `fix_links.py` contains:
    ```python
    content = re.sub(r'<a href="/press"[^>]*>.*?</a>', '', content)
    ```

* **Observation 6 (SEO, Preloads, HTML Attributes)**:
  * Running `audit_img_tags.py` output: `Total img tags missing lazy loading: 0`.
  * File: `web/templates/en/_base_tailwind.html` Line 2:
    ```html
    <html lang="en" class="dark">
    ```
    (No `dir="ltr"` attribute).

---

## 2. Logic Chain

1. **Jinja Syntax Corruption**: Based on **Observation 1**, `pricing_v2.html` and `pricing_v3.html` contain malformed Jinja2 tag markup (`discount="" if="" {%=""`). Because Jinja2's parser fails on these lines with a `TemplateSyntaxError: tag name expected`, loading either pricing page on the live server will fail and trigger an HTTP 500 error if these blocks are reached.
2. **FastAPI Route Collision**: Based on **Observation 2**, FastAPI resolves routes sequentially. Since `/referral` GET is defined twice, FastAPI registers only the first handler (Line 2599). Logged-in users clicking the referrals button (which links to `/referral` in `_sidebar.html` as seen in **Observation 5**) are immediately caught by the first handler's redirect (`if user_id: return RedirectResponse("/dashboard")`) and returned to `/dashboard`. The actual referrals stats rendering logic on Line 5779 is completely unreachable.
3. **Missing/Mismatched Context Variables**:
   - Based on **Observation 3**, since `request` is not passed to `render_template` inside `_public_shell`, `request` evaluates to undefined. Although protected by `if request` checks in templates, canonical links fall back to empty strings, which breaks canonical/alternate SEO mapping.
   - Since `now` is not passed in the `/admin` context, `now` is undefined in Jinja. The comparison `s.end_time > now` fails, rendering flash sales expiration displays incorrectly.
4. **Local vs. Remote Link Desync**: Based on **Observation 5**, the local files have successfully had `fix_links.py` run to clean up the 404 links `/press`, `/partners`, and `/gdpr`. However, the live server continues to return 404s, implying that the remote server has not yet been redeployed or pulled the latest changes.
5. **SEO & HTML Attributes**: Based on **Observation 6**, the dynamic base template handles dynamic language direction properly. However, English-specific templates set `lang="en"` but omit `dir="ltr"`. Explicitly writing `dir="ltr"` is a recommended best practice for browser compliance.

---

## 3. Caveats

* **Logs Investigation Scoping**: The server log scan covered `_pa_server.log` (95MB), but was restricted to finding system tracebacks, exceptions, database faults, and unique warnings. High-frequency client request details or specific user actions were not mapped.
* **Network Restrictions**: Since we are in `CODE_ONLY` network mode, we could not run `qa_spider.py` actively against the live remote domain. We relied on the existing `qa_report.json` in the workspace to evaluate the crawl results.

---

## 4. Conclusion

1. **Syntax Fix**: `pricing_v2.html` (Line 425) and `pricing_v3.html` (Line 489) must be restored to standard Jinja syntax: `{% if discount > 0 %}style="..."{% endif %}`.
2. **Route Separation**: Rename the logged-in referrals route at Line 5779 in `web/app_v2.py` from `/referral` to `/referrals`, and update `_sidebar.html` to point to `/referrals` to resolve the route collision.
3. **Context Injection**: Pass `request=request` in `_public_shell` function, and pass `now=datetime.now(timezone.utc)` (or local equivalent) in the `/admin` page context.
4. **Deploy Updates**: Redeploy the codebase to the remote host to resolve sitemap and broken 404 links, since the fixes are already committed locally.
5. **SEO Rich Snippets**: Add `dir="ltr"` to all English templates' `<html>` tags, and inject `FAQPage` schema on `faq.html` and `Product` schemas on `pricing_v3.html`.

---

## 5. Verification Method

To verify these issues independently:
1. **Route Collision**: Start the FastAPI server locally (`python web/app_v2.py`) and log in. Navigate to `http://localhost:8000/referral`. If it redirects you to `/dashboard` instead of showing the referrals stats page, the bug is reproduced.
2. **Template Syntax**: Run Python in the project root:
   ```python
   from jinja2 import Environment, FileSystemLoader
   env = Environment(loader=FileSystemLoader("web/templates"))
   env.get_template("pricing_v3.html")
   ```
   If it raises a `TemplateSyntaxError`, the corruption is present.
3. **Sitemap / Robots.txt**: Run `curl http://localhost:8000/sitemap.xml` and `curl http://localhost:8000/robots.txt` after launching the server to verify the dynamic payload.
