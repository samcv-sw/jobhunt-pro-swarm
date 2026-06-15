import asyncio
from playwright.async_api import async_playwright

async def main():
    pages_to_screenshot = [
        ('/login', 'login_screenshot.png'),
        ('/register', 'register_screenshot.png'),
        ('/pricing', 'pricing_screenshot.png'),
        ('/about', 'about_screenshot.png')
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        
        for route, filename in pages_to_screenshot:
            print(f"Taking screenshot of {route}...")
            url = f'http://127.0.0.1:8000{route}'
            await page.goto(url, wait_until='networkidle')
            await page.screenshot(path=f'C:\\Users\\samde\\.gemini\\antigravity\\brain\\bf7a2a2b-e5f4-430c-881d-9470b1e426b8\\{filename}', full_page=True)
            
        await browser.close()
        print("Done!")

if __name__ == '__main__':
    asyncio.run(main())
