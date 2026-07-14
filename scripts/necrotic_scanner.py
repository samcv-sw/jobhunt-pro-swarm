import asyncio
import json
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

BASE_URL = "https://jhfguf.pythonanywhere.com"

# The audit registry
audit_registry = {
    "timestamp": str(datetime.now()),
    "necrotic_links": [],
    "broken_endpoints": [],
    "missing_hrefs": []
}

async def scan():
    visited_urls = set()
    urls_to_visit = {BASE_URL}

    # Store all discovered internal links
    all_internal_links = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a generic Windows Chrome User-Agent to bypass Aegis Shield
        context = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # Crawl to extract links
        while urls_to_visit:
            current_url = urls_to_visit.pop()
            if current_url in visited_urls:
                continue

            visited_urls.add(current_url)
            logging.info(f"Crawling: {current_url}")

            try:
                response = await page.goto(current_url, wait_until='domcontentloaded', timeout=15000)
                if not response or not response.ok:
                    audit_registry["broken_endpoints"].append({
                        "url": current_url,
                        "status": response.status if response else "Timeout/Unknown",
                        "reason": "Page load failed during crawl"
                    })
                    continue
            except Exception as e:
                logging.error(f"Failed to navigate to {current_url}: {e}")
                audit_registry["broken_endpoints"].append({
                    "url": current_url,
                    "status": "Error",
                    "reason": str(e)
                })
                continue

            # Extract interactive elements
            links = await page.locator("a").evaluate_all(
                "elements => elements.map(e => { return {href: e.getAttribute('href'), text: e.innerText, html: e.outerHTML} })"
            )

            for link in links:
                href = link.get('href')
                text = link.get('text', '').strip()
                html_snippet = link.get('html', '')

                # Check for missing href
                if href is None:
                    audit_registry["missing_hrefs"].append({
                        "page": current_url,
                        "text": text,
                        "snippet": html_snippet
                    })
                    continue

                # Check for necrotic links
                href_stripped = href.strip()
                if href_stripped in ['#', '', 'javascript:void(0)', 'javascript:void(0);']:
                    audit_registry["necrotic_links"].append({
                        "page": current_url,
                        "href": href_stripped,
                        "text": text
                    })
                    continue

                # Normalize URL
                absolute_url = urljoin(current_url, href_stripped)
                parsed = urlparse(absolute_url)

                # Only follow internal HTTP/HTTPS links
                if parsed.netloc == urlparse(BASE_URL).netloc and parsed.scheme in ['http', 'https']:
                    # Remove fragments for deduplication
                    clean_url = absolute_url.split('#')[0]
                    if clean_url not in visited_urls:
                        all_internal_links.add(clean_url)

        # Dispatch async HEAD requests to all discovered internal links
        logging.info(f"Verifying {len(all_internal_links)} discovered internal endpoints...")

        # We can use Playwright's APIRequestContext
        api_context = await p.request.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )

        async def check_url(url):
            try:
                # Some servers reject HEAD, so we use GET but abort reading body if possible
                res = await api_context.get(url, timeout=10000)
                if not res.ok:
                    audit_registry["broken_endpoints"].append({
                        "url": url,
                        "status": res.status,
                        "reason": "Returned non-2xx status code"
                    })
            except Exception as e:
                audit_registry["broken_endpoints"].append({
                    "url": url,
                    "status": "Error",
                    "reason": str(e)
                })

        # Process in batches of 10 to avoid hammering the server
        link_list = list(all_internal_links)
        batch_size = 10
        for i in range(0, len(link_list), batch_size):
            batch = link_list[i:i+batch_size]
            await asyncio.gather(*(check_url(url) for url in batch))

        await browser.close()
        await api_context.dispose()

    # Save to JSON
    with open("necrotic_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_registry, f, indent=4, ensure_ascii=False)

    logging.info("Audit complete. Results saved to necrotic_audit.json")

if __name__ == "__main__":
    asyncio.run(scan())
