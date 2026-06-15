from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        print("Navigating to login...")
        page.goto("https://jhfguf.pythonanywhere.com/login")
        
        # We need to register a user or use an existing one to login.
        # But wait, there is no register page right now? Oh, there is one, or we can use the test_ai_agent@samde.com ?
        # Actually I don't know the password on pythonanywhere.
        # Let's just create a new user!
        page.goto("https://jhfguf.pythonanywhere.com/register")
        time.sleep(2)
        try:
            page.fill('input[name="email"]', 'test_fara8@samde.com')
            page.fill('input[name="password"]', 'password123')
            page.click('button[type="submit"]')
            print("Registered/Logged in")
            time.sleep(2)
        except Exception as e:
            print("Registration failed, trying login", e)
            page.goto("https://jhfguf.pythonanywhere.com/login")
            page.fill('input[name="email"]', 'test_fara8@samde.com')
            page.fill('input[name="password"]', 'password123')
            page.click('button[type="submit"]')
            time.sleep(2)
        
        print("Navigating to user dashboard...")
        page.goto("https://jhfguf.pythonanywhere.com/user-dashboard")
        time.sleep(3)
        page.screenshot(path="live_dashboard.png")
        print("Saved live_dashboard.png")
        
        print("Navigating to upload-cv...")
        page.goto("https://jhfguf.pythonanywhere.com/upload-cv")
        time.sleep(3)
        page.screenshot(path="live_upload_cv.png")
        print("Saved live_upload_cv.png")
        
        browser.close()

if __name__ == "__main__":
    run()
