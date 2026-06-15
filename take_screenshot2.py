from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        print("Registering...")
        page.goto('https://jhfguf.pythonanywhere.com/register')
        page.fill('input[name="name"]', 'Test Agent')
        page.fill('input[name="email"]', 'agenttest@samde.com')
        page.fill('input[name="password"]', 'password123')
        page.click('button[type="submit"]')
        time.sleep(3)
        print("Navigating to dashboard...")
        page.goto('https://jhfguf.pythonanywhere.com/user-dashboard')
        time.sleep(2)
        print("Taking screenshot...")
        page.screenshot(path='c:\\Users\\samde\\Desktop\\cv sam new ma3 kimi\\dashboard_full.png', full_page=True)
        browser.close()

if __name__ == '__main__':
    run()
