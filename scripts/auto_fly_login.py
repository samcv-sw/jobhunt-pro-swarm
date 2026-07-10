import asyncio
import re
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def automate_fly_login():
    logger.debug("Starting Fly.io OAuth Automation...")
    process = await asyncio.create_subprocess_shell(
        "flyctl auth login",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    oauth_url = None
    while True:
        line = await process.stdout.readline()
        if not line:
            break
        text = line.decode('utf-8', errors='ignore').strip()
        logger.debug(f"Flyctl: {text}")
        if "https://fly.io/app/auth/cli/" in text:
            match = re.search(r'(https://fly\.io/app/auth/cli/\S+)', text)
            if match:
                oauth_url = match.group(1)
                break

    if not oauth_url:
        logger.debug("Could not find OAuth URL.")
        return

    logger.debug(f"\nExtracted Fly OAuth URL: {oauth_url}")
    logger.debug("Launching Browser to authenticate...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            await page.goto(oauth_url)
            
            # Wait for email input
            await page.wait_for_selector('input[type="email"]', timeout=15000)
            await page.fill('input[type="email"]', "samsalameh.cv@gmail.com")
            await page.fill('input[type="password"]', "GFKHGFKH*^%$84854hgf")
            
            # Click sign in
            await page.click('button[type="submit"]')
            logger.debug("Submitted login form...")

            # Wait for authorize button
            try:
                await page.wait_for_selector('button:has-text("Continue")', timeout=15000)
                await page.click('button:has-text("Continue")')
                logger.debug("Clicked Continue (Authorize)!")
            except Exception as e:
                pass

            try:
                await page.wait_for_selector('button:has-text("Authorize")', timeout=5000)
                await page.click('button:has-text("Authorize")')
                logger.debug("Clicked Authorize!")
            except Exception as e:
                pass

            logger.debug("Waiting for Flyctl to complete...")
            await asyncio.sleep(5)
        except Exception as e:
            logger.debug(f"Browser automation failed: {e}")
            await page.screenshot(path="fly_error.png")
            logger.debug("Saved screenshot to fly_error.png")
        finally:
            await browser.close()
    
    await process.wait()
    logger.debug("Flyctl process completed.")

if __name__ == "__main__":
    asyncio.run(automate_fly_login())
