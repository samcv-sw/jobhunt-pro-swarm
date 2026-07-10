"""
Human Mouse Emulation (Tier 3 Stealth)
Generates non-linear, human-like mouse trajectories using Bezier curves and easing functions
to bypass Datadome and Cloudflare behavioral tracking.
"""

import logging
import math
import random
from typing import Any

logger = logging.getLogger(__name__)


class HumanMouse:
    @staticmethod
    def _bezier_curve(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
        """Cubic Bezier curve equation."""
        return (
            (1 - t) ** 3 * p0
            + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t**2 * p2
            + t**3 * p3
        )

    @staticmethod
    def generate_path(
        start_x: int, start_y: int, dest_x: int, dest_y: int, num_points: int = 20
    ) -> list[tuple[int, int]]:
        """
        Generate a human-like path from start to destination using a cubic Bezier curve.
        Adds random control points to create realistic "wobble" and overshoot.
        """
        path = []

        # Control points for the Bezier curve
        # Randomize control points to create an arc rather than a straight line
        offset_x = random.randint(-100, 100)
        offset_y = random.randint(-100, 100)

        p0_x, p0_y = start_x, start_y
        p3_x, p3_y = dest_x, dest_y

        # Intermediate control points
        p1_x = start_x + (dest_x - start_x) * random.uniform(0.1, 0.4) + offset_x
        p1_y = start_y + (dest_y - start_y) * random.uniform(0.1, 0.4) + offset_y

        p2_x = start_x + (dest_x - start_x) * random.uniform(0.6, 0.9) - offset_x
        p2_y = start_y + (dest_y - start_y) * random.uniform(0.6, 0.9) - offset_y

        for i in range(num_points):
            t = i / (num_points - 1)

            # Apply an easing function to make movement start slow, speed up, then slow down
            # EaseInOutCubic
            if t < 0.5:
                eased_t = 4 * t * t * t
            else:
                p = 2 * t - 2
                eased_t = 0.5 * p * p * p + 1

            x = int(HumanMouse._bezier_curve(eased_t, p0_x, p1_x, p2_x, p3_x))
            y = int(HumanMouse._bezier_curve(eased_t, p0_y, p1_y, p2_y, p3_y))

            # Add microscopic jitter
            if i > 0 and i < num_points - 1:
                x += random.randint(-1, 1)
                y += random.randint(-1, 1)

            path.append((x, y))

        return path

    @staticmethod
    async def simulate_mouse_movement(
        page: Any, start_x: int, start_y: int, dest_x: int, dest_y: int
    ) -> None:
        """
        Simulate human mouse movement on a browser page (e.g., nodriver or playwright).
        """
        # Calculate distance to determine number of points
        distance = math.hypot(dest_x - start_x, dest_y - start_y)
        num_points = max(10, int(distance / 15))  # More points for longer distances

        logger.info(
            f"Simulating mouse path from ({start_x}, {start_y}) to ({dest_x}, {dest_y}) in {num_points} points."
        )
        path = HumanMouse.generate_path(start_x, start_y, dest_x, dest_y, num_points)

        import asyncio

        for x, y in path:
            # Dispatch native mouse move event (Playwright/Nodriver compatible format)
            try:
                await page.mouse.move(x, y)
            except AttributeError:
                pass  # If the page object doesn't support raw mouse move, skip

            # Random delay between movements (1ms to 5ms)
            await asyncio.sleep(random.uniform(0.001, 0.005))

        # Final micro-pause before clicking
        await asyncio.sleep(random.uniform(0.05, 0.15))
