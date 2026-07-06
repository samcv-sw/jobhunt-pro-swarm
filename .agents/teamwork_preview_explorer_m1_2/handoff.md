# Handoff Report: Page-by-Page Audit of Secondary Pages

## 1. Observation
Below are the direct observations from auditing the codebase and secondary page templates:

### Page-specific Issues

#### A. `/trust`
- **File**: `web/templates/trust.html` (Arabic)
  - **Line 62**: `.nav{ position:fixed;top:12px;inset-inline-start: 50%;transform:translateX(50%);z-index:1000;`
  - **Issue**: Redundant custom `.nav` style block overrides and conflicts with the layout defined in `_public_nav.html`. Using `transform: translateX(50%)` in RTL shifts the navbar incorrectly.
- **File**: `web/templates/en/trust.html` (English)
  - **Line 56**: `.nav{ position:fixed;top:12px;inset-inline-start: 0; inset-inline-end: 0; margin-inline: auto;transform:translateX(-50%);z-index:1000;`
  - **Issue**: Combines logical centering (`inset-inline-start: 0; inset-inline-end: 0; margin-inline: auto;`) with `transform: translateX(-50%)`, which shifts the navbar off-center by exactly half of its width.

#### B. `/blog`
- **File**: `web/templates/en/blog.html` (English)
  - **Line 11**: `<meta property="og:title" content="المدونة | JobHunt Pro"/>`
  - **Issue**: Meta property `og:title` contains Arabic text `"المدونة | JobHunt Pro"` in the English page template.
  - **Line 16**: `<main class="blog-index" style="padding-top:140px;">`
  - **Issue**: Uses physical CSS `padding-top:140px;` instead of logical `padding-block-start: 140px;` (which is correctly used in `blog.html` line 38).

#### C. `/compare`
- **Files**: `web/templates/compare.html` (Arabic) and `web/templates/en/compare.html` (English)
  - **Lines 63-66 (AR)** / **Lines 58-61 (EN)**: CSS hides FAQ answers by default (`.faq-item p { display: none; }`) and shows them when `.faq-item.open` is applied.
  - **Issue**: There is no JavaScript script block to add/remove the `open` class on clicking `.faq-item h4`. Thus, the FAQ accordion is completely non-functional on both pages.

#### D. `/services`
- **File**: `web/templates/services_new.html` (Arabic)
  - **Line 24**: `.sec-badge{font-size:10px;font-weight:700;background:rgba(59,130,246,.12);color:#60a5fa;padding:3px 10px;border-radius:20px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-bottom:24px}`
  - **Issue**: Copy-paste error. The grid layout styles for `.svc-grid` were appended inside the `.sec-badge` CSS block. Desktop `.svc-grid` selector is entirely missing from the stylesheet.
  - **Line 394**: `document.querySelectorالكل('.cat-tab').forEach(t => t.classList.remove('active'));`
  - **Issue**: Fatal JS syntax error. Combines English and Arabic characters `querySelectorالكل` instead of using the standard `querySelectorAll`. Clicking any category tab throws a JavaScript exception, breaking category filtering.

#### E. `/for-employers`
- **File**: `web/templates/for_employers.html` (Arabic)
  - **Line 344**: `<form id="jobForm" onsubmit="submitJob(event)">`
  - **Issue**: Form lacks `action` and `method` attributes.
  - **Line 568**: `fetch('/api/employer/منشور-job', { method:'POST', body:formData })`
  - **Issue**: Submits POST request to `/api/employer/منشور-job`. However, the backend router in `web/app_v2.py` (line 7175) only defines `@app.post("/api/employer/post-job")`. The endpoint `/api/employer/منشور-job` does not exist on the server, causing form submission to fail with a 404 error.
- **File**: `web/templates/en/for_employers.html` (English)
  - **Line 360**: `<form id="jobForm" onsubmit="submitJob(event)">`
  - **Issue**: Form lacks `action` and `method` attributes.

#### F. `/referral`
- **File**: `web/templates/en/referral.html` (English)
  - **Line 9**: `Your friend has gifted you a fast-pass to land your next job. Sign up today and get <strong>50 free credits</strong> to tailormade your resume...`
  - **Issue**: Grammar typo ("tailormade" instead of "tailor" or "tailor-make").

### Shared Layout Issues

- **File**: `web/templates/en/_public_footer.html`
  - **Lines 2, 3, 5, 7, 10, 24**: Uses physical CSS properties (`margin-top`, `max-width`, `margin-bottom`, `height`, `margin`) inside inline styling. (Note: The Arabic template `_public_footer.html` correctly uses logical properties).
- **File**: `web/templates/en/_public_nav.html`
  - **Line 39**: `right: -100%;` and **Line 44**: `right: 0;` (along with `width`/`height` in lines 5, 6, 7) use physical layout properties instead of logical ones (`inset-inline-end`, `inline-size`/`block-size`).

### Audit Log Observations
- **`necrotic_audit.json`**: Identified footer social links (`𝕏`, `📱`, `💻`, `▶️`) pointing to `#` as necrotic links.
- **`qa_report_round4.json`**: This automated audit marked all these files as "passing" because it only checked for the presence of `<title>`, `<h1>`, meta description, and `<style>` block violations. It completely missed functional bugs such as query selector typos, non-existent API routes, and broken JavaScript accordion handlers.

---

## 2. Logic Chain
1. **Automated QA Limitations**: The automated check in `qa_report_round4.py` marked secondary templates as "passing" (visible in `qa_report_round4.json`), but it only scanned basic tags and styles. A manual line-by-line inspection of the template files revealed deep structural and runtime errors.
2. **Broken Route in Arabic Employers Page**: In `for_employers.html`, form submission targets `/api/employer/منشور-job` via `fetch()`. Comparing this with `web/app_v2.py` line 7175 shows only `/api/employer/post-job` is registered. This mismatch guarantees that job postings fail in the Arabic view.
3. **Broken Script in Arabic Services Page**: In `services_new.html`, category selection uses `document.querySelectorالكل`. Because `querySelectorالكل` is undefined, clicking tabs triggers a syntax error in the browser console and stops the script execution.
4. **CSS Grid Bug on Services Page**: In `services_new.html` line 24, the grid styling rules are inside `.sec-badge` instead of `.svc-grid`. Without the desktop grid rule, cards are laid out vertically as block elements.
5. **Interactive FAQ Failure**: In both `compare.html` files, clicking headers is intended to toggle their visibility class. However, the absence of any click listeners in the code blocks the FAQ accordion from expanding.
6. **Logical Properties Violation**: In `en/_public_footer.html` and `en/_public_nav.html`, physical attributes like `margin-top` and `right` are used in inline styles, which violates the Gulf region RTL/Arabic typography and layout rules specified in `AGENTS.md`.

---

## 3. Caveats
- Direct visual testing in a browser was not performed since the explorer is in read-only mode and lacks web browsing capability. Observations are entirely derived from static analysis of the templates and comparison with views (`app_v2.py`).
- Assumptions are made that templates in `web/templates/` and `web/templates/en/` represent the current layout served on the live website.

---

## 4. Conclusion
While the secondary pages (/trust, /blog, /compare, /services, /for-employers, /referral) pass basic SEO tag validation, they contain critical layout and functional issues. These range from fatal JavaScript typos (`querySelectorالكل`) and wrong API endpoints (`/api/employer/منشور-job`) to non-functional FAQs, layout alignment errors, and physical CSS overrides.

### Actionable Fix Strategy Recommendations:
1. **`/trust`**: Remove the custom navigation styling (`.nav`) from `trust.html` and `en/trust.html` style blocks to avoid conflicts with the unified nav.
2. **`/blog`**: Translate the `og:title` in `en/blog.html` to English (`"Blog | JobHunt Pro"`) and replace `padding-top` with logical `padding-block-start`.
3. **`/compare`**: Append a lightweight click listener script to toggle the `.open` class on `.faq-item` elements when headers are clicked.
4. **`/services`**:
   - Extract `.svc-grid` styles from `.sec-badge` in `services_new.html` and set them in a dedicated `.svc-grid` class.
   - Replace `querySelectorالكل` with `querySelectorAll` on line 394 of `services_new.html`.
5. **`/for-employers`**:
   - Change `/api/employer/منشور-job` to `/api/employer/post-job` in `for_employers.html` line 568.
   - Add `method="POST" action="/api/employer/post-job"` fallback attributes to `<form id="jobForm">` tags.
6. **`/referral`**: Correct the typo "tailormade" to "tailor" in `en/referral.html`.
7. **English navigation/footer**: Rewrite inline styles in `en/_public_footer.html` and `en/_public_nav.html` using CSS Logical Properties.

---

## 5. Verification Method
1. **Run the Project Server**: Spin up the FastAPI server locally (`python web/app_v2.py` or equivalent setup).
2. **Manual Inspection**:
   - Navigate to `/services` (Arabic locale). Attempt to switch categories using the category tabs. Check for JavaScript console errors.
   - Navigate to `/for-employers` (Arabic locale). Fill out the job form and submit it. Verify if a `404` status code is returned on the `/api/employer/منشور-job` route.
   - Navigate to `/compare`. Attempt to click on FAQ items to see if they open/close.
   - Navigate to `/trust` (English locale). Verify the visual alignment and center of the navbar.
3. **HTML Code Inspection**: Look at the changes directly in the templates directory. Check that there are no physical property violations in `en/_public_footer.html` and `en/_public_nav.html`.
