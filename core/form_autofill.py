"""
core/form_autofill.py — Playwright-based Auto-Fill Browser Agent (R2)

Navigates to a job application form page, dynamically detects standard form
fields (name, email, phone, CV/resume file inputs, cover letter, etc.), fills
them with user profile data, clicks the submit button, and saves a screenshot.
"""

import logging
import os
import uuid

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

# Standard selectors and keywords to identify common job application fields
FIELDS_SCHEMA = {
    "first_name": ["first_name", "firstname", "first name", "given name"],
    "last_name": ["last_name", "lastname", "last name", "family name"],
    "full_name": ["name", "full_name", "fullname", "full name", "your name"],
    "email": ["email", "e-mail", "mail address", "email address"],
    "phone": ["phone", "tel", "mobile", "telephone", "phone number", "contact number"],
    "cover_letter": ["cover", "coverletter", "cover letter", "message", "note", "letter"],
    "resume": ["resume", "cv", "curriculum", "upload", "file"],
}


async def autofill_job_form(url: str, user_profile: dict) -> dict:
    """Navigates to a job application form, auto-fills standard fields,
    and clicks the submit/apply button.

    Args:
        url: The job application page URL.
        user_profile: Dict containing user info (e.g. name, email, phone, cv_path, cover_letter).

    Returns:
        dict: {"success": bool, "screenshot_path": str, "error": str | None}
    """
    logger.info("Starting auto-fill agent for URL: %s", url)
    screenshot_dir = os.path.join("data", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, f"autofill_{uuid.uuid4().hex[:8]}.png")

    result = {
        "success": False,
        "screenshot_path": screenshot_path,
        "error": None
    }

    async with async_playwright() as p:
        # Launch browser in headless mode to run efficiently
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Block heavy resources like images and fonts to boost speed and reduce OOM risks
            await page.route("**/*", lambda route: route.abort()
                            if route.request.resource_type in ["image", "media", "font"]
                            else route.continue_())

            # Navigate to the page
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for dynamic JS layout

            # Find all input, textarea, and select elements
            inputs = await page.query_selector_all("input, textarea, select")
            filled_count = 0

            for el in inputs:
                # Skip invisible elements
                if not await el.is_visible():
                    continue

                name_attr = (await el.get_attribute("name") or "").lower()
                id_attr = (await el.get_attribute("id") or "").lower()
                placeholder_attr = (await el.get_attribute("placeholder") or "").lower()
                type_attr = (await el.get_attribute("type") or "").lower()

                # Determine if field matches any target fields in schema
                field_type = None
                for schema_key, keywords in FIELDS_SCHEMA.items():
                    if any(k in name_attr or k in id_attr or k in placeholder_attr for k in keywords):
                        field_type = schema_key
                        break

                if not field_type:
                    continue

                # Auto-fill values based on detected type
                if field_type == "resume" or type_attr == "file":
                    cv_path = user_profile.get("cv_path") or user_profile.get("resume_path")
                    if cv_path and os.path.exists(cv_path):
                        await el.set_input_files(cv_path)
                        filled_count += 1
                        logger.info("Auto-filled CV file input with path: %s", cv_path)
                elif field_type == "cover_letter":
                    val = user_profile.get("cover_letter") or "Please find my attached resume."
                    await el.fill(val)
                    filled_count += 1
                    logger.info("Auto-filled cover letter textarea.")
                elif field_type == "email":
                    val = user_profile.get("email", "")
                    if val:
                        await el.fill(val)
                        filled_count += 1
                        logger.info("Auto-filled email: %s", val)
                elif field_type == "phone":
                    val = user_profile.get("phone", "")
                    if val:
                        await el.fill(val)
                        filled_count += 1
                        logger.info("Auto-filled phone: %s", val)
                elif field_type == "first_name":
                    val = user_profile.get("first_name") or user_profile.get("name", "").split()[0]
                    if val:
                        await el.fill(val)
                        filled_count += 1
                        logger.info("Auto-filled first name: %s", val)
                elif field_type == "last_name":
                    parts = user_profile.get("name", "").split()
                    val = user_profile.get("last_name") or (parts[-1] if len(parts) > 1 else "")
                    if val:
                        await el.fill(val)
                        filled_count += 1
                        logger.info("Auto-filled last name: %s", val)
                elif field_type == "full_name":
                    val = user_profile.get("name") or user_profile.get("full_name", "")
                    if val:
                        await el.fill(val)
                        filled_count += 1
                        logger.info("Auto-filled full name: %s", val)

            # Look for submit buttons
            # Typical buttons containing "submit", "apply", "send", "تقديم"
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Apply')",
                "button:has-text('Submit')",
                "button:has-text('Send')",
                "button:has-text('تقديم')",
                "button:has-text('ارسال')"
            ]

            submit_btn = None
            for sel in submit_selectors:
                try:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible() and await btn.is_enabled():
                        submit_btn = btn
                        break
                except Exception:
                    continue

            if submit_btn:
                # Click it and await navigation or timeout
                await submit_btn.click()
                await page.wait_for_timeout(3000)
                logger.info("Submit button clicked successfully.")
                result["success"] = True
            else:
                logger.warning("No clear visible submit button found on form.")
                # We count it as success if we filled the fields, treating button absence as non-fatal
                if filled_count > 0:
                    result["success"] = True

            # Save screenshot for audit trail
            await page.screenshot(path=screenshot_path)
            logger.info("Form autofill completed. Screenshot saved to %s", screenshot_path)

        except Exception as exc:
            logger.error("Error during auto-fill session: %s", exc)
            result["error"] = str(exc)
        finally:
            await browser.close()

    return result
