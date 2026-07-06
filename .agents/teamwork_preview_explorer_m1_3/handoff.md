# Handoff Report — Page-by-Page Website Audit (/privacy, /terms, /en/, /en/pricing, /en/login, /en/register)

This report details the findings and fix strategies for the page-by-page audit of the target paths and templates.

---

## 1. Observation

### 1.1 Programmatic Routing Audit
Using Python introspection on the running FastAPI instance of `web/app_v2.py` (which is imported in the WSGI entrypoint of the live site), we extracted all registered routes and compared them to the requested paths.

*   **Missing `/login` GET & POST routes**: 
    The routes table contains `/api/v1/login` (POST JSON API) and `/login/v2` (GET) but does **NOT** contain `/login` (GET) or `/login` (POST) routes.
    *   `web/templates/en/login.html` (line 146) has `<form method="POST" action="/login">`.
    *   `web/templates/en/login_v2.html` (line 120) has `<form method="POST" action="/login" id="loginForm" onsubmit="handleLogin(event)">`.
    *   `web/templates/en/_public_nav.html` (line 25) has `<a href="/login" ...>Login</a>`.
    *   `web/templates/en/privacy.html` (line 50) and `web/templates/en/terms.html` (line 50) have `<a href="/login">Login</a>`.
    *   `web/templates/en/register_v2.html` (line 242) has `Already have an account? <a href="/login">Login</a>`.
    *   All of the above links and forms redirect or post to `/login`, which returns a **404 Not Found**.

*   **Missing `/new-campaign` GET route**:
    *   In `web/templates/en/pricing_v3.html` (line 543): `<a href="{{ '/new-campaign' if is_logged_in else '/register' }}" class="btn {{ tier.button_class }}">`.
    *   FastAPI routes dump confirms `/new-campaign` does **NOT** exist in `web/app_v2.py`. Clicking this as a logged-in user results in a **404 Not Found**.

*   **Missing Explicit Prefix Routes (e.g. `/en/pricing`, `/en/login`, `/en/register`, `/en/`)**:
    *   FastAPI routes list contains `/pricing`, `/register`, `/privacy`, `/terms`, `/` but has **no** paths prefixing with `/en/`.
    *   Visiting `/en/pricing`, `/en/login`, `/en/register`, or `/en/` directly results in a **404 Not Found** (handled by `custom_404_handler` in `web/app_v2.py:5288`).
    *   `LanguageMiddleware` (`core/localization.py:28`) checks query params (`?lang=en`) or cookies (`lang=en`) but does not handle or rewrite URL path prefixes (e.g., stripping `/en` or `/ar` from request paths).

### 1.2 UI and Script Validation
*   **HTML Entity Bug in `.textContent` Assignments (`web/templates/en/index_v4.html`)**:
    *   Line 990: `btn.querySelector('.faq-icon').textContent = expanded ? '&#x271a;' : '&#x2212;';`
    *   Line 1033: `scoreMsg.textContent = '&#x1f389; Great score! ...';`
    *   Line 1036: `scoreMsg.textContent = '&#x1f4aa; Good score! ...';`
    *   Line 1039: `scoreMsg.textContent = '&#x1f4ad; Your resume needs optimization. ...';`
    *   Since `.textContent` treats content as raw text, HTML entities (e.g. `&#x1f389;` for 🎉) are displayed literally as text rather than rendering as the intended symbol or emoji in the browser.

*   **Non-functional Social Navigation Links (verified via `necrotic_audit.json` and templates)**:
    *   Footer social links in `web/templates/en/index_v4.html` point to `#` placeholders:
        *   Line 838: `<a href="#" aria-label="Twitter">&#x1d54f;</a>`
        *   Line 839: `<a href="#" aria-label="LinkedIn">&#x1f4f1;</a>`
        *   Line 840: `<a href="#" aria-label="GitHub">&#x1f4bb;</a>`
        *   Line 841: `<a href="#" aria-label="YouTube">&#x25b6;&#xfe0f;</a>`

---

## 2. Logic Chain

1. **Missing GET/POST `/login` routes**:
   * *Observation*: Programmatic routes list contains `/api/v1/login` (POST) and `/login/v2` (GET) but lacks `/login` (GET or POST).
   * *Observation*: Templates (`login.html`, `login_v2.html`, `_public_nav.html`, `privacy.html`, `terms.html`, `register_v2.html`) reference `/login` for links or form actions.
   * *Inference*: Any user trying to navigate to `/login` or submit the login form will get a 404 error page.

2. **Missing GET `/new-campaign` route**:
   * *Observation*: Programmatic routes list lacks `/new-campaign`.
   * *Observation*: `pricing_v3.html` button points to `/new-campaign` for logged-in users.
   * *Inference*: Logged-in users selecting a plan are directed to a 404 page, blocking the checkout/campaign flow.

3. **Prefix Route 404s**:
   * *Observation*: Programmatic routes list does not have `/en/` prefixed routes.
   * *Observation*: `LanguageMiddleware` reads `lang` cookie/query parameters but does not rewrite URL paths in-flight.
   * *Inference*: Accessing `/en/pricing` or `/en/` directly routes to the custom 404 handler.

4. **Raw HTML entities in JS textContent**:
   * *Observation*: JavaScript uses `.textContent` to assign strings containing HTML decimal entities (`&#x1f389;`).
   * *Inference*: Emojis and icons are rendered as literal text strings instead of visual elements.

---

## 3. Caveats

*   **No Access to PythonAnywhere Web Tab Configuration**: We assumed the live site uses `web/app_v2.py` as indicated in the live WSGI config retrieved via `read_wsgi.py`.
*   **Static vs. Dynamic Audit**: The audit is based on local templates, WSGI configs, and programmatic FastAPI introspection. Some routes might be bypassed or redirected at the edge (e.g. Cloudflare Worker or Caddy) if there are routing rules not present in the workspace files, though no prefix rewrites were found in Caddyfile or Pages `_worker.js`.

---

## 4. Conclusion & Fix Strategies

### 4.1 Fix GET/POST `/login` and `/new-campaign` Routes
Map GET `/login` to render `login.html` and define POST `/login` to handle browser form authentication. Also redirect GET `/new-campaign` to the correct page or define it.

**Proposed additions to `web/app_v2.py` or `web/routers/auth.py`**:
```python
# In web/routers/auth.py:
@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, plan: str = ""):
    _, _, templates, config, _ = _deps()
    return templates.TemplateResponse(request, "login.html", {
        "plan": plan,
        "VERSION": config.VERSION
    })

@router.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    # Re-use or adapt the verification login logic similar to api_login but set cookie and redirect
    get_db, session_serializer, templates, config, _ = _deps()
    conn = get_db()
    user = conn.execute("SELECT user_id, password_hash FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    
    if not user or not _verify_pw(password, user["password_hash"]):
        return templates.TemplateResponse(request, "login.html", {"error": "Invalid email or password"})
        
    signed_uid = session_serializer.dumps(user["user_id"])
    resp = RedirectResponse("/dashboard", status_code=303)
    resp.set_cookie("user_id", signed_uid, max_age=86400 * 30, httponly=True, samesite="lax", secure=True)
    return resp
```

**Proposed addition to `web/app_v2.py` for `/new-campaign`**:
```python
@app.get("/new-campaign", response_class=HTMLResponse)
def new_campaign_page(request: Request):
    user_id = get_verified_user_id(request)
    if not user_id:
        return RedirectResponse("/login", status_code=303)
    # Redirect to campaign setup or render the new campaign template
    return RedirectResponse("/user-dashboard", status_code=302)
```

### 4.2 Fix English Prefix Routes (`/en/`, `/en/pricing`, etc.)
Add prefix stripping middleware to FastAPI inside `web/app_v2.py` to transparently map `/en/` and `/ar/` prefixed routes to their standard equivalents while setting `request.state.locale` to `'en'` or `'ar'`.

**Proposed middleware to insert in `web/app_v2.py`**:
```python
@app.middleware("http")
async def language_prefix_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/en/") or path == "/en":
        request.state.locale = "en"
        # Rewrite path internally for routing
        new_path = path[3:] if path.startswith("/en/") else "/"
        request.scope["path"] = new_path
    elif path.startswith("/ar/") or path == "/ar":
        request.state.locale = "ar"
        new_path = path[3:] if path.startswith("/ar/") else "/"
        request.scope["path"] = new_path
        
    response = await call_next(request)
    return response
```

### 4.3 Fix JS Emojis/HTML Entity rendering (`en/index_v4.html`)
Change `.textContent` assignments to use actual Unicode characters or `.innerHTML` instead of raw HTML decimal entities.
*   **Before**: `btn.querySelector('.faq-icon').textContent = expanded ? '&#x271a;' : '&#x2212;';`
*   **After**: `btn.querySelector('.faq-icon').innerHTML = expanded ? '&#x271a;' : '&#x2212;';` (or use `'✚'` and `'−'`)
*   **Before**: `scoreMsg.textContent = '&#x1f389; Great score! ...';`
*   **After**: `scoreMsg.textContent = '🎉 Great score! ...';` (or use `.innerHTML`)

---

## 5. Verification Method

1.  **Status Code and Path Verification**:
    Run a python script that instantiates the FastAPI client (via `fastapi.testclient.TestClient`) and requests:
    *   `GET /login` -> Assert status code is `200`.
    *   `POST /login` -> Assert status code is `200` or `303` Redirect.
    *   `GET /en/pricing` -> Assert status code is `200` and `dir="ltr"` is set on the HTML tag.
    *   `GET /new-campaign` -> Assert status code is `302` or `303` Redirect (if unauthorized).
2.  **Lint / Pytest verification**:
    After applying the middleware and router updates, run:
    `pytest`
