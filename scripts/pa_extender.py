import os
import pyotp
import time
from playwright.sync_api import sync_playwright

def extend_pythonanywhere():
    username = os.getenv("PA_USERNAME")
    password = os.getenv("PA_PASSWORD")
    totp_secret = os.getenv("PA_TOTP_SECRET")
    
    if not all([username, password, totp_secret]):
        logger.debug("❌ Error: Missing PA_USERNAME, PA_PASSWORD, or PA_TOTP_SECRET in environment variables.")
        return
        
    logger.debug(f"🔄 Starting auto-renewal process for PythonAnywhere user: {username}...")
    totp = pyotp.TOTP(totp_secret.replace(" ", ""))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Login Page
            logger.debug("🌐 Navigating to login page...")
            page.goto("https://www.pythonanywhere.com/login/")
            page.fill("input[name='id_auth-username']", username)
            page.fill("input[name='id_auth-password']", password)
            page.click("button[type='submit']")
            
            # 2. 2FA Page
            logger.debug("🔐 Submitting 2FA code...")
            page.wait_for_selector("input[name='id_token-otp_token']", timeout=10000)
            code = totp.now()
            page.fill("input[name='id_token-otp_token']", code)
            page.click("button[type='submit']")
            
            # 3. Webapps Dashboard
            logger.debug("🖥️ Navigating to Webapps dashboard...")
            page.wait_for_selector(f"a[href='/user/{username}/webapps/']", timeout=10000)
            page.goto(f"https://www.pythonanywhere.com/user/{username}/webapps/")
            
            # 4. Click Extend Button
            logger.debug("⏳ Looking for the extend button...")
            try:
                # The button usually says 'Run until 3 months from today' for paid, or 'Run until 3 months...' etc.
                # For free tier, it says 'Run until 3 months from today'
                extend_btn = page.query_selector("input[value^='Run until']")
                if extend_btn:
                    extend_btn.click()
                    logger.debug("✅ Successfully clicked the extend button! Your server will not sleep.")
                else:
                    extend_btn_alt = page.query_selector("button:has-text('Run until')")
                    if extend_btn_alt:
                        extend_btn_alt.click()
                        logger.debug("✅ Successfully clicked the extend button! Your server will not sleep.")
                    else:
                        logger.debug("⚠️ Could not find the extend button. It might already be extended to the maximum allowed date.")
            except Exception as e:
                logger.debug(f"⚠️ Button click error: {e}")
                
        except Exception as e:
            logger.debug(f"❌ Automation failed: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    extend_pythonanywhere()
