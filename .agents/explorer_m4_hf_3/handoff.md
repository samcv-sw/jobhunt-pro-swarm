# Handoff Report: Milestone 4 - Browser Scraper Performance Optimization

## 1. Observation
- **Orchestration Entry Point**: `scrapers/stealth_ingest.py` (lines 492-508) orchestrates scraping and falls back to browser-based mechanisms when HTTP sessions fail or hit challenges:
  ```python
  if not html_content:
      logger.warning(f"Stealth fetch returned empty or challenged content. Trying NodriverFallback for {url}.")
      try:
          from core.stealth import NodriverFallback
          proxy_str = proxy_config.get("http") if proxy_config else None
          html_content = await NodriverFallback.get_page_content(url, proxy=proxy_str)
      ...
      if not html_content or any(k in html_content.lower() for k in ["just a moment", "attention required", "turnstile", "ddg-captcha"]):
          logger.warning(f"Nodriver fallback failed or was challenged. Trying ApexCamoufoxFallback for {url}.")
          try:
              from core.stealth import ApexCamoufoxFallback
              proxy_str = proxy_config.get("http") if proxy_config else None
              html_content = await ApexCamoufoxFallback.get_page_content(url, proxy=proxy_str)
  ```
- **Nodriver Integration**: `core/stealth.py` (lines 629-711) implements `NodriverFallback` which starts a headless browser and directly navigates to a URL:
  ```python
  browser = await uc.start(headless=True, browser_args=browser_args)
  page = await browser.get(url)
  ```
- **Camoufox Integration**: `core/stealth.py` (lines 713-751) implements `ApexCamoufoxFallback` using Playwright-based `AsyncCamoufox`:
  ```python
  async with AsyncCamoufox(headless=True, proxy=proxy) as browser:
      page = await browser.new_page()
      await page.goto(url)
  ```
- **Undetected Chromedriver**: `core/zero_cost_stealth_browser.py` (lines 12-60) implements `ZeroCostStealthScraper` using Selenium-based `undetected_chromedriver`:
  ```python
  driver = uc.Chrome(options=options)
  try:
      driver.get(url)
  ```
- **Ghost Applicant Integration**: `core/ghost_applicant.py` (lines 8-71) implements `GhostApplicant` using Playwright to fill forms:
  ```python
  async with async_playwright() as p:
      browser = await p.chromium.launch(headless=True)
      context = await browser.new_context(...)
      page = await context.new_page()
      await page.goto(url, wait_until="networkidle")
  ```
- **CDP Bindings for Nodriver**: Python package diagnostics showed that `nodriver.cdp.network` exposes standard Chrome DevTools Protocol commands:
  ```python
  ['BlockPattern', 'BlockedReason', 'BlockedSetCookieWithReason', 'CookieBlockedReason', 'RenderBlockingBehavior', 'SetCookieBlockedReason', 'enable', 'enable_device_bound_sessions', 'enable_reporting_api', 'set_blocked_ur_ls']
  ```
  Note the camelCase conversion result `set_blocked_ur_ls` (accepting `urls: List[str]`).
- **Camoufox Module Status**: Running `python -c "import camoufox"` threw a `ModuleNotFoundError: No module named 'camoufox'`, indicating it is not pre-installed, though `playwright` (version `1.49.1`/`1.59.0`) is present and fully functional.
- **Tests Validation**: Running the project test suite using `pytest tests/test_stealth_parser_and_fallbacks.py tests/test_stealth_reliability.py` passed all 20 unit tests.

## 2. Logic Chain
- **Step 1**: Minimizing network and memory overhead is key to browser scraper performance optimization. Since browser fallbacks load full web pages, heavy assets (stylesheets, images, fonts, media) and tracking scripts should be blocked.
- **Step 2**: Chrome DevTools Protocol (CDP) provides native resource-blocking capabilities through `Network.setBlockedURLs` (mapped as `set_blocked_ur_ls` in Nodriver and Selenium CDP wrappers). Enabling this before page navigation intercepts and cancels the fetching of specified asset patterns.
- **Step 3**: Playwright provides `page.route` to intercept network requests. By inspecting `request.resource_type` and matching target domain regular expressions, matching asset and tracker requests can be aborted via `route.abort()`, while leaving necessary HTML/JS requests intact.
- **Step 4**: For applicant scripts like `core/ghost_applicant.py`, styling (stylesheets and fonts) must be retained to maintain layout correctness for form-filling interactions, but heavy assets like images and video/media, plus all trackers, can be safely blocked.

## 3. Caveats
- **Camoufox Package**: `camoufox` is currently not installed on the system, which prevents running `ApexCamoufoxFallback` locally without first performing `pip install camoufox`.
- **CSS Rendering Dependents**: Some SPA sites or job search engines may depend on style sheets or dynamic CSS-in-JS definitions for layout positioning and loading states. Blocking stylesheets (`.css`) could theoretically break DOM element extraction if the page blocks layout execution when styles are missing. If layout disruption occurs, the `*.css` pattern should be omitted from the blocklist.

## 4. Conclusion
To implement performance optimization for the browser scrapers, resource-blocking should be added to the three respective integrations.
We have produced `resource_blocking.patch` within the agent's folder which applies:
1. **Nodriver Blocking**:
   ```python
   page = await browser.main_tab
   await page.send(uc.cdp.network.enable())
   await page.send(uc.cdp.network.set_blocked_ur_ls(
       urls=[
           "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.webp", "*.ico",
           "*.css", "*.woff", "*.woff2", "*.ttf", "*.otf",
           "*analytics*", "*google-analytics.com*", "*doubleclick*", "*tracker*", "*facebook.com*", "*fbcdn*"
       ]
   ))
   await page.get(url)
   ```
2. **Camoufox / Playwright Blocking**:
   ```python
   async def route_intercept(route, request):
       if request.resource_type in {"image", "stylesheet", "font", "media"}:
           await route.abort()
       elif any(re.search(pat, request.url) for pat in [r"analytics", r"tracker", r"doubleclick", r"fbcdn"]):
           await route.abort()
       else:
           await route.continue_()
   await page.route("**/*", route_intercept)
   ```
3. **Undetected Chromedriver Blocking**:
   ```python
   prefs = {"profile.managed_default_content_settings.images": 2}
   options.add_experimental_option("prefs", prefs)
   ...
   driver.execute_cdp_cmd("Network.enable", {})
   driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": [...]})
   ```
4. **GhostApplicant Playwright Blocking**:
   ```python
   async def route_intercept(route, request):
       if request.resource_type in {"image", "media"}:
           await route.abort()
       elif any(re.search(pat, request.url) for pat in [r"analytics", r"tracker", r"doubleclick", r"fbcdn"]):
           await route.abort()
       else:
           await route.continue_()
   await page.route("**/*", route_intercept)
   ```

## 5. Verification Method
1. **Patch Verification**: Inspect and apply `resource_blocking.patch` from:
   `C:\Users\samde\Desktop\📂 Folders & Projects\cv sam new ma3 kimi\.agents\explorer_m4_hf_3\resource_blocking.patch`
2. **Test Command**: Execute the test commands to ensure the browser fallback mocks and parser unit tests are fully compliant and green:
   `pytest tests/test_stealth_parser_and_fallbacks.py tests/test_stealth_reliability.py`
3. **Performance Metrics**: Monitor the RAM usage and network logs during fallback crawls to verify that stylesheet, image, font, and tracker assets are not fetched.
