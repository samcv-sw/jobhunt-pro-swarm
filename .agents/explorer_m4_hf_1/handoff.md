# Handoff Report: Browser Scraper Performance Optimization (Milestone 4)

## 1. Observation
We observed the following files and code locations in the codebase during the investigation of browser-based scraping scripts:

1. **`scrapers/stealth_ingest.py`**:
   - Integrates progressive fallbacks when HTTP requests fail or bot detection is triggered.
   - At lines 493–497, `NodriverFallback` is called:
     ```python
     html_content = await NodriverFallback.get_page_content(url, proxy=proxy_str)
     ```
   - At lines 502–506, `ApexCamoufoxFallback` is called:
     ```python
     html_content = await ApexCamoufoxFallback.get_page_content(url, proxy=proxy_str)
     ```

2. **`core/stealth.py`**:
   - Defines the fallback classes `NodriverFallback` (line 629) and `ApexCamoufoxFallback` (line 713).
   - In `NodriverFallback.get_page_content` (lines 649–656), the Chrome instance is started and immediately navigated:
     ```python
     browser_args = []
     if proxy:
         browser_args.append(f"--proxy-server={proxy}")

     # On some environments headless=True may be detected, but usually Nodriver handles it well
     browser = await uc.start(headless=True, browser_args=browser_args)
     page = await browser.get(url)
     ```
   - In `ApexCamoufoxFallback.get_page_content` (lines 734–736), the Camoufox browser (Playwright-based) is created and navigated:
     ```python
     # Using Camoufox which intercepts and overrides WebGL/Canvas natively
     async with AsyncCamoufox(headless=True, proxy=proxy) as browser:
         page = await browser.new_page()
         await page.goto(url)
     ```

3. **`core/zero_cost_stealth_browser.py`**:
   - Defines `ZeroCostStealthScraper` using `undetected_chromedriver` synchronously.
   - At lines 37–47, Chrome is initialized and navigated:
     ```python
     def _scrape_sync():
         options = uc.ChromeOptions()
         options.add_argument("--headless")
         options.add_argument("--disable-gpu")
         # Add free community proxies here if needed

         driver = uc.Chrome(options=options)
         try:
             driver.get(url)
             # Wait for JS challenge to pass
             time.sleep(5)
             return driver.page_source
     ```

4. **`core/stealth_http.py`**:
   - Implements a request-based stealth client (`StealthClient` / `AsyncStealthClient`) using `curl_cffi` or `httpx`. Since it only fetches raw HTML documents and does not execute JS or fetch subresources (stylesheets, images, fonts, trackers), it is already fully optimal and does not require resource blocking.

---

## 2. Logic Chain
To reduce RAM and network bandwidth usage for browser-based scrapers, we must block heavy resources (images, fonts, stylesheets, and trackers) before page navigation occurs.

1. **Chromium-based Engines (`nodriver` and `undetected-chromedriver`)**:
   - **Launch/CLI Arguments**: Chromium allows blocking images and remote fonts at the browser launch level by passing CLI flags:
     - `--blink-settings=imagesEnabled=false` blocks images at the layout engine level.
     - `--disable-remote-fonts` disables downloading custom fonts.
   - **CDP (Chrome DevTools Protocol)**: Chromium's `Network.setBlockedURLs` command allows blocking matching network requests. This is the only way to block stylesheets (`*.css`) and trackers (`*google-analytics*`, etc.) without browser extensions.
     - **For `nodriver`**: The `Tab` class provides a `send(cdp_obj)` method to run CDP commands. We can use `browser.main_tab` (which accesses the default pre-opened page) to enable network and set blocked URLs *before* calling `page.get(url)`.
     - **For `undetected-chromedriver`**: Selenium provides `driver.execute_cdp_cmd(cmd_name, cmd_args)`. This can be called right after driver initialization, before executing `driver.get(url)`.

2. **Playwright-based Engine (`camoufox` / `Playwright`)**:
   - Playwright allows network request interception and blocking via `page.route()`.
   - By routing all requests (`"**/*"`), we can inspect `route.request.resource_type` (blocking `"image"`, `"font"`, `"stylesheet"`, and `"media"`) and check `route.request.url` for tracker/analytics keywords, aborting matches and continuing others. This operates at the network protocol level and prevents any data transfer for blocked resources.

---

## 3. Caveats
- **Blocking Stylesheets**: Some modern websites use JavaScript to detect element visibility or position. If stylesheets are blocked, elements might appear visible or misaligned in the DOM. This could occasionally trigger bot detection honeypots (which rely on hidden elements) or break certain parsing logic if it depends on style-computed properties. In testing, standard HTML structure remains intact, so CSS blocking should be evaluated site-by-site if issues arise.
- **Camoufox Environment**: `camoufox` is currently not installed in the local environment, but its usage is mocked/stubbed in tests and called conditionally. The proposed Playwright-based routing is fully compatible with standard Playwright Page objects used by Camoufox.

---

## 4. Conclusion
We recommend implementing a double-layered optimization strategy for the three browser-based engines:
1. **`nodriver` (`core/stealth.py`)**: Use launch arguments for images and fonts, and CDP `setBlockedURLs` via `page.send` on the default `main_tab` for stylesheets and trackers.
2. **`camoufox` (`core/stealth.py`)**: Use Playwright's `page.route` to abort heavy resources and trackers.
3. **`undetected-chromedriver` (`core/zero_cost_stealth_browser.py`)**: Use launch arguments for images and fonts, and CDP `Network.setBlockedURLs` via `driver.execute_cdp_cmd` for stylesheets and trackers.

Precise code changes are prepared in the patch file `performance_optimizations.patch` in our working directory.

---

## 5. Verification Method
To verify the changes independently, the implementer should:
1. Apply the patch `performance_optimizations.patch` to the codebase.
2. Run the test suite to ensure no regressions:
   ```pwsh
   pytest tests/test_stealth_parser_and_fallbacks.py
   ```
3. Run a network/RAM audit test. Create a test script that navigates to a local test page (or mock server) containing images, stylesheets, fonts, and tracker scripts. Verify that:
   - Network requests for images (`.png`/`.jpg`), stylesheets (`.css`), fonts (`.woff`/`.ttf`), and analytics hosts are aborted / blocked.
   - The memory footprint of the browser processes is reduced compared to baseline runs.
