"""
STEALTH SCRAPING TECHNIQUES
Ported from demo_user Project - Advanced anti-detection methods
"""

import asyncio
import hashlib
import inspect
import logging
import os
import random
import re
import time

import httpx
import requests

try:
    from curl_cffi import requests as cffi_requests

    HAS_CFFI = True
except ImportError:
    HAS_CFFI = False

logger = logging.getLogger(__name__)

PROXY_SOURCE_URL = os.getenv(
    "PROXY_SOURCE_URL",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=elite",
)


class StealthScraper:
    """Advanced scraping techniques to avoid detection with Ghost Proxy Support."""

    def __init__(self):
        self.request_count = 0
        self.last_request_time = 0
        self.user_agents = self._load_user_agents()
        self.fingerprints = self._generate_fingerprints()
        self.proxies = []
        self.last_proxy_fetch = 0
        self._proxy_fetch_in_progress = False
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self.fetch_proxies_async())
        except RuntimeError:
            pass

    async def fetch_proxies_async(self) -> None:
        """Fetch proxies asynchronously using httpx to prevent event-loop block."""
        if getattr(self, "_proxy_fetch_in_progress", False):
            return
        self._proxy_fetch_in_progress = True
        try:
            logger.info(
                "[GHOST PROXY] Async fetching fresh proxies from global network..."
            )
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(PROXY_SOURCE_URL)
                if res.status_code == 200:
                    proxies = [p.strip() for p in res.text.split("\n") if p.strip()]
                    if proxies:
                        self.proxies = proxies
                        self.last_proxy_fetch = time.time()
                        logger.info(
                            f"[GHOST PROXY] Async harvested {len(self.proxies)} elite stealth IPs."
                        )
        except Exception as e:
            logger.warning(f"[GHOST PROXY] Async proxy fetch failed: {e}")
        finally:
            self._proxy_fetch_in_progress = False

    def _fetch_free_proxies(self) -> list[str]:
        """[GHOST PROXY] Fetch 10,000+ free residential/datacenter proxies dynamically"""
        if time.time() - self.last_proxy_fetch < 3600 and self.proxies:
            return self.proxies

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                if not getattr(self, "_proxy_fetch_in_progress", False):
                    loop.create_task(self.fetch_proxies_async())
                return self.proxies
        except RuntimeError:
            pass

        try:
            logger.info(
                "[GHOST PROXY] Fetching fresh proxies from global network (synchronous fallback)..."
            )
            res = requests.get(PROXY_SOURCE_URL)
            if res.status_code == 200:
                self.proxies = [p.strip() for p in res.text.split("\n") if p.strip()]
                self.last_proxy_fetch = time.time()
                logger.info(
                    f"[GHOST PROXY] Successfully harvested {len(self.proxies)} elite stealth IPs (sync)."
                )
            return self.proxies
        except Exception as e:
            logger.warning(f"[GHOST PROXY] Failed to fetch proxies (sync): {e}")
            return []

    def get_random_proxy(self) -> str | None:
        proxies = self._fetch_free_proxies()
        if proxies:
            return f"http://{random.choice(proxies)}"
        return None

    def _load_user_agents(self) -> list[str]:
        """Real browser fingerprints from around the world + Googlebot"""
        return [
            # Chrome Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Safari Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            # Firefox Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
            # ====== MOBILE UAs (bypass desktop detection) ======
            # Mobile iPhone
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
            # Mobile Android
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 14; Samsung Galaxy S24) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.165 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.179 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 14; SM-S928B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Mobile Safari/537.36",
            # Mobile iPad
            "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
            # ====== GOOGLEBOT UAs (highest trust, 0% block) ======
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Googlebot/2.1; +http://www.google.com/bot.html) Chrome/125.0.6422.168 Safari/537.36",
            "Googlebot-Image/1.0",
            # ====== BINGBOT ======
            "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
            # ====== CHINESE SEARCH ENGINES (trusted by .lb sites) ======
            "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
            "Sogou web spider/4.0(+http://www.sogou.com/docs/help/webmaster.htm)",
        ]

    def _generate_fingerprints(self) -> list[dict]:
        """Complete browser profiles to avoid detection"""
        return [
            {
                "name": "chrome_windows",
                "platform": "Win32",
                "vendor": "Google Inc.",
                "languages": ["en-US", "en"],
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
            },
            {
                "name": "safari_mac",
                "platform": "MacIntel",
                "vendor": "Apple Computer, Inc.",
                "languages": ["en-US", "en"],
                "screen": {"width": 2560, "height": 1440, "colorDepth": 24},
            },
            {
                "name": "firefox_windows",
                "platform": "Win32",
                "vendor": "",
                "languages": ["en-US", "en"],
                "screen": {"width": 1920, "height": 1080, "colorDepth": 24},
            },
        ]

    def get_random_user_agent(self) -> str:
        """Get a random user agent"""
        return random.choice(self.user_agents)

    def get_mobile_user_agent(self) -> str:
        """Get only mobile user agents for 403 bypass"""
        mobile_agents = [
            ua
            for ua in self.user_agents
            if "Mobile" in ua or "iPhone" in ua or "iPad" in ua
        ]
        return (
            random.choice(mobile_agents)
            if mobile_agents
            else self.get_random_user_agent()
        )

    def get_googlebot_user_agent(self) -> str:
        """Get Googlebot user agent (highest trust)"""
        return random.choice(
            [
                ua
                for ua in self.user_agents
                if "Googlebot" in ua or "bingbot" in ua or "Baiduspider" in ua
            ]
            or self.user_agents
        )

    def get_random_fingerprint(self) -> dict:
        """Get a random browser fingerprint"""
        return random.choice(self.fingerprints)

    def get_headers(
        self, mobile: bool = False, googlebot: bool = False
    ) -> dict[str, str]:
        """Get realistic browser headers. Use mobile=True for 403 bypass."""
        fingerprint = self.get_random_fingerprint()
        ua = (
            self.get_googlebot_user_agent()
            if googlebot
            else (
                self.get_mobile_user_agent() if mobile else self.get_random_user_agent()
            )
        )

        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8"
            if not googlebot
            else "en-US,en;q=0.9",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        # Add platform-specific headers
        if fingerprint["platform"] == "MacIntel":
            headers["Sec-CH-UA-Platform"] = '"macOS"'
        else:
            headers["Sec-CH-UA-Platform"] = '"Windows"'

        return headers

    async def human_delay(self):
        """Add human-like delay between requests"""
        now = time.time()

        if self.last_request_time > 0:
            elapsed = now - self.last_request_time

            # Minimum 1 second between requests
            min_delay = 1.0
            if elapsed < min_delay:
                delay = min_delay - elapsed + random.uniform(0.1, 0.5)
                await asyncio.sleep(delay)

        self.last_request_time = time.time()
        self.request_count += 1

    # APEX MATRIX: Browser profile rotation to avoid static fingerprint detection
    # Rotate between latest Chrome, Safari, Edge profiles
    _BROWSER_PROFILES = [
        "chrome131",  # Chrome 131 (Windows) — most common desktop
        "chrome130",  # Chrome 130 (Windows) — second most common
        "chrome129",  # Chrome 129 (macOS)
        "safari18_0",  # Safari 18 (macOS) — avoid LinkedIn honeypots
        "edge99",  # Edge 99 (Windows)
    ]

    def _get_impersonation_profile(self) -> str:
        """
        Rotate browser fingerprints per request.
        Uses a seeded rotation (not fully random) so the same 'session'
        presents a consistent profile for cookie/session matching.
        """
        # Rotate every 10 requests to simulate a normal browsing session
        profile_index = (self.request_count // 10) % len(self._BROWSER_PROFILES)
        return self._BROWSER_PROFILES[profile_index]

    def should_rotate_ip(self) -> bool:
        """Decide if we should rotate IP (for proxy users)"""
        # Rotate every 50 requests
        return self.request_count % 50 == 0

    def get_request_fingerprint(self) -> str:
        """Generate unique fingerprint for this request"""
        data = f"{time.time()}{random.random()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def get_async_client(self, timeout: float = 30.0, follow_redirects: bool = True):
        """
        [NEW TIER 1 STEALTH] Returns an AsyncSession that natively spoofs TLS and HTTP/2.
        If curl_cffi is missing, it falls back to httpx (not recommended).
        """
        proxy = self.get_random_proxy()
        proxies = {"http": proxy, "https": proxy} if proxy else None

        if HAS_CFFI:
            # APEX MATRIX: Rotate browser impersonation profile
            # Each profile replicates a different browser's TLS + HTTP/2 + header fingerprint
            profile = self._get_impersonation_profile()
            logger.debug(f"[STEALTH] Using browser profile: {profile}")
            return cffi_requests.AsyncSession(
                impersonate=profile,
                timeout=timeout,
                proxies=proxies,
            )
        else:
            logger.warning(
                "[STEALTH] curl_cffi is missing! Falling back to raw httpx. Cloudflare may block you."
            )
            client_kwargs = {"timeout": timeout, "follow_redirects": follow_redirects}
            if proxy:
                sig = inspect.signature(httpx.AsyncClient.__init__)
                if "proxy" in sig.parameters:
                    client_kwargs["proxy"] = proxy
                else:
                    client_kwargs["proxies"] = proxy
            return httpx.AsyncClient(**client_kwargs)

    def get_sync_client(self, timeout: float = 30.0, follow_redirects: bool = True):
        """Synchronous version of Tier 1 stealth client."""
        proxy = self.get_random_proxy()
        proxies = {"http": proxy, "https": proxy} if proxy else None

        if HAS_CFFI:
            # APEX MATRIX: Rotate browser profile for sync client too
            profile = self._get_impersonation_profile()
            return cffi_requests.Session(
                impersonate=profile,
                timeout=timeout,
                proxies=proxies,
            )
        else:
            client_kwargs = {"timeout": timeout, "follow_redirects": follow_redirects}
            if proxy:
                sig = inspect.signature(httpx.Client.__init__)
                if "proxy" in sig.parameters:
                    client_kwargs["proxy"] = proxy
                else:
                    client_kwargs["proxies"] = proxy
            return httpx.Client(**client_kwargs)

    def get_canvas_spoofing_script(self) -> str:
        """[RUSSIAN STEALTH] Injectable JS to spoof Canvas fingerprint with non-deterministic subpixel noise"""
        return """
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {
            const context = originalGetContext.apply(this, arguments);
            if (type === '2d') {
                const originalGetImageData = context.getImageData;
                context.getImageData = function() {
                    const imageData = originalGetImageData.apply(this, arguments);
                    // Add subtle non-deterministic subpixel noise to bypass statistical XOR fingerprinting
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        const shift = Math.random() > 0.5 ? 1 : -1;
                        imageData.data[i] = Math.min(255, Math.max(0, imageData.data[i] + shift));
                    }
                    return imageData;
                };
            }
            return context;
        };
        """

    def get_webgl_spoofing_script(self) -> str:
        """[RUSSIAN STEALTH] Injectable JS to spoof WebGL vendor/renderer with matched GPU pairs"""
        gpu_pairs = [
            ("Google Inc. (Apple)", "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)"),
            ("Intel Inc.", "Intel(R) Iris(R) Xe Graphics"),
            ("NVIDIA Corporation", "NVIDIA GeForce RTX 4090"),
            ("ATI Technologies Inc.", "AMD Radeon Pro 5300M OpenGL Engine"),
        ]
        vendor, renderer = random.choice(gpu_pairs)
        return f"""
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{vendor}'; // UNMASKED_VENDOR_WEBGL
            if (parameter === 37446) return '{renderer}'; // UNMASKED_RENDERER_WEBGL
            return getParameter.apply(this, arguments);
        }};
        """

        # ═══════════════════════════════════════════════════════════════════════════

    # 403 RETRY WITH MOBILE/GOOGLEBOT UA (TIER 6 STEALTH)
    # ═══════════════════════════════════════════════════════════════════════════

    async def smart_fetch(self, url: str, timeout: float = 30.0) -> str | None:
        """
        Fetch URL with automatic 403 retry using mobile → Googlebot fallback.
        Strategy: Try desktop → mobile → Googlebot → Google Cache.
        """
        strategies = [
            ("desktop", False, False),
            ("mobile", True, False),
            ("googlebot", False, True),
        ]

        for name, mobile, googlebot in strategies:
            try:
                logger.info(f"[STEALTH] Trying {name} UA for {url}")
                resp = await self._fetch_with_headers(
                    url, mobile=mobile, googlebot=googlebot, timeout=timeout
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))

                if resp and len(resp) > 500:
                    logger.info(f"[STEALTH] {name} UA succeeded ({len(resp)} bytes)")
                    return resp
                elif resp:
                    logger.warning(
                        f"[STEALTH] {name} UA: response too short ({len(resp)} bytes), trying next"
                    )
            except Exception as e:
                logger.warning(f"[STEALTH] {name} UA failed: {e}")
                continue

        # Last resort: Google Cache
        logger.info(
            f"[STEALTH] All UA strategies failed, trying Google Cache for {url}"
        )
        return await self.fetch_google_cache(url, timeout)

    async def _fetch_with_headers(
        self,
        url: str,
        mobile: bool = False,
        googlebot: bool = False,
        timeout: float = 30.0,
    ) -> str | None:
        """Internal fetch with specific UA profile."""
        headers = self.get_headers(mobile=mobile, googlebot=googlebot)

        # Extra security headers for Googlebot
        if googlebot:
            rand_octet3 = random.randint(64, 95)
            rand_octet4 = random.randint(1, 254)
            headers["X-Forwarded-For"] = (
                f"66.249.{rand_octet3}.{rand_octet4}"  # Google IP range
            )
            headers["Via"] = "1.1 google"

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            # Add jitter (random delay 0.3-1.2s)
            await asyncio.sleep(random.uniform(0.3, 1.2))
            resp = await client.get(url, headers=headers)

            if resp.status_code == 200 and len(resp.text) > 500:
                return resp.text
            elif resp.status_code == 403:
                logger.info(f"[STEALTH] 403 on {url} with {mobile=} {googlebot=}")
                return None
            else:
                logger.info(f"[STEALTH] {resp.status_code} on {url}")
                return None

    async def fetch_google_cache(
        self, url: str, timeout: float = 30.0
    ) -> str | None:
        """Fetch page from Google Cache (bypasses Cloudflare entirely)."""
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        try:
            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True
            ) as client:
                resp = await client.get(cache_url, headers=headers)
                if resp.status_code == 200 and len(resp.text) > 1000:
                    logger.info(f"[STEALTH] Google Cache success for {url}")
                    return resp.text
        except Exception as e:
            logger.warning(f"[STEALTH] Google Cache failed for {url}: {e}")
        return None

    # ── PORTED FROM CHRONOS ──────────────────────────────────────────────────

    def bypass_cloudflare(self) -> dict[str, str]:
        """[PORTED FROM CHRONOS] Headers to pass Cloudflare protection."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "TE": "trailers",
        }

    def extract_email_patterns(self, text: str) -> list[str]:
        """[PORTED FROM CHRONOS] Find emails even when obfuscated."""
        emails = []

        # Standard email pattern
        standard = re.findall(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", text
        )
        emails.extend(standard)

        # "name [at] company [dot] com"
        obfuscated1 = re.findall(
            r"\b[\w.+-]+\s*\[at\]\s*[\w.-]+\s*\[dot\]\s*\w+\b", text, re.IGNORECASE
        )
        for email in obfuscated1:
            emails.append(
                email.replace("[at]", "@").replace("[dot]", ".").replace(" ", "")
            )

        # "name (at) company (dot) com"
        obfuscated2 = re.findall(
            r"\b[\w.+-]+\s*\(at\)\s*[\w.-]+\s*\(dot\)\s*\w+\b", text, re.IGNORECASE
        )
        for email in obfuscated2:
            emails.append(
                email.replace("(at)", "@").replace("(dot)", ".").replace(" ", "")
            )

        # "name @ company . com" (with spaces)
        spaced = re.findall(r"\b[\w.+-]+\s*@\s*[\w.-]+\s*\.\s*\w+\b", text)
        for email in spaced:
            emails.append(email.replace(" ", ""))

        return list(set(emails))

    def get_session_cookies(self) -> dict[str, str]:
        """[PORTED FROM CHRONOS] Generate realistic session cookies."""
        session_id = hashlib.md5(str(time.time()).encode()).hexdigest()
        return {
            "session_id": session_id,
            "_ga": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
            "_gid": f"GA1.2.{random.randint(100000000, 999999999)}.{int(time.time())}",
            "_gat": "1",
        }

    def rotate_identity(self):
        """[PORTED FROM CHRONOS] Rotate complete browser identity."""
        self.user_agents = self._load_user_agents()
        self.fingerprints = self._generate_fingerprints()
        self.request_count = 0
        logger.info("Identity rotated — new browser fingerprint")

    def smart_retry(self, func, max_retries: int = 3, backoff_factor: float = 2.0):
        """[PORTED FROM CHRONOS] Retry with exponential backoff + jitter."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                delay = backoff_factor**attempt + random.uniform(
                    0, 0.3 * backoff_factor**attempt
                )
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} failed, retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
        return None


class AntiDetectionTricks:
    """[PORTED FROM CHRONOS] Advanced anti-detection techniques."""

    @staticmethod
    def randomize_request_order(urls: list[str]) -> list[str]:
        """Don't scrape in predictable order."""
        shuffled = urls.copy()
        random.shuffle(shuffled)
        return shuffled

    @staticmethod
    def add_noise_requests(
        target_urls: list[str], noise_ratio: float = 0.2
    ) -> list[str]:
        """Add random 'decoy' requests to hide pattern."""
        noise_urls = [
            "https://www.google.com",
            "https://www.linkedin.com",
            "https://www.indeed.com",
            "https://www.glassdoor.com",
        ]
        num_noise = int(len(target_urls) * noise_ratio)
        combined = target_urls + random.choices(noise_urls, k=num_noise)
        random.shuffle(combined)
        return combined

    @staticmethod
    def mimic_human_scrolling():
        """Return scroll delays that simulate human behavior."""
        return [
            random.uniform(0.5, 1.5),
            random.uniform(1.0, 2.0),
            random.uniform(0.3, 0.8),
        ]

    @staticmethod
    def detect_honeypot(html: str) -> bool:
        """Detect if page contains honeypot elements for scrapers."""
        indicators = [
            "display:none",
            "visibility:hidden",
            "position:absolute;left:-9999px",
            "opacity:0",
        ]
        for indicator in indicators:
            if indicator in html.lower():
                logger.warning("Honeypot detected on page")
                return True
        return False


class NodriverFallback:
    """
    [TIER 2 STEALTH] Browser Automation Fallback.
    Used when curl_cffi hits a strong challenge (like Turnstile).
    """

    @staticmethod
    async def get_page_content(url: str, proxy: str | None = None, timeout_seconds: int = 20) -> str:
        try:
            import asyncio
            import os

            import nodriver as uc

            from core.human_mouse import HumanMouse

            if not proxy:
                env_proxies = [p.strip() for p in os.getenv("RESIDENTIAL_PROXIES", "").split(",") if p.strip()]
                if env_proxies:
                    proxy = env_proxies[0]
                else:
                    proxy = "http://jobhunt-stub-proxy:8080"

            browser_args = []
            if proxy:
                browser_args.append(f"--proxy-server={proxy}")

            # On some environments headless=True may be detected, but usually Nodriver handles it well
            browser = await uc.start(headless=True, browser_args=browser_args)
            page = await browser.get(url)

            # Inject WebGL, Canvas, and browser attribute stealth spoofing scripts
            js_script = """
            (function() {
                // WebGL Spoofing
                if (window.WebGLRenderingContext) {
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) return 'Intel Inc.';
                        if (parameter === 37446) return 'Intel(R) UHD Graphics';
                        return getParameter.apply(this, arguments);
                    };
                }
                // Canvas Spoofing
                if (window.CanvasRenderingContext2D) {
                    const getImageData = CanvasRenderingContext2D.prototype.getImageData;
                    CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
                        const imageData = getImageData.apply(this, arguments);
                        if (imageData.data.length > 0) {
                            imageData.data[0] = (imageData.data[0] + 1) % 256;
                        }
                        return imageData;
                    };
                }
                // Browser Attribute Spoofing
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            })();
            """
            try:
                await page.evaluate(js_script)
            except Exception as eval_err:
                logger.warning(f"[Nodriver] Failed to evaluate stealth script: {eval_err}")

            # Execute human mouse simulation events
            try:
                await HumanMouse.simulate_mouse_movement(page, 10, 10, 500, 400)
            except Exception as mouse_err:
                logger.warning(f"[Nodriver] Failed to simulate mouse movement: {mouse_err}")

            await asyncio.sleep(5)  # Wait for Cloudflare/JS
            html = await page.get_content()
            browser.stop()
            return html
        except Exception as e:
            logger.error(f"[Nodriver] Fallback failed for {url}: {e}")
            return ""


class ApexCamoufoxFallback:
    """
    [THE APEX TIER 3 STEALTH] C++ Engine-Level Firefox Modification.
    Completely replaces Nodriver when maximum stealth is needed.
    """

    @staticmethod
    async def get_page_content(url: str, proxy: str | None = None) -> str:
        try:
            import asyncio
            import os

            from camoufox.async_api import AsyncCamoufox

            from core.human_mouse import HumanMouse

            if not proxy:
                env_proxies = [p.strip() for p in os.getenv("RESIDENTIAL_PROXIES", "").split(",") if p.strip()]
                if env_proxies:
                    proxy = env_proxies[0]
                else:
                    proxy = "http://jobhunt-stub-proxy:8080"

            # Using Camoufox which intercepts and overrides WebGL/Canvas natively
            async with AsyncCamoufox(headless=True, proxy=proxy) as browser:
                page = await browser.new_page()
                await page.goto(url)

                # Simulate human interaction before extraction
                # Move from an arbitrary start point to an arbitrary center point
                await HumanMouse.simulate_mouse_movement(page, 10, 10, 500, 400)

                await asyncio.sleep(4)  # Allow Datadome to track the mouse movement
                html = await page.content()
                return html
        except ImportError:
            logger.error("[Apex] Camoufox not installed. Please pip install camoufox")
            return ""
        except Exception as e:
            logger.error(f"[Apex] Camoufox Fallback failed for {url}: {e}")
            return ""


# Global instance
stealth = StealthScraper()

