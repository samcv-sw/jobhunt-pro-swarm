"""
Bot Watchdog: PythonAnywhere Auto-Renewer (v2026)
This script logs into PythonAnywhere and clicks the "Run until 1 month from today" button.
It runs headlessly on GitHub Actions or a secondary cloud provider (like Zeabur or Fly).
"""

import asyncio
import os
import logging
from playwright.async_api import async_playwright
import pyotp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PA_Watchdog")

# Load credentials from environment
PA_USER = os.getenv("PA_USER", "JHFGUF")
PA_PASS = os.getenv("PA_PASS")
# TOTP Secret extracted from: otpauth://totp/www.pythonanywhere.com%3A%20JHFGUF?secret=4RQLUKK6XN62I4OH3DTXMORWVABDRZS6
PA_TOTP_SECRET = os.getenv("PA_TOTP_SECRET", "4RQLUKK6XN62I4OH3DTXMORWVABDRZS6")

async def renew_pythonanywhere():
    if not PA_PASS:
        logger.error("PythonAnywhere password (PA_PASS) not set in environment.")
        return

    logger.info(f"Starting auto-renewal for {PA_USER}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 1. Login Page
            await page.goto("https://www.pythonanywhere.com/login/")
            await page.fill("input[name='auth-username']", PA_USER)
            await page.fill("input[name='auth-password']", PA_PASS)
            await page.click("button[id='id_next']")
            await page.wait_for_load_state("networkidle")
            
            # 2. 2FA (TOTP) Page
            # Generate the current 6-digit code using the TOTP secret
            totp = pyotp.TOTP(PA_TOTP_SECRET)
            current_code = totp.now()
            logger.info(f"Generated 2FA Code: {current_code}")
            
            # Fill the 2FA code (adjust selector based on actual PA 2FA page)
            # Typically it's an input for the token.
            token_input = await page.query_selector("input[name='token']")
            if token_input:
                await token_input.fill(current_code)
                await page.click("button[type='submit']")
                await page.wait_for_load_state("networkidle")
            
            # 3. Navigate to Web Tab
            await page.goto(f"https://www.pythonanywhere.com/user/{PA_USER}/webapps/")
            await page.wait_for_load_state("networkidle")
            
            # 4. Click the Extend button
            # The button usually has class 'btn-primary' and text 'Run until 1 month from today'
            extend_button = await page.query_selector("input[value='Run until 1 month from today']")
            if extend_button:
                await extend_button.click()
                logger.info("Successfully clicked the 'Run until 1 month from today' button!")
            else:
                logger.warning("Extend button not found. It might not be time to renew yet, or the UI changed.")
                
        except Exception as e:
            logger.error(f"Auto-renewal failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(renew_pythonanywhere())
