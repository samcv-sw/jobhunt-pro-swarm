"""
Fingerprint Rotator — IMP-201
Provides randomized browser fingerprints (User-Agent, viewport, WebGL)
to reduce fingerprint consistency and avoid bot detection.
"""
import random
from typing import TypedDict


class BrowserFingerprint(TypedDict):
    """A complete randomized browser fingerprint."""
    user_agent: str
    viewport_width: int
    viewport_height: int
    webgl_renderer: str
    webgl_vendor: str
    platform: str
    language: str


# 20+ real-world User-Agent strings (Chrome, Firefox, Safari, Edge)
_USER_AGENTS: list[str] = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Firefox on Linux
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    # Chrome on Android
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.82 Mobile Safari/537.36",
    # Safari on iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
    # Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 OPR/110.0.0.0",
    # Brave (same UA as Chrome, different header)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    # Vivaldi
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Vivaldi/6.7.3329.35",
]

# Common desktop resolutions
_VIEWPORTS: list[tuple[int, int]] = [
    (1280, 800),
    (1366, 768),
    (1440, 900),
    (1536, 864),
    (1600, 900),
    (1920, 1080),
    (2560, 1440),
    (1280, 1024),
    (1024, 768),
]

# WebGL renderer/vendor combinations
_WEBGL_RENDERERS: list[tuple[str, str]] = [
    ("ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)", "Google Inc. (Intel)"),
    ("ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)", "Google Inc. (Intel)"),
    ("ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)", "Google Inc. (NVIDIA)"),
    ("ANGLE (AMD, AMD Radeon RX 6600 Direct3D11 vs_5_0 ps_5_0)", "Google Inc. (AMD)"),
    ("Apple M2", "Apple"),
    ("Apple M1 Pro", "Apple"),
    ("Mesa Intel(R) UHD Graphics 620 (WHL GT2)", "Intel Open Source Technology Center"),
    ("NVIDIA GeForce GTX 1650/PCIe/SSE2", "NVIDIA Corporation"),
]

_PLATFORMS: list[str] = ["Win32", "MacIntel", "Linux x86_64", "iPhone"]
_LANGUAGES: list[str] = ["en-US", "en-GB", "ar-SA", "fr-FR", "de-DE", "es-ES"]


def get_random_fingerprint() -> BrowserFingerprint:
    """Return a randomized browser fingerprint for stealth scraping — IMP-201.

    Returns:
        A BrowserFingerprint dict with user_agent, viewport dimensions,
        WebGL renderer/vendor, platform, and language.
    """
    viewport = random.choice(_VIEWPORTS)
    webgl = random.choice(_WEBGL_RENDERERS)
    return BrowserFingerprint(
        user_agent=random.choice(_USER_AGENTS),
        viewport_width=viewport[0],
        viewport_height=viewport[1],
        webgl_renderer=webgl[0],
        webgl_vendor=webgl[1],
        platform=random.choice(_PLATFORMS),
        language=random.choice(_LANGUAGES),
    )


def get_random_user_agent() -> str:
    """Return a single random User-Agent string."""
    return random.choice(_USER_AGENTS)


def get_random_headers() -> dict[str, str]:
    """Return a complete set of realistic HTTP headers with a random fingerprint."""
    fp = get_random_fingerprint()
    return {
        "User-Agent": fp["user_agent"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": f"{fp['language']},en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    }
