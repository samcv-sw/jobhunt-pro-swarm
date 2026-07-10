# Worker RTL Progress
Last visited: 2026-07-10T19:00:20Z

- [x] Jinja2 Templates:
  - [x] Updated transition on `.btn-submit::before` in `forgot_password.html`, `login.html`, and `reset_password.html` (both root and `en/` versions).
  - [x] Updated transition on `.notif-panel` in `en/_sidebar_head.html` and root `_sidebar_head.html`.
- [x] CSS Files:
  - [x] `dashboard-v4.css`
    - [x] Add font overrides block for `[dir="rtl"]` (Cairo, IBM Plex Arabic, Tajawal, sans-serif) with font-size: 16px and line-height: 1.8.
    - [x] Define `--text-x-direction` direction variable.
    - [x] Make translateX transitions direction-aware.
  - [x] `landing-v4.css`
    - [x] Add font overrides block for `[dir="rtl"]`.
    - [x] Define `--text-x-direction` direction variable.
    - [x] Make keyframes and translateX transitions direction-aware (slideInLeft, slideInRight, marquee, reveal-left, reveal-right).
    - [x] Fix transition property for `.cta-btn::before` to use `inset-inline-start` instead of `left`.
  - [x] `cyberpunk.css`
    - [x] Add font overrides block for `[dir="rtl"]`.
    - [x] Define `--text-x-direction` direction variable.
- [x] Verification:
  - [x] Run verify_integrity.py.
  - [x] Run pytest suite.
