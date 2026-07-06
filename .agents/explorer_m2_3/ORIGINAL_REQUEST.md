## 2026-07-06T09:19:18Z

Identity: You are teamwork_preview_explorer (Explorer 3).
Working directory: c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_3

Task:
Perform an audit of backend route variables, navigation, performance, and SEO.
Identify:
1. Inspect `web/app_v2.py` and see what routes render templates with empty or missing context variables (e.g. `jobs`, `stats`, `user_data`, etc.). Identify what variables are referenced in Jinja2 templates but are missing from backend contexts (potential Jinja2 UndefinedErrors).
2. Check `_pa_server.log` (if it exists) or check page loading errors.
3. Run or check if we can run tests/audits (e.g., look for `qa_spider.py` or inspect links in templates) to check for 404 links or broken routing.
4. Audit templates for image lazy loading (`loading="lazy"` on all `<img>` tags).
5. Audit templates for preload hints (`rel="preload"`) for critical fonts and CSS.
6. Check if `<html>` tags have the correct `lang` and `dir` attributes.
7. Check for structured data (JSON-LD) in landing, pricing, and FAQ pages.
8. Check sitemap.xml and robots.txt.

Output: Write your detailed findings to `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_3\analysis.md` and write a handoff report `c:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m2_3\handoff.md`. Communicate your results back using the send_message tool.
