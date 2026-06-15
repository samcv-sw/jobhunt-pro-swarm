
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        page = await context.new_page()
        
        pages = [
            ("01_homepage", "/"),
            ("02_login", "/login"),
            ("03_register", "/register"),
            ("04_pricing", "/pricing"),
            ("05_services", "/services"),
            ("06_contact", "/contact"),
            ("07_faq", "/faq"),
            ("08_blog", "/blog"),
        ]
        
        base = "https://jhfguf.pythonanywhere.com"
        
        for name, path in pages:
            try:
                await page.goto(base + path, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(2000)  # Wait for animations
                await page.screenshot(path=f"screenshots\\{name}.png", full_page=True)
                print(f"OK {name}: {await page.title()}")
            except Exception as e:
                print(f"ER {name}: {str(e)[:60]}")
        
        # Login then take auth pages
        await page.goto(base + "/login", wait_until="networkidle", timeout=15000)
        await page.fill('input[name="email"]', "test_audit_64668@temp.com")
        await page.fill('input[name="password"]', "TestPass123!")
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(3000)
        
        auth_pages = [
            ("09_dashboard", "/user-dashboard"),
            ("10_stats", "/stats"),
            ("11_wallet", "/wallet"),
            ("12_battle_station", "/battle-station"),
            ("13_new_campaign", "/new-campaign"),
            ("14_upload_cv", "/upload-cv"),
            ("15_sent_emails", "/sent-emails"),
            ("16_funnel_analytics", "/funnel-analytics"),
            ("17_ats_scorer", "/ats-scorer"),
            ("18_resume_tailor", "/resume-tailor"),
            ("19_employers", "/employers"),
            ("20_email_test", "/email-test"),
        ]
        
        for name, path in auth_pages:
            try:
                await page.goto(base + path, wait_until="networkidle", timeout=15000)
                await page.wait_for_timeout(2000)
                await page.screenshot(path=f"screenshots\\{name}.png", full_page=True)
                print(f"OK {name}: {await page.title()}")
            except Exception as e:
                print(f"ER {name}: {str(e)[:60]}")
        
        await browser.close()

asyncio.run(main())
