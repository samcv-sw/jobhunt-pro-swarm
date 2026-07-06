# M1 Preview Audit Handoff Report

## 1. Observation
Below are the exact observations, file paths, line numbers, and verbatim issues found during the page-by-page audit:

### A. Critical Server-Side Routing Bugs
*   **GET `/login` and POST `/login`**: In `web/app_v2.py` and all modules in `web/routers/` (such as `auth.py`, `public.py`, etc.), there is no `@app.get("/login")` or `@router.get("/login")` route defined. There is also no `@app.post("/login")` or `@router.post("/login")` route defined.
    *   The older `web/app.py` defined these routes at lines 394 and 398:
        ```python
        394: @app.get("/login", response_class=HTMLResponse)
        395: async def login_page(request: Request):
        396:     return templates.TemplateResponse(request=request, name="login.html", context={"request": request})
        397: 
        398: @app.post("/login")
        399: async def login(request: Request, email: str = Form(...), password: str = Form(...)):
        ```
    *   In `web/append_routes_v3.py` (which is appended to `app_v2.py` on the PythonAnywhere server), only `/login/v2` is defined at line 138:
        ```python
        138: @app.get("/login/v2", response_class=HTMLResponse)
        ```
    *   Crucially, the login templates `login_v2.html` (line 150) and `en/login_v2.html` (line 120) contain a form that POSTs to `/login`:
        ```html
        <form action="/login" id="loginForm" method="POST" onsubmit="handleLogin(event)">
        ```
    *   *Result*: Submitting the login form or visiting `/login` GET will fail with a **404 Not Found** because there is no route handler on the server.
*   **GET `/new-campaign`**: The route `/new-campaign` is referenced multiple times in the templates:
    *   `web/templates/dashboard_v3.html` line 175: `<a href="/new-campaign">`
    *   `web/templates/dashboard_v3.html` line 274: `<a href="/new-campaign">`
    *   `web/templates/pricing_v3.html` line 538: `<a class="btn {{ tier.button_class }}" href="{{ '/new-campaign' if is_logged_in else '/register' }}">`
    *   `web/templates/en/pricing_v3.html` line 543: `<a href="{{ '/new-campaign' if is_logged_in else '/register' }}" class="btn {{ tier.button_class }}">`
    *   No GET route for `/new-campaign` is defined in `web/app_v2.py` or any files in `web/routers/`. In the old `web/app.py`, it was defined at line 479:
        ```python
        479: @app.get("/new-campaign", response_class=HTMLResponse)
        ```
    *   *Result*: Clicking these CTA buttons or navigating to `/new-campaign` as a logged-in user results in a **404 Not Found**.

### B. Template Inclusion Bugs (Arabic Nav and Footer Loaded on English Site)
*   In the English templates folder `web/templates/en/`:
    *   `en/index_v4.html` line 115: `{% include '_public_nav.html' %}`
    *   `en/index_v4.html` line 1221: `{% include '_public_footer.html' %}`
    *   `en/faq.html` line 72: `{% include '_public_nav.html' %}`
    *   `en/faq.html` line 110: `{% include '_public_footer.html' %}`
    *   `en/login_v2.html` line 82: `{% include '_public_nav.html' %}`
    *   `en/login_v2.html` line 227: `{% include '_public_footer.html' %}`
    *   `en/register_v2.html` line 123: `{% include '_public_nav.html' %}`
    *   `en/register_v2.html` line 429: `{% include '_public_footer.html' %}`
    *   `en/pricing_v3.html` line 72: `{% include '_public_nav.html' %}`
    *   `en/_public_shell.html` line 143: `{% include "_public_nav.html" %}`
    *   `en/_public_shell.html` line 147: `{% include "_public_footer.html" %}`
*   *Result*: These includes load files named `_public_nav.html` and `_public_footer.html` without specifying the subfolder. Because the Jinja2 loader root is `web/templates/`, it matches the root (Arabic) versions `_public_nav.html` and `_public_footer.html` instead of the English versions `en/_public_nav.html` and `en/_public_footer.html` that exist in `web/templates/en/`. This causes the English site to display the Arabic navigation bar and Arabic footer.

### C. Localized Metadata Bugs (Arabic Content in English Meta Tags)
*   In `web/templates/en/register_v2.html` line 114:
    ```html
    <meta property="og:title" content="إنشاء حساب | JobHunt Pro"/>
    ```
*   In `web/templates/en/login_v2.html` line 73:
    ```html
    <meta property="og:title" content="تسجيل الدخول | JobHunt Pro"/>
    ```
*   *Result*: Hardcodes Arabic content on the English page meta tags, leading to incorrect social media previews.

### D. Security and Visibility Bug on Contact Page
*   In `web/templates/contact.html` (Arabic contact page) line 131:
    ```html
    <!-- System Logs Card -->
    <a class="support-card" href="/admin/sys-logs" style="border-color:rgba(255,100,100,0.3);background:rgba(255,100,100,0.05)">
    <div class="icon">??</div>
    <h3>{{ _('System Logs') }}</h3>
    <p>{{ _('View server and error logs to quickly diagnose website issues. Admin only.') }}</p>
    </a>
    ```
*   *Result*: This card is not guarded by `{% if is_admin %}` like the other admin logs button at line 167, and is visible to the public. It also has a broken `??` icon placeholder.

### E. CSS Validation Conflict on FAQ Page
*   In `web/templates/faq.html` line 22:
    ```css
    h1{font-size:32px;font-weight:800;margin-bottom:6px;font-size:14px;margin-bottom:40px}
    ```
*   *Result*: Duplicate and conflicting definitions for `font-size` (`32px` vs `14px`) and `margin-bottom` (`6px` vs `40px`). The browser will overwrite the first with the second, making the h1 font size very small (14px) and increasing the bottom margin.

### F. Formatting, Typo and Encoding Quirks
*   In `web/templates/pricing_v3.html` and `web/templates/en/pricing_v3.html`, multiple raw UTF-8 emoji and typographic characters are corrupted into characters like `â€”`, `âš¡`, `ðŸ”`, and `â˜…`. E.g.:
    *   `<!-- Pricing v3 â€” ... -->`
    *   `fs-icon` has `âš¡` (should be `⚡`)
    *   `stars` has `â˜…â˜…â˜…â˜…â˜…` (should be `★★★★★`)
    *   Close button has `âœ•` (should be `✖` or `×`)
    *   Fire emoji timer text has `ðŸ”🔥`
*   In `web/templates/index_v4.html`:
    *   Line 568 has `{{ _('... 9 ETH ...') }}` where `9 ETH` is a typo for `Ξ ETH` or `♦ ETH`.
    *   Logo list uses a soap emoji `🧼` for LinkedIn.
    *   Mix of English/Arabic strings inside translation tags, e.g., line 283 `{{ _('Everything You Need to احصل على وظيفة أحلامك') }}`.
*   In `web/templates/_public_nav.html` line 10:
    *   The language switcher is hardcoded to English (`/lang/en` and `{{ _('English') }}`). When the active language is English, this link will still point to `/lang/en` and say "English", making it impossible for the user to switch back to Arabic from the English pages.

---

## 2. Logic Chain
1. **Observation 1** shows that the `GET /login`, `POST /login`, and `GET /new-campaign` routes are not defined in `web/app_v2.py` or its routers, although they are referenced in the front-end login form and pricing/dashboard templates. Therefore, trying to log in or click pricing CTAs as a logged-in user will result in a 404 error.
2. **Observation 2** shows that the English page templates include root `_public_nav.html` and `_public_footer.html` instead of their English counterparts in `en/`. Therefore, Jinja2 falls back to the root Arabic versions, rendering the navigation bar and footer in Arabic on the English site.
3. **Observation 3** shows that the English templates hardcode Arabic text for `og:title` metadata tags, causing SEO title mismatches in social media previews.
4. **Observation 4** shows that the "System Logs" card is not wrapped in `{% if is_admin %}` in the Arabic template, making it visible to guest users, leading to dead links (403 errors) and a broken layout with `??` placeholders.
5. **Observation 5** shows that `h1` in `faq.html` contains duplicate conflicting properties, causing the header text to be rendered incorrectly at 14px size instead of 32px.
6. **Observation 6** shows that UTF-8 files were loaded or saved with mismatched encodings, leading to corrupted text and broken symbols in pricing and FAQ pages.
7. **Observation 7** shows that `_public_nav.html` hardcodes the English language switcher link, meaning that once the language is set to English, there is no way to switch back to Arabic from the navigation menu.

---

## 3. Caveats
*   We did not perform a live network scan of all endpoints due to CODE_ONLY constraints.
*   We assumed that PythonAnywhere executes `web/app_v2.py` as configured in `pythonanywhere_wsgi.py`. If it executes `web/app.py` instead, the missing routes might exist but then other `app_v2.py` optimizations would not run.
*   We assumed that `append_routes_v3.py` is appended to `app_v2.py` as described in its comments.

---

## 4. Conclusion
The preview site suffers from critical routing omissions (missing web login GET/POST and campaign creation GET), translation includes mismatches (rendering Arabic nav/footer on English pages), and localized metadata and validation flaws.

### Fix Strategy Recommendations:
1.  **Add Web Login Routes**: Implement GET `/login` and POST `/login` route handlers in `web/app_v2.py` (matching the logic in old `web/app.py` but using the new `login_v2.html` template).
2.  **Add Campaign Creation Route**: Implement GET `/new-campaign` in `web/app_v2.py` or `web/routers/jobs.py` to render `new_campaign_v2.html` for authenticated users.
3.  **Dynamic Includes**: Update the includes in all English page templates to dynamically resolve or load the English versions:
    ```html
    {% include 'en/_public_nav.html' if lang == 'en' else '_public_nav.html' %}
    {% include 'en/_public_footer.html' if lang == 'en' else '_public_footer.html' %}
    ```
4.  **Fix Metadata**: Correct the `og:title` content in `en/register_v2.html` and `en/login_v2.html`.
5.  **Guard Admin-Only Card**: Wrap the "System Logs" card in `contact.html` with `{% if is_admin %}`.
6.  **Resolve CSS Conflict**: Correct duplicate CSS properties for `h1` in `faq.html`.
7.  **Encoding Fix**: Re-save pricing and FAQ templates with UTF-8 encoding to fix corrupted characters.
8.  **Dynamic Language Switcher**: Update the language switcher in `_public_nav.html` to be dynamic:
    ```html
    {% if lang == 'en' %}
    <a href="/lang/ar" class="lang-switcher">🌐 العربية</a>
    {% else %}
    <a href="/lang/en" class="lang-switcher">🌐 English</a>
    {% endif %}
    ```

---

## 5. Verification Method
1.  **Server Start**: Run the local development server using `python web/app_v2.py` or `uvicorn web.app_v2:app --reload`.
2.  **Verify Web Login**: Navigate to `/login` GET, verify it serves `login_v2.html` correctly. Submit the login form with valid credentials and verify it redirects to `/dashboard` without raising a 404 on POST `/login`.
3.  **Verify Campaign Route**: Log in, navigate to `/pricing` and click the CTA to verify that `/new-campaign` serves `new_campaign_v2.html` correctly.
4.  **Verify English Page Nav/Footer**: Set language cookie `lang=en` and visit `/faq` or `/contact`. Verify that navigation links and footer are rendered in English.
5.  **Audit Meta Tags**: Inspect page sources to ensure the `og:title` displays in the correct language.
