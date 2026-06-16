"""
JobHunt Pro v13 - OS-Level Computer Use Agent
Bypasses ultra-strict ATS systems (Workday, Taleo) by physically taking control 
of the headless virtual display (Xvfb) and mimicking human mouse movements/clicks.
"""

import logging
import asyncio
import os
import random
import time

logger = logging.getLogger(__name__)

class OSAgent:
    """
    Combines Playwright DOM inspection with OS-level physical mouse interactions.
    Requires Xvfb running on DISPLAY=:99 (configured in Dockerfile).
    """
    def __init__(self):
        self.display = os.environ.get("DISPLAY", ":99")
        self.is_ready = False
        self._check_dependencies()

    def _check_dependencies(self):
        try:
            import pyautogui
            pyautogui.FAILSAFE = False
            self.is_ready = True
        except Exception as e:
            logger.warning(f"pyautogui init failed (likely no X11/DISPLAY). OS Agent running in degraded mode. Error: {e}")

    async def human_mouse_move(self, target_x: int, target_y: int):
        """Simulate a human-like mouse curve to the target."""
        if not self.is_ready:
            return
            
        import pyautogui
        current_x, current_y = pyautogui.position()
        
        # Calculate intermediate control points for a bezier-like curve
        steps = random.randint(15, 35)
        for i in range(steps):
            t = i / steps
            # Add jitter
            jitter_x = random.randint(-5, 5)
            jitter_y = random.randint(-5, 5)
            
            x = int(current_x + (target_x - current_x) * t) + jitter_x
            y = int(current_y + (target_y - current_y) * t) + jitter_y
            
            pyautogui.moveTo(x, y)
            await asyncio.sleep(random.uniform(0.01, 0.04))
            
        # Final precise move
        pyautogui.moveTo(target_x, target_y)

    async def physical_click_element(self, page, selector: str):
        """Find element via DOM, but click it using physical OS mouse."""
        if not self.is_ready:
            # Fallback to standard playwright click if no OS access
            await page.click(selector)
            return

        import pyautogui
        
        # Get bounding box of the element
        box = await page.locator(selector).bounding_box()
        if not box:
            logger.error(f"Cannot find element for OS physical click: {selector}")
            return
            
        # Calculate center with slight offset
        center_x = int(box["x"] + box["width"] / 2) + random.randint(-2, 2)
        center_y = int(box["y"] + box["height"] / 2) + random.randint(-2, 2)
        
        logger.info(f"OS Agent moving physical mouse to ({center_x}, {center_y})")
        await self.human_mouse_move(center_x, center_y)
        
        # Human click delay
        pyautogui.mouseDown()
        await asyncio.sleep(random.uniform(0.05, 0.15))
        pyautogui.mouseUp()
        
        logger.info(f"OS physical click completed on {selector}")

    async def type_like_human(self, text: str):
        """Physically type text with human-like delays and typos."""
        if not self.is_ready:
            return
            
        import pyautogui
        for char in text:
            # 2% chance of a typo and immediate backspace
            if random.random() < 0.02 and char.isalpha():
                wrong_char = chr(ord(char) + 1)
                pyautogui.write(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                pyautogui.press('backspace')
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
            pyautogui.write(char)
            await asyncio.sleep(random.uniform(0.03, 0.15))

    async def crack_workday_login(self, page, username: str, password: str):
        """Execute a full physical Workday login bypass."""
        logger.info("Initiating OS-Level ATS Cracker for Workday...")
        
        # Wait for inputs to render
        await page.wait_for_selector("input[type='text']")
        
        # Physical click on username
        await self.physical_click_element(page, "input[type='text']")
        await self.type_like_human(username)
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Physical click on password
        await self.physical_click_element(page, "input[type='password']")
        await self.type_like_human(password)
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Physical submit
        await self.physical_click_element(page, "div[data-automation-id='click_filter']")
        logger.info("OS-Level ATS bypass complete.")

os_cracker = OSAgent()
