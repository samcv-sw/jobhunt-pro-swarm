## 2026-07-12T13:59:36Z

You are Worker M4. Your working directory is C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\worker_m4_stealth.
Your task is to implement Milestone 4: Browser Scraper Performance Optimization.
Specifically:
1. Configure NodriverFallback in core/stealth.py to block images and remote fonts via launch args, and block stylesheets and trackers via CDP set_blocked_ur_ls.
2. Configure ApexCamoufoxFallback in core/stealth.py to block images, stylesheets, fonts, media, and trackers using page.route.
3. Configure ZeroCostStealthScraper in core/zero_cost_stealth_browser.py to block images via experimental options, and block stylesheets/trackers via CDP commands.
4. Configure GhostApplicant in core/ghost_applicant.py to block images and trackers using Playwright page.route.
Refer to the patch and reports in C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m4_hf_3\resource_blocking.patch and C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m4_hf_1\handoff.md.

MANDATORY INTEGRITY WARNING — DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Run tests using 'pytest tests/test_stealth_parser_and_fallbacks.py' to verify. Document your changes and verification logs in your handoff report.
