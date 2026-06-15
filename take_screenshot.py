from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # Login
        page.goto('https://jhfguf.pythonanywhere.com/login')
        page.fill('input[name="email"]', 'samde')
        page.fill('input[name="password"]', 'password')
        page.click('button[type="submit"]')
        page.wait_for_url('https://jhfguf.pythonanywhere.com/user-dashboard')
        
        # Take screenshot of the dashboard
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.screenshot(path='dashboard_screenshot.png')
        browser.close()
        print("Screenshot saved to dashboard_screenshot.png")

if __name__ == '__main__':
    run()
