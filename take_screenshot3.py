from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        print("Logging in...")
        page.goto('https://jhfguf.pythonanywhere.com/login')
        page.fill('input[name="email"]', 'samde@samde.com')
        page.fill('input[name="password"]', 'samdesamde')
        page.click('button[type="submit"]')
        time.sleep(3)
        print("Navigating to dashboard...")
        page.goto('https://jhfguf.pythonanywhere.com/user-dashboard')
        time.sleep(3)
        print("Taking screenshot...")
        page.screenshot(path='c:\\Users\\samde\\Desktop\\cv sam new ma3 kimi\\dashboard_real.png', full_page=True)
        
        # Take a screenshot of the wallet page too
        page.goto('https://jhfguf.pythonanywhere.com/wallet')
        time.sleep(3)
        page.screenshot(path='c:\\Users\\samde\\Desktop\\cv sam new ma3 kimi\\wallet_real.png', full_page=True)
        
        browser.close()

if __name__ == '__main__':
    run()
