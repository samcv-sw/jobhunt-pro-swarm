import asyncio
import re
import sys

from playwright.async_api import async_playwright

# Fix stdout encoding for windows
sys.stdout.reconfigure(encoding='utf-8')

async def automate_wrangler_login():
    logger.debug("Starting Wrangler OAuth Automation...")
    # Start wrangler login process
    process = await asyncio.create_subprocess_shell(
        "npx wrangler login",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    oauth_url = None
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        text = line.decode('utf-8', errors='ignore').strip()
        logger.debug(f"Wrangler: {text}")
        if "https://dash.cloudflare.com/oauth2/auth" in text:
            # Extract URL
            match = re.search(r'(https://dash\.cloudflare\.com/oauth2/auth\S+)', text)
            if match:
                oauth_url = match.group(1)
                break

    if not oauth_url:
        logger.debug("Could not find OAuth URL.")
        return

    logger.debug(f"\nExtracted OAuth URL: {oauth_url}")
    logger.debug("Launching Browser to authenticate...")

    async with async_playwright() as p:
        # Launch headed to avoid some bot detection, or headless if needed
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(oauth_url)

            # Wait for email input
            await page.wait_for_selector('input[name="email"]', timeout=15000)
            await page.fill('input[name="email"]', "samsalameh.cv@gmail.com")
            await page.fill('input[name="password"]', "JHGHjhfg^%^%*6853^%*%^tdhgHJF^%#")

            # Click login
            await page.click('button[type="submit"]')
            logger.debug("Submitted login form...")

            # Wait for Authorize page
            try:
                await page.wait_for_selector('button:has-text("Allow")', timeout=15000)
                await page.click('button:has-text("Allow")')
                logger.debug("Clicked Allow!")
            except Exception:
                logger.debug("Could not find Allow button immediately. Checking for account selection...")
                # Try clicking the account if it prompts
                account_button = await page.query_selector('div[data-testid="account-card"]')
                if account_button:
                    await account_button.click()
                    await page.wait_for_selector('button:has-text("Allow")', timeout=15000)
                    await page.click('button:has-text("Allow")')
                    logger.debug("Clicked Allow after account selection!")

            logger.debug("Waiting for Wrangler to complete...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.debug(f"Browser automation failed: {e}")
            await page.screenshot(path="cloudflare_error.png")
            logger.debug("Saved screenshot to cloudflare_error.png")
        finally:
            await browser.close()

    # Wait for wrangler to finish
    await process.wait()
    logger.debug("Wrangler process completed.")

if __name__ == "__main__":
    asyncio.run(automate_wrangler_login())
