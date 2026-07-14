"""
JobHunt Pro v18 - Ultimate OS-Level Agent via Camoufox
Replaces Nodriver. Deeply hooks into browser engine to spoof TLS,
Canvas, Audio, WebGL, and automatically matches Timezone/Language to GeoIP.
"""

import asyncio
import logging
import random

logger = logging.getLogger(__name__)


class OSAgent:
    """
    Camoufox-based automation agent.
    Absolute stealth mode to bypass Cloudflare Turnstile and Datadome.
    """

    def __init__(self):
        self.browser = None
        self.page = None
        self.is_ready = False
        self._sticky_sessions = {}

    async def _check_dependencies(self):
        try:
            import camoufox  # noqa: F401
            from camoufox.async_api import AsyncCamoufox  # noqa: F401

            self.is_ready = True
        except ImportError as e:
            logger.warning(f"camoufox not installed. OS Agent unavailable. Error: {e}")

    async def start_browser(
        self,
        headless: bool = True,
        proxy: str | None = None,
        session_id: str | None = None,
    ):
        """Start the Camoufox browser instance."""
        await self._check_dependencies()
        if not self.is_ready:
            return None

        from camoufox.async_api import AsyncCamoufox

        args = {
            "headless": headless,
            "geoip": True,  # Automatically match timezone and language to proxy IP
            "allow_insecure": True,
            "enable_cache": True,
        }

        if proxy:
            args["proxy"] = proxy

        # Sticky Sessions for persistent logins across agent tasks
        if session_id:
            if session_id not in self._sticky_sessions:
                self._sticky_sessions[session_id] = await AsyncCamoufox(
                    **args
                ).__aenter__()
            self.browser = self._sticky_sessions[session_id]
        else:
            self.browser = await AsyncCamoufox(**args).__aenter__()

        self.page = await self.browser.new_page()
        logger.info(f"Camoufox OS Agent started. GeoIP matched: {proxy or 'Local'}")
        return self.page

    async def human_mouse_move(self, target_x: int, target_y: int):
        """Simulate a human-like mouse curve to the target."""
        if not self.is_ready or not self.page:
            return

        try:
            from core.human_mouse import HumanMouse

            start_x = random.randint(100, 300)
            start_y = random.randint(100, 300)
            await HumanMouse.simulate_mouse_movement(
                self.page, start_x, start_y, target_x, target_y
            )
        except Exception:
            # Fallback Playwright mouse move (Camoufox wraps Playwright)
            await self.page.mouse.move(target_x, target_y, steps=random.randint(5, 15))

    async def physical_click_element(self, selector: str):
        """Click element physically to trigger trusted events."""
        if not self.is_ready or not self.page:
            return

        try:
            element = await self.page.query_selector(selector)
            if not element:
                return

            box = await element.bounding_box()
            if not box:
                return

            center_x = box["x"] + box["width"] / 2 + random.randint(-2, 2)
            center_y = box["y"] + box["height"] / 2 + random.randint(-2, 2)

            await self.human_mouse_move(center_x, center_y)
            await self.page.mouse.click(
                center_x, center_y, delay=random.randint(50, 150)
            )
            logger.info(f"OS physical click completed on {selector}")
        except Exception as e:
            logger.error(f"physical_click_element failed: {e}")

    async def type_like_human(self, text: str):
        """Type text with human-like delays."""
        if not self.is_ready or not self.page:
            return

        for char in text:
            if random.random() < 0.02 and char.isalpha():
                wrong_char = chr(ord(char) + 1)
                await self.page.keyboard.type(wrong_char, delay=random.randint(50, 150))
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(random.uniform(0.1, 0.3))

            await self.page.keyboard.type(char, delay=random.randint(30, 150))

    async def close(self, session_id: str | None = None):
        if session_id and session_id in self._sticky_sessions:
            # Keep alive for sticky sessions unless explicitly closed globally
            pass
        elif self.browser:
            await self.browser.close()
            self.browser = None


os_cracker = OSAgent()
