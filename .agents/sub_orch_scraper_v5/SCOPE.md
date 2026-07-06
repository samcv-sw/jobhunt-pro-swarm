# Scope: Scraper Stealth & Proxy Hardening

## Overview
Audit and refine scrapers to ensure resilient spoofing against high-end anti-bot mitigations and perfect structured data extraction.

## Requirements & Fixes
1. **Proxy Leak in Browser Fallback**: Modify `scrapers/stealth_ingest.py` (specifically `NodriverFallback` and any other browser fallback classes like `ApexCamoufoxFallback` if proxy is missing) to inject the active proxy server configuration.
   - For `NodriverFallback.get_page_content`, pass the proxy IP/port to Chrome launch flags (e.g. `--proxy-server=http://...` or `--proxy-server=socks5://...`). Ensure that when curl_cffi fails and browser fallback is triggered, it does not leak the server's real IP address.
2. **Structured Output Invariant**: Ensure all scraper code blocks return structured `list[dict]` containing at minimum `title` and `url` keys.

## Complete Criteria
- Nodriver browser runs with proxy settings.
- Scraper does not bypass proxy configuration and leak host IP on proxy fail.
