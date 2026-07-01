import asyncio
import re
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def automate_fly_login():
    print("Starting Fly.io OAuth Automation...")
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
        print(f"Flyctl: {text}")
        if "https://fly.io/app/auth/cli/" in text:
            match = re.search(r'(https://fly\.io/app/auth/cli/\S+)', text)
            if match:
                oauth_url = match.group(1)
                break

    if not oauth_url:
        print("Could not find OAuth URL.")
        return

    print(f"\nExtracted Fly OAuth URL: {oauth_url}")
    print("Launching Browser to authenticate...")

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
            print("Submitted login form...")

            # Wait for authorize button
            try:
                await page.wait_for_selector('button:has-text("Continue")', timeout=15000)
                await page.click('button:has-text("Continue")')
                print("Clicked Continue (Authorize)!")
            except:
                pass

            try:
                await page.wait_for_selector('button:has-text("Authorize")', timeout=5000)
                await page.click('button:has-text("Authorize")')
                print("Clicked Authorize!")
            except:
                pass

            print("Waiting for Flyctl to complete...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Browser automation failed: {e}")
            await page.screenshot(path="fly_error.png")
            print("Saved screenshot to fly_error.png")
        finally:
            await browser.close()
    
    await process.wait()
    print("Flyctl process completed.")

if __name__ == "__main__":
    asyncio.run(automate_fly_login())
