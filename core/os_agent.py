"""
JobHunt Pro v17 - OS-Level Agent via CDP (Nodriver)
Replaces legacy Playwright/pyautogui with native Nodriver automation for
undetectable, headless, proxy-aware interactions. Uses bezier curves for mouse movements.
"""

import logging
import asyncio
import random
from typing import Optional

logger = logging.getLogger(__name__)

class OSAgent:
    """
    CDP-based automation agent using Nodriver.
    Bypasses ultra-strict ATS systems and Cloudflare natively.
    """
    def __init__(self):
        self.browser = None
        self.is_ready = False

    async def _check_dependencies(self):
        try:
            import nodriver
            self.is_ready = True
        except ImportError as e:
            logger.warning(f"nodriver not installed. OS Agent unavailable. Error: {e}")

    async def start_browser(self, headless: bool = True, proxy: Optional[str] = None):
        """Start the nodriver browser instance."""
        await self._check_dependencies()
        if not self.is_ready:
            return None

        import nodriver
        
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
        
        if proxy:
            # Add proxy support as per Phase 2 requirements
            browser_args.append(f'--proxy-server={proxy}')
            logger.info(f"OS Agent starting with proxy: {proxy}")

        self.browser = await nodriver.start(
            headless=headless,
            browser_args=browser_args
        )
        return self.browser

    async def human_mouse_move(self, page, target_x: int, target_y: int):
        """Simulate a human-like mouse curve to the target using core.human_mouse."""
        if not self.is_ready or not self.browser:
            return

        try:
            from core.human_mouse import HumanMouse
            
            # Start from a random position near the top-left if we don't have current mouse coords
            start_x = random.randint(100, 300)
            start_y = random.randint(100, 300)
            
            await HumanMouse.simulate_mouse_movement(page, start_x, start_y, target_x, target_y)
        except Exception as e:
            logger.error(f"human_mouse_move failed: {e}")
            # Fallback direct CDP move
            try:
                await page.send(nodriver.cdp.input_.dispatch_mouse_event(
                    type_="mouseMoved",
                    x=target_x,
                    y=target_y
                ))
            except Exception:
                pass

    async def physical_click_element(self, page, selector: str):
        """Find element via DOM, but click it using physical CDP mouse events."""
        if not self.is_ready or not self.browser:
            return

        import nodriver
        
        try:
            element = await page.select(selector)
            if not element:
                logger.error(f"Cannot find element for OS physical click: {selector}")
                return
                
            # Get center coordinates
            rect = element.tree_node.box_model.content
            if not rect or len(rect) < 8:
                return
                
            center_x = int((rect[0] + rect[4]) / 2) + random.randint(-2, 2)
            center_y = int((rect[1] + rect[5]) / 2) + random.randint(-2, 2)
            
            logger.info(f"OS Agent moving CDP mouse to ({center_x}, {center_y})")
            await self.human_mouse_move(page, center_x, center_y)
            
            # Human click delay
            await page.send(nodriver.cdp.input_.dispatch_mouse_event(
                type_="mousePressed",
                x=center_x,
                y=center_y,
                button="left",
                click_count=1
            ))
            await asyncio.sleep(random.uniform(0.05, 0.15))
            await page.send(nodriver.cdp.input_.dispatch_mouse_event(
                type_="mouseReleased",
                x=center_x,
                y=center_y,
                button="left",
                click_count=1
            ))
            
            logger.info(f"OS CDP click completed on {selector}")
        except Exception as e:
            logger.error(f"physical_click_element failed: {e}")

    async def type_like_human(self, page, text: str):
        """Type text with human-like delays via CDP."""
        if not self.is_ready or not self.browser:
            return
            
        import nodriver

        for char in text:
            # 2% chance of a typo and immediate backspace
            if random.random() < 0.02 and char.isalpha():
                wrong_char = chr(ord(char) + 1)
                await page.send(nodriver.cdp.input_.dispatch_key_event(
                    type_="char", text=wrong_char
                ))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.send(nodriver.cdp.input_.dispatch_key_event(
                    type_="keyDown", windows_virtual_key_code=8 # Backspace
                ))
                await page.send(nodriver.cdp.input_.dispatch_key_event(
                    type_="keyUp", windows_virtual_key_code=8
                ))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
            await page.send(nodriver.cdp.input_.dispatch_key_event(
                type_="char", text=char
            ))
            await asyncio.sleep(random.uniform(0.03, 0.15))

    async def crack_workday_login(self, page, username: str, password: str):
        """Execute a full CDP Workday login bypass."""
        logger.info("Initiating Nodriver ATS Cracker for Workday...")
        
        try:
            # Physical click on username
            await self.physical_click_element(page, "input[type='text']")
            await self.type_like_human(page, username)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Physical click on password
            await self.physical_click_element(page, "input[type='password']")
            await self.type_like_human(page, password)
            
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Physical submit
            await self.physical_click_element(page, "div[data-automation-id='click_filter']")
            logger.info("Nodriver ATS bypass complete.")
        except Exception as e:
            logger.error(f"crack_workday_login failed: {e}")

    async def close(self):
        if self.browser:
            self.browser.stop()
            self.browser = None

os_cracker = OSAgent()
