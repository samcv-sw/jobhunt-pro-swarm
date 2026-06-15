import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 800})
        await page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
        await page.screenshot(path='C:\\Users\\samde\\.gemini\\antigravity\\brain\\bf7a2a2b-e5f4-430c-881d-9470b1e426b8\\home_screenshot.png', full_page=True)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
