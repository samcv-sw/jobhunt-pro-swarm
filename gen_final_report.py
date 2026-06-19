#!/usr/bin/env python3
"""Comprehensive analysis and final report for Indeed proxy bypass tests."""
import json
from datetime import datetime

results = json.load(open("proxy_test_results/all_results.json", "r", encoding="utf-8"))

ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Manual reclassification based on actual content analysis
# JinaAI returned Cloudflare challenge page = NOT truly working
manual_corrections = {
    "04_JinaAI_NoHTTPPrefix": {"reality": "CLOUDFLARE_CHALLENGE", "real_success": False,
        "note": "HTTP 200 but content is Indeed's Cloudflare challenge page (Just a moment...)"},
    "04b_JinaAI_WithHTTPPrefix": {"reality": "CLOUDFLARE_CHALLENGE", "real_success": False,
        "note": "Same as above - Jina AI proxy connects but Indeed serves Cloudflare challenge"},
}

report = f"""================================================================================
INDEED PROXY BYPASS TEST - FINAL REPORT
Date: {ts}
Test Location: C:\\Users\\samde\\Desktop\\cv sam new ma3 kimi (Beirut, Lebanon)
================================================================================

NOTE: 'HasJobs=True' in raw tests was a false positive for Jina AI responses
      because Indeed's Cloudflare challenge page contains nav links with 'job'
      (e.g. "Find jobs" in the nav menu).
      All results below are VERIFIED by full content inspection.

================================================================================
SUMMARY: WHAT WORKS
================================================================================

  YES - Dice.com
       URL: https://www.dice.com/jobs?q=network+engineer&location=Dubai
       Status: HTTP 200, 353KB HTML
       Verdict: Full page returned with job content. BUT data is JS-rendered
                (Next.js). API endpoints (v1/v2) return 404/HTML. Would need
                browser automation (Playwright/Selenium) or finding the correct
                internal API to extract structured job data.

  YES - LinkedIn Jobs
       URL: https://www.linkedin.com/jobs/search/?keywords=network+engineer&location=Dubai
       Status: HTTP 200
       Verdict: Directly accessible, no blocking. Contains job listings.
                LinkedIn is NOT blocked in Lebanon.

  YES - Bing Search (for Indeed job discovery)
       URL: https://www.bing.com/search?q=site:indeed.com+network+engineer+Dubai
       Status: HTTP 200
       Verdict: Bing indexes Indeed jobs. Can search and find Indeed job links
                through Bing's search results.

================================================================================
SUMMARY: WHAT DOES NOT WORK
================================================================================

  NO  - Indeed direct (any domain)
       .com, .ae → 403 (Cloudflare WAF block)
       Both RSS and jobs pages blocked.

  NO  - RSSHub (any instance)
       rsshub.app → 403 (Cloudflare block on RSSHub's own Indeed route)
       rsshub.bili.xyz → DNS resolution failed

  NO  - Google Web Cache
       webcache.googleusercontent.com → 429 (rate limited from this IP)
       Alternative: HTTP 200 but returned Google Search page, not cached content

  NO  - Jina AI (r.jina.ai)
       HTTP 200 but content is Cloudflare challenge page ("Just a moment...")
       Jina AI proxy can CONNECT to Indeed, but Indeed returns the challenge.
       Essentially blocked.

  NO  - AllOrigins CORS Proxy
       api.allorigins.win → 522 (connection timeout)

  NO  - CORSProxy.io
       → 403 (free tier limited to localhost only)

  NO  - ThingProxy / proxy.cors.dev
       → DNS resolution failures (services no longer active)

  NO  - CORS Anywhere (Heroku)
       → 403 (demo endpoint requires specific origin, doesn't allow Indeed)

  NO  - Bing Cache (cc.bingj.com)
       → DNS resolution failure (service no longer active)

  NO  - Glassdoor
       → 403 (Cloudflare WAF block, "Security | Glassdoor" challenge page)
       Both direct jobs page and search page blocked.

  NO  - Monster.com
       → 403 (WAF blocked, explicit "waf blocked - monster" error)

  NO  - Wayback Machine
       → 404 (no archived copy of Indeed RSS)

================================================================================
DETAILED BREAKDOWN
================================================================================

Platform        Endpoint                    HTTP    Blocked?    Notes
-------         --------                    ----    -------    -----
Indeed RSS      indeed.com/rss              403     YES (CF)   Cloudflare WAF
Indeed Jobs     indeed.com/jobs             403     YES (CF)   Cloudflare WAF
Indeed UAE      indeed.ae/jobs              403     YES (CF)   Cloudflare WAF
RSSHub (std)    rsshub.app/indeed/jobs      403     YES (CF)   RSSHub itself blocked fetching Indeed
Google Cache    webcache.googleusercontent  429     YES        Rate limited from Lebanon IP
Jina AI (any)   r.jina.ai/*                 200     YES (CF)   Cloudflare challenge page returned
AllOrigins      api.allorigins.win          522     YES        Timeout
CORSProxy.io    corsproxy.io                403     YES        Free tier restriction
CORS Anywhere   cors-anywhere.herokuapp.com 403     YES        Origin restriction

Glassdoor       glassdoor.com/jobs          403     YES (CF)   Cloudflare WAF
Monster         monster.com/jobs            403     YES (WAF)  Explicit WAF block
Wayback Machine web.archive.org             404     YES        No archived copy

Dice.com        dice.com/jobs               200     NO         Works! JS-rendered
LinkedIn Jobs   linkedin.com/jobs           200     NO         Works! Direct access
Bing Search     bing.com/search             200     NO         Works! Can find Indeed via search

================================================================================
RECOMMENDATIONS FOR JobHunt Pro
================================================================================

1. PRIMARY REPLACEMENT: DICE.COM
   - Not blocked, returns full job listings
   - Need to scrape via browser automation (Playwright) or find the internal API
   - Dice's search API endpoint needs investigation: try intercepting XHR calls
  
2. SECONDARY: LINKEDIN JOBS
   - Not blocked, directly accessible
   - Can scrape job listings directly via HTTP
   - LinkedIn has good coverage for Dubai/UAE network engineer roles

3. INDEED WORKAROUND: BING SEARCH
   - Bing indexes Indeed jobs
   - Can parse Bing search results to get Indeed job URLs
   - Limitation: only shows what Bing indexed, not full Indeed search results

4. DOES NOT WORK (save time, don't retry):
   - RSSHub (blocked at Indeed's end)
   - Jina AI / textise.iitty (Cloudflare challenge)
   - Any CORS proxy (blocked, rate limited, or dead)
   - Google Cache (429 rate limited)
   - Glassdoor, Monster (both blocked like Indeed)

================================================================================
"""

with open("proxy_test_results/FINAL_REPORT.txt", "w", encoding="utf-8") as f:
    f.write(report)

print(report)
