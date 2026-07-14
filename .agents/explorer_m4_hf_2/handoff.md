# Handoff Report: Browser Scraper Performance Optimization (Milestone 4)

## 1. Observation

During our read-only investigation, we mapped out the browser-based scraping infrastructure across the codebase. Three browser automation systems were identified:

1. **Nodriver** (`core/stealth.py`, lines 629-710):
   Used as the primary headless Chrome browser fallback via Chrome DevTools Protocol (CDP).
   ```python
   654:             browser = await uc.start(headless=True, browser_args=browser_args)
   655:             page = await browser.get(url)
   ```

2. **Camoufox** (`core/stealth.py`, lines 713-751):
   Used as the advanced WAF bypass browser context (based on Firefox/Playwright).
   ```python
   734:             async with AsyncCamoufox(headless=True, proxy=proxy) as browser:
   735:                 page = await browser.new_page()
   736:                 await page.goto(url)
   ```

3. **Undetected Chromedriver** (`core/zero_cost_stealth_browser.py`, lines 12-63):
   Used as a secondary standalone Selenium-based Chrome automation instance.
   ```python
   37:             options = uc.ChromeOptions()
   38:             options.add_argument("--headless")
   39:             options.add_argument("--disable-gpu")
   ...
   42:             driver = uc.Chrome(options=options)
   43:             try:
   44:                 driver.get(url)
   ```

We also inspected the `camoufox` configuration module in the project's virtual environment (`test_env/Lib/site-packages/camoufox/utils.py` lines 590-592), which reveals native support for image blocking via Firefox preferences:
```python
590:     # Set Firefox user preferences
591:     if block_images:
592:         LeakWarning.warn('block_images', i_know_what_im_doing)
593:         firefox_user_prefs['permissions.default.image'] = 2
```

---

## 2. Logic Chain

Our step-by-step reasoning for implementing Milestone 4 performance optimizations:
1. **Network & RAM Reduction Goal**: Reducing RAM and bandwidth requires preventing heavy files (images, fonts, stylesheets, and tracking scripts) from downloading.
2. **Nodriver Integration**: Since Nodriver uses Chrome DevTools Protocol (CDP), the most efficient way to block resource requests is via the CDP `Network` domain (`Network.enable` followed by `Network.setBlockedURLs`). This must run on `browser.main_tab` *before* calling `page.get(url)` so that the initial page load does not fetch the heavy assets.
3. **Camoufox (Playwright) Integration**:
   - Images can be blocked at the engine level by passing `block_images=True` and `i_know_what_im_doing=True` (to suppress warnings) to `AsyncCamoufox(...)` initialization.
   - Other assets (stylesheets, fonts, media, and third-party trackers) can be aborted using Playwright's native request interceptor `page.route("**/*", route_handler)`.
4. **Undetected Chromedriver Integration**:
   - Image blocking can be configured via Chrome preferences (`profile.managed_default_content_settings.images = 2`).
   - Stylesheets, fonts, and trackers can be blocked using CDP command execution (`driver.execute_cdp_cmd`) prior to calling `driver.get(url)`.

---

## 3. Caveats

- **Bot-Detection Risks with Stylesheet Blocking**: Bypassing sophisticated challenges (such as Cloudflare Turnstile or DataDome) often relies on browser environment checks that inspect CSS properties (e.g. element layout, visibility, rendering speeds). Completely blocking stylesheets (`*.css`) may trigger bot-detection WAF blocks. We recommend making stylesheet blocking configurable (e.g. dynamic bypass depending on the target site's protection level).
- **Virtual Environment Execution**: Camoufox and its dependencies (such as playwright) are installed in the `test_env` virtual environment. Verification and execution must be performed using the python binary from `test_env/Scripts/python`.

---

## 4. Conclusion

Milestone 4 can be implemented by modifying the three browser automation managers to block heavy resources before page navigation. Below are the recommended code modifications:

### Proposed Modification 1: `core/stealth.py` (`NodriverFallback`)
Replace lines 654-655 in `core/stealth.py` with:
```python
            browser = await uc.start(headless=True, browser_args=browser_args)
            page = browser.main_tab
            
            # Block heavy resources via CDP Network domain before navigation
            try:
                await page.send(uc.cdp.network.enable())
                blocked_patterns = [
                    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.webp", "*.ico",  # Images
                    "*.woff", "*.woff2", "*.ttf", "*.otf",                           # Fonts
                    "*.css",                                                         # Stylesheets
                    "*analytics*", "*tracker*", "*google-analytics*", "*doubleclick*", "*adsystem*"  # Trackers
                ]
                await page.send(uc.cdp.network.set_blocked_ur_ls(urls=blocked_patterns))
                logger.info("[Nodriver] Enabled performance resource blocking.")
            except Exception as net_err:
                logger.warning(f"[Nodriver] Failed to enable resource blocking: {net_err}")
                
            # Navigate using configured page tab
            await page.get(url)
```

### Proposed Modification 2: `core/stealth.py` (`ApexCamoufoxFallback`)
Replace lines 734-736 in `core/stealth.py` with:
```python
            # Pass block_images=True to disable image loading at browser engine level.
            # Pass i_know_what_im_doing=True to suppress image-blocking warnings.
            async with AsyncCamoufox(
                headless=True, 
                proxy=proxy, 
                block_images=True, 
                i_know_what_im_doing=True
            ) as browser:
                page = await browser.new_page()

                # Block fonts, stylesheets, and trackers via Playwright route interception
                async def block_resources(route):
                    resource_type = route.request.resource_type
                    req_url = route.request.url.lower()

                    # Stylesheets and fonts
                    if resource_type in ["font", "media", "stylesheet"]:
                        await route.abort()
                        return

                    # Trackers / ads
                    tracker_keywords = [
                        "analytics", "google-analytics", "doubleclick", 
                        "adsystem", "facebook", "tracker", "hotjar"
                    ]
                    if any(kw in req_url for kw in tracker_keywords):
                        await route.abort()
                        return

                    await route.continue_()

                await page.route("**/*", block_resources)
                await page.goto(url)
```

### Proposed Modification 3: `core/zero_cost_stealth_browser.py` (`ZeroCostStealthScraper`)
Replace lines 37-47 in `core/zero_cost_stealth_browser.py` with:
```python
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            
            # Disable image loading via Chrome preferences
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)

            driver = uc.Chrome(options=options)
            try:
                # Disable stylesheets, fonts, and trackers via CDP before navigation
                try:
                    driver.execute_cdp_cmd("Network.enable", {})
                    blocked_patterns = [
                        "*.woff", "*.woff2", "*.ttf", "*.otf",
                        "*.css",
                        "*analytics*", "*tracker*", "*google-analytics*", "*doubleclick*", "*adsystem*"
                    ]
                    driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": blocked_patterns})
                    logger.info("[Undetected Chromedriver] CDP resource blocking enabled.")
                except Exception as net_err:
                    logger.warning(f"[Undetected Chromedriver] Failed to set resource blocking: {net_err}")

                driver.get(url)
                # Wait for JS challenge to pass
                time.sleep(5)
                return driver.page_source
```

---

## 5. Verification Method

To independently verify these changes:
1. **Apply the modifications** outlined in the Conclusion section.
2. **Run the Stealth Parser Unit Tests** to verify that WAF fallbacks, crawler orchestration, and page loading mechanisms continue to operate correctly:
   ```bash
   .\test_env\Scripts\pytest tests/test_stealth_parser_and_fallbacks.py
   ```
3. **Audit Resource Loading in Logs**: In the test execution or sandbox run, monitor the outbound browser requests/CDP logs. Requests for `.css`, `.png`, `google-analytics.com`, etc., must return aborted/failed or show zero network bandwidth consumption.
