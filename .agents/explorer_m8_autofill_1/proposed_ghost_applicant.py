import asyncio
import logging
import random
import re
from typing import Any, Dict, List, Optional

from core.stealth import stealth

logger = logging.getLogger(__name__)

# Fuzzy matching patterns for common job application fields
FIELD_PATTERNS = {
    "first_name": [r"first\s*name", r"given\s*name", r"fname", r"forename"],
    "last_name": [r"last\s*name", r"family\s*name", r"lname", r"surname"],
    "full_name": [r"^name$", r"full\s*name", r"candidate\s*name", r"your\s*name"],
    "email": [r"email", r"e-mail"],
    "phone": [r"phone", r"mobile", r"telephone", r"contact", r"cell"],
    "linkedin": [r"linkedin", r"li\.com"],
    "github": [r"github", r"git"],
    "portfolio": [r"portfolio", r"website", r"personal\s*site", r"homepage"],
    "location": [r"location", r"city", r"address", r"reside"],
    "salary": [r"salary", r"compensation", r"expectations", r"pay"],
    "notice_period": [r"notice\s*period", r"availability", r"start\s*date"],
}

class GhostApplicantEnhanced:
    """
    Enhanced Ghost Applicant Engine.
    Uses Playwright with advanced fuzzy locating, accessibility tree crawling,
    iframe traversal, custom select/radio handling, and human emulation.
    """

    def __init__(self):
        try:
            from playwright.async_api import async_playwright
            self.playwright_available = True
        except ImportError:
            self.playwright_available = False
            logger.error("Playwright not installed.")

    async def apply_to_url(self, url: str, profile: dict, cv_path: str) -> bool:
        if not self.playwright_available:
            logger.error("Cannot run Ghost Applicant without Playwright.")
            return False

        logger.info(f"[GHOST] Navigating to job post: {url}")
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=stealth.get_random_user_agent(),
                    extra_http_headers=stealth.bypass_cloudflare(),
                )

                # Inject Russian Stealth canvas/webgl protections
                await context.add_init_script(stealth.get_canvas_spoofing_script())
                await context.add_init_script(stealth.get_webgl_spoofing_script())

                page = await context.new_page()
                page.set_default_timeout(45000)

                await page.goto(url, wait_until="domcontentloaded")
                # Extra wait for dynamic frameworks (React, Angular, Vue, etc.)
                await page.wait_for_timeout(3000)

                # Detect ATS portal type and process
                content = await page.content()
                if "greenhouse.io" in url or "application_form" in content.lower():
                    logger.info("[GHOST] Processing Greenhouse portal.")
                    success = await self._fill_greenhouse(page, profile, cv_path)
                elif "jobs.lever.co" in url or "application-page" in content.lower():
                    logger.info("[GHOST] Processing Lever portal.")
                    success = await self._fill_lever(page, profile, cv_path)
                else:
                    logger.info("[GHOST] Applying Advanced Universal Autofill.")
                    success = await self._fill_universal(page, profile, cv_path)

                await browser.close()
                return success

        except Exception as e:
            logger.error(f"[GHOST] Enhanced Application failed: {e}")
            return False

    async def _fill_greenhouse(self, page, profile: dict, cv_path: str) -> bool:
        """Greenhouse specific autofill using semantic locators."""
        try:
            # Match fields using a combination of name attributes and labels
            # First Name
            first_name = profile.get("name", "").split(" ")[0]
            await self._fill_field(page, "input[name='job_application[first_name]']", first_name)
            
            # Last Name
            name_parts = profile.get("name", "").split(" ")
            last_name = name_parts[-1] if len(name_parts) > 1 else name_parts[0]
            await self._fill_field(page, "input[name='job_application[last_name]']", last_name)

            # Email
            await self._fill_field(page, "input[name='job_application[email]']", profile.get("email", ""))
            
            # Phone
            await self._fill_field(page, "input[name='job_application[phone]']", profile.get("phone", ""))

            # Handle file upload
            await self._upload_file(page, "input[type='file']", cv_path)

            # LinkedIn / Portfolios
            await self._fill_field(page, "input[name*='linkedin' i]", profile.get("linkedin", ""))
            await self._fill_field(page, "input[name*='website' i], input[name*='portfolio' i]", profile.get("portfolio", ""))

            # Handle custom select boxes or dynamic questions
            await self._answer_greenhouse_custom_questions(page, profile)

            # Submit
            return await self._click_submit(page)
        except Exception as e:
            logger.error(f"Greenhouse enhanced fill error: {e}")
            return False

    async def _fill_lever(self, page, profile: dict, cv_path: str) -> bool:
        """Lever specific autofill using semantic locators."""
        try:
            await self._fill_field(page, "input[name='name']", profile.get("name", ""))
            await self._fill_field(page, "input[name='email']", profile.get("email", ""))
            await self._fill_field(page, "input[name='phone']", profile.get("phone", ""))
            
            # Upload CV
            await self._upload_file(page, "input[type='file']", cv_path)

            # Social links
            await self._fill_field(page, "input[name*='urls[LinkedIn]' i]", profile.get("linkedin", ""))
            await self._fill_field(page, "input[name*='urls[GitHub]' i]", profile.get("github", ""))
            await self._fill_field(page, "input[name*='urls[Portfolio]' i]", profile.get("portfolio", ""))

            # Submit
            return await self._click_submit(page)
        except Exception as e:
            logger.error(f"Lever enhanced fill error: {e}")
            return False

    async def _fill_universal(self, page, profile: dict, cv_path: str) -> bool:
        """
        Advanced Universal Autofill Engine.
        Traverses all elements, parses labels, accesses subframes,
        and uses fuzzy/pattern heuristics to identify inputs.
        """
        try:
            # Step 1: Collect all frames (since forms are often in iframes)
            all_frames = [page] + page.frames
            logger.info(f"[GHOST] Scanned page and found {len(page.frames)} sub-frames.")

            for frame in all_frames:
                # 1. Look for and upload CV/Resume first, as ATS forms often parse text from it
                file_inputs = await frame.locator("input[type='file']").all()
                if file_inputs:
                    for fi in file_inputs:
                        # Upload to the first or relevant file input
                        try:
                            await fi.set_input_files(cv_path)
                            logger.info(f"[GHOST] Uploaded CV to frame element: {fi}")
                            await asyncio.sleep(2.0)  # Wait for parse
                            break
                        except Exception as file_err:
                            logger.debug(f"Failed to upload CV to file input: {file_err}")

                # 2. Iterate and match standard text/tel/email fields
                inputs = await frame.locator("input:not([type='submit']):not([type='button']):not([type='hidden']), textarea").all()
                for inp in inputs:
                    if not await inp.is_visible():
                        continue

                    # Extract attributes
                    name_attr = (await inp.get_attribute("name") or "").lower()
                    id_attr = (await inp.get_attribute("id") or "").lower()
                    placeholder_attr = (await inp.get_attribute("placeholder") or "").lower()
                    aria_label = (await inp.get_attribute("aria-label") or "").lower()

                    # Find nearby label text
                    label_text = ""
                    if id_attr:
                        label_elem = frame.locator(f"label[for='{id_attr}']").first
                        if await label_elem.count() > 0:
                            label_text = (await label_elem.inner_text() or "").lower()

                    # Try parent element inner text as fallback for label
                    if not label_text:
                        parent = inp.locator("xpath=..")
                        if await parent.count() > 0:
                            label_text = (await parent.inner_text() or "").lower()

                    # Combine identification markers
                    markers = f"{name_attr} {id_attr} {placeholder_attr} {aria_label} {label_text}"

                    # Match markers with profile values
                    for field, patterns in FIELD_PATTERNS.items():
                        is_match = False
                        for pattern in patterns:
                            if re.search(pattern, markers):
                                is_match = True
                                break

                        if is_match:
                            # Select input type and value
                            value = self._get_profile_value(profile, field)
                            if value:
                                # Check if it's already filled
                                current_val = await inp.input_value()
                                if not current_val:
                                    logger.info(f"[GHOST] Fuzzy match found! Field: '{field}', Markers: '{markers[:50]}'")
                                    await self._type_humanlike(inp, str(value))
                                    await asyncio.sleep(random.uniform(0.3, 0.8))
                            break

                # 3. Handle custom dropdowns (Selects)
                selects = await frame.locator("select").all()
                for sel in selects:
                    # Parse labels for selects
                    id_attr = (await sel.get_attribute("id") or "").lower()
                    name_attr = (await sel.get_attribute("name") or "").lower()
                    label_text = ""
                    if id_attr:
                        label_elem = frame.locator(f"label[for='{id_attr}']").first
                        if await label_elem.count() > 0:
                            label_text = (await label_elem.inner_text() or "").lower()

                    combined_sel = f"{name_attr} {id_attr} {label_text}"

                    # Handle common dropdowns like visa sponsorship / work authorization
                    if "sponsor" in combined_sel or "work authorization" in combined_sel or "authorized" in combined_sel:
                        # Default answer: usually "no" to sponsorship request or "yes" to authorized to work
                        options = await sel.locator("option").all()
                        for opt in options:
                            val = await opt.get_attribute("value") or ""
                            txt = (await opt.inner_text() or "").lower()
                            if "sponsor" in combined_sel and ("no" in txt or "no" in val.lower()):
                                await sel.select_option(value=val)
                                break
                            elif "authorized" in combined_sel and ("yes" in txt or "yes" in val.lower()):
                                await sel.select_option(value=val)
                                break

            # Submit form
            return await self._click_submit(page)

        except Exception as e:
            logger.error(f"Universal enhanced fill error: {e}")
            return False

    async def _answer_greenhouse_custom_questions(self, page, profile: dict):
        """Specifically handles custom/conditional Greenhouse fields like visa, address, etc."""
        try:
            # Custom questions on Greenhouse are usually inside div.jobs-custom-question
            questions = await page.locator("div.jobs-custom-question-class, div.jobs-custom-question").all()
            for q in questions:
                text = (await q.inner_text() or "").lower()
                
                # Check for visa sponsorship question
                if "sponsor" in text or "visa" in text:
                    # Select "No" (standard default or based on config)
                    no_radio = q.locator("input[type='radio'][value*='no' i], input[type='radio'][value='0'], label:has-text('No') input")
                    if await no_radio.count() > 0:
                        await no_radio.first.click()
                        logger.info("[GHOST] Answered Visa Sponsorship -> No")

                # Check for authorized to work in US/country
                elif "authorized" in text or "legally" in text:
                    # Select "Yes"
                    yes_radio = q.locator("input[type='radio'][value*='yes' i], input[type='radio'][value='1'], label:has-text('Yes') input")
                    if await yes_radio.count() > 0:
                        await yes_radio.first.click()
                        logger.info("[GHOST] Answered Authorized to Work -> Yes")
        except Exception as e:
            logger.debug(f"Error filling custom Greenhouse questions: {e}")

    def _get_profile_value(self, profile: dict, field: str) -> Optional[Any]:
        """Resolves field name to profile value."""
        if field == "first_name":
            return profile.get("name", "").split(" ")[0]
        elif field == "last_name":
            name_parts = profile.get("name", "").split(" ")
            return name_parts[-1] if len(name_parts) > 1 else name_parts[0]
        elif field == "full_name":
            return profile.get("name")
        elif field == "salary":
            return profile.get("salary_expectation") or profile.get("salary")
        return profile.get(field)

    async def _fill_field(self, page_or_frame, selector: str, value: str):
        """Helper to fill a field if it exists with human-like delay."""
        if not value:
            return
        loc = page_or_frame.locator(selector)
        if await loc.count() > 0:
            await loc.first.scroll_into_view_if_needed()
            await self._type_humanlike(loc.first, value)

    async def _upload_file(self, page_or_frame, selector: str, file_path: str):
        """Uploads file using Playwright set_input_files."""
        loc = page_or_frame.locator(selector)
        if await loc.count() > 0:
            await loc.first.scroll_into_view_if_needed()
            await loc.first.set_input_files(file_path)
            logger.info(f"[GHOST] Uploaded file to: {selector}")

    async def _type_humanlike(self, locator, text: str):
        """Types string character-by-character to trigger JS keypress listeners."""
        await locator.focus()
        await locator.clear()
        for char in text:
            await locator.press(char)
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def _click_submit(self, page) -> bool:
        """Finds and clicks the submit button, mimicking human hovering first."""
        submit_btn = page.locator(
            "input[type='submit'], button[type='submit'], "
            "button:has-text('Submit Application'), button:has-text('Submit'), button:has-text('Apply')"
        )
        if await submit_btn.count() > 0:
            btn = submit_btn.first
            await btn.scroll_into_view_if_needed()
            
            # Hover before click to trigger mousemove event listeners
            box = await btn.bounding_box()
            if box:
                # Move mouse to button center
                await page.mouse.move(box["x"] + box["width"]/2, box["y"] + box["height"]/2, steps=10)
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Click
            await btn.click()
            logger.info("[GHOST] Clicked Submit button.")
            await page.wait_for_timeout(5000)  # Wait for submission redirect/API response
            return True
        else:
            logger.warning("[GHOST] Submit button not found")
            return False
