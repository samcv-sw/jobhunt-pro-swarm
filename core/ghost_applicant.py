import logging
import asyncio
from typing import Dict, Optional
from core.stealth import stealth

logger = logging.getLogger(__name__)

class GhostApplicant:
    """
    The Ghost Applicant Engine.
    Uses Playwright to automatically fill and submit job applications
    on Greenhouse, Lever, and Workable portals, bypassing email entirely.
    """
    
    def __init__(self):
        try:
            from playwright.async_api import async_playwright
            self.playwright_available = True
        except ImportError:
            self.playwright_available = False
            logger.error("Playwright not installed. Ghost Applicant disabled.")
            
    async def apply_to_url(self, url: str, profile: Dict, cv_path: str) -> bool:
        """Navigate to URL, detect the portal type, and auto-fill."""
        if not self.playwright_available:
            logger.error("Cannot run Ghost Applicant without Playwright.")
            return False
            
        logger.info(f"[GHOST] Starting silent application injection for {url}")
        
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=stealth.get_random_user_agent(),
                    extra_http_headers=stealth.bypass_cloudflare()
                )
                
                # [RUSSIAN STEALTH] Inject Canvas and WebGL spoofing before page loads
                await context.add_init_script(stealth.get_canvas_spoofing_script())
                await context.add_init_script(stealth.get_webgl_spoofing_script())
                
                page = await context.new_page()
                
                # Setup timeout and navigate
                page.set_default_timeout(30000)
                await page.goto(url, wait_until="networkidle")
                
                # Detect ATS type
                content = await page.content()
                if "greenhouse.io" in url or "application_form" in content.lower():
                    logger.info("[GHOST] Detected Greenhouse portal.")
                    success = await self._fill_greenhouse(page, profile, cv_path)
                elif "jobs.lever.co" in url or "application-page" in content.lower():
                    logger.info("[GHOST] Detected Lever portal.")
                    success = await self._fill_lever(page, profile, cv_path)
                else:
                    logger.info("[GHOST] Generic/Unknown portal. Attempting universal fallback fill.")
                    success = await self._fill_generic(page, profile, cv_path)
                    
                await browser.close()
                return success
                
        except Exception as e:
            logger.error(f"[GHOST] Application failed: {e}")
            return False

    async def _fill_greenhouse(self, page, profile: Dict, cv_path: str) -> bool:
        """Fill a Greenhouse application form."""
        try:
            # First Name
            if await page.locator("input[name='job_application[first_name]']").count() > 0:
                await page.fill("input[name='job_application[first_name]']", profile.get("name", "").split(" ")[0])
            
            # Last Name
            if await page.locator("input[name='job_application[last_name]']").count() > 0:
                name_parts = profile.get("name", "").split(" ")
                last_name = name_parts[-1] if len(name_parts) > 1 else ""
                await page.fill("input[name='job_application[last_name]']", last_name)
                
            # Email
            if await page.locator("input[name='job_application[email]']").count() > 0:
                await page.fill("input[name='job_application[email]']", profile.get("email", ""))
                
            # Phone
            if await page.locator("input[name='job_application[phone]']").count() > 0:
                await page.fill("input[name='job_application[phone]']", profile.get("phone", ""))
                
            # Upload CV
            if await page.locator("input[type='file']").count() > 0:
                await page.set_input_files("input[type='file']", cv_path)
                
            # Submit application form
            from playwright.async_api import expect
            submit_btn = page.locator("input[type='submit'], button[type='submit'], button[id='submit_app'], button:has-text('Submit')")
            if await submit_btn.count() > 0:
                await submit_btn.first.click()
                logger.info("[GHOST] Greenhouse form submitted!")
            else:
                logger.warning("[GHOST] Greenhouse: No submit button found")
            
            await page.wait_for_timeout(3000)
            return True
        except Exception as e:
            logger.error(f"Greenhouse fill error: {e}")
            return False

    async def _fill_lever(self, page, profile: Dict, cv_path: str) -> bool:
        """Fill a Lever application form."""
        try:
            await page.fill("input[name='name']", profile.get("name", ""))
            await page.fill("input[name='email']", profile.get("email", ""))
            await page.fill("input[name='phone']", profile.get("phone", ""))
            
            if await page.locator("input[type='file']").count() > 0:
                await page.set_input_files("input[type='file']", cv_path)
            
            # Submit application form
            submit_btn = page.locator("input[type='submit'], button[type='submit']:not([aria-label='Close']), button:has-text('Submit')")
            if await submit_btn.count() > 0:
                await submit_btn.first.click()
                await page.wait_for_timeout(2000)
                logger.info("[GHOST] Lever form submitted!")
            else:
                logger.warning("[GHOST] Lever: No submit button found")
            
            logger.info("[GHOST] Lever form successfully populated and submitted.")
            return True
        except Exception as e:
            logger.error(f"Lever fill error: {e}")
            return False

    async def _fill_generic(self, page, profile: Dict, cv_path: str) -> bool:
        """Fallback generic form filler for unknown ATS."""
        try:
            # Try generic CSS selectors
            inputs = {"name": profile.get("name"), "email": profile.get("email"), "phone": profile.get("phone")}
            for key, val in inputs.items():
                if not val: continue
                locators = [f"input[name*='{key}' i]", f"input[id*='{key}' i]", f"input[placeholder*='{key}' i]"]
                for loc in locators:
                    if await page.locator(loc).count() > 0:
                        await page.fill(loc, val)
                        break
            
            if await page.locator("input[type='file']").count() > 0:
                await page.set_input_files("input[type='file']", cv_path)
            
            # Submit application form
            submit_btn = page.locator("input[type='submit'], button[type='submit'], button:has-text('Send'), button:has-text('Apply'), button:has-text('Submit')")
            if await submit_btn.count() > 0:
                await submit_btn.first.click()
                await page.wait_for_timeout(2000)
                logger.info("[GHOST] Generic form submitted!")
            else:
                logger.warning("[GHOST] Generic: No submit button found")
            
            logger.info("[GHOST] Generic form successfully populated and submitted.")
            return True
        except Exception as e:
            logger.error(f"Generic fill error: {e}")
            return False
