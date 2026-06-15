import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        # 1. Register a test user
        print("Registering user...")
        await page.goto('http://127.0.0.1:8000/register', wait_until='networkidle')
        await page.fill('input[name="name"]', 'Test User')
        await page.fill('input[name="email"]', 'test_ui@jobhuntpro.com')
        await page.fill('input[name="password"]', 'password123')
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(2000) # wait for redirect to dashboard
        
        # 2. Login just in case (sometimes register auto-logs in, sometimes it redirects to login)
        if '/login' in page.url:
            print("Logging in...")
            await page.fill('input[name="email"]', 'test_ui@jobhuntpro.com')
            await page.fill('input[name="password"]', 'password123')
            await page.click('button[type="submit"]')
            await page.wait_for_timeout(2000)
            
        print(f"Current URL after auth: {page.url}")
        
        # 3. Take screenshots of internal pages
        pages = [
            ('/dashboard', 'dashboard_screenshot.png'),
            ('/upload-cv', 'upload_cv_screenshot.png'),
            ('/wallet', 'wallet_screenshot.png'),
            ('/services', 'services_screenshot.png'),
            ('/stats', 'stats_screenshot.png')
        ]
        
        for route, filename in pages:
            print(f"Taking screenshot of {route}...")
            url = f'http://127.0.0.1:8000{route}'
            await page.goto(url, wait_until='networkidle')
            await page.screenshot(path=f'C:\\Users\\samde\\.gemini\\antigravity\\brain\\bf7a2a2b-e5f4-430c-881d-9470b1e426b8\\{filename}', full_page=True)
            
        await browser.close()
        print("Done auth screenshots!")

if __name__ == '__main__':
    asyncio.run(main())
