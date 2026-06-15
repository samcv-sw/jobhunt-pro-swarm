"""
STEALTH SCRAPING TECHNIQUES
Ported from Rita Project - Advanced anti-detection methods
"""

import random
import time
import hashlib
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class StealthScraper:
    """Advanced scraping techniques to avoid detection."""
    
    def __init__(self):
        self.request_count = 0
        self.last_request_time = 0
        self.user_agents = self._load_user_agents()
        self.fingerprints = self._generate_fingerprints()
    
    def _load_user_agents(self) -> List[str]:
        """Real browser fingerprints from around the world"""
        return [
            # Chrome Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            
            # Safari Mac
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            
            # Firefox Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            
            # Edge
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            
            # Mobile iPhone
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            
            # Mobile Android
            "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
        ]
    
    def _generate_fingerprints(self) -> List[Dict]:
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
    
    def get_random_fingerprint(self) -> Dict:
        """Get a random browser fingerprint"""
        return random.choice(self.fingerprints)
    
    def get_headers(self) -> Dict[str, str]:
        """Get realistic browser headers"""
        fingerprint = self.get_random_fingerprint()
        
        headers = {
            "User-Agent": self.get_random_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
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
                import asyncio
                await asyncio.sleep(delay)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def should_rotate_ip(self) -> bool:
        """Decide if we should rotate IP (for proxy users)"""
        # Rotate every 50 requests
        return self.request_count % 50 == 0
    
    def get_request_fingerprint(self) -> str:
        """Generate unique fingerprint for this request"""
        data = f"{time.time()}{random.random()}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def get_canvas_spoofing_script(self) -> str:
        """[RUSSIAN STEALTH] Injectable JS to spoof Canvas fingerprint"""
        noise = random.randint(1, 5)
        return f"""
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {{
            const context = originalGetContext.apply(this, arguments);
            if (type === '2d') {{
                const originalGetImageData = context.getImageData;
                context.getImageData = function() {{
                    const imageData = originalGetImageData.apply(this, arguments);
                    for (let i = 0; i < imageData.data.length; i += 4) {{
                        imageData.data[i] = imageData.data[i] ^ {noise};
                    }}
                    return imageData;
                }};
            }}
            return context;
        }};
        """

    def get_webgl_spoofing_script(self) -> str:
        """[RUSSIAN STEALTH] Injectable JS to spoof WebGL vendor/renderer"""
        vendors = ["Google Inc. (Apple)", "Intel Inc.", "AMD", "NVIDIA Corporation"]
        renderers = ["ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)", "Intel Iris OpenGL Engine", "AMD Radeon Pro 5300M OpenGL Engine", "NVIDIA GeForce RTX 4090"]
        return f"""
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) return '{random.choice(vendors)}'; // UNMASKED_VENDOR_WEBGL
            if (parameter === 37446) return '{random.choice(renderers)}'; // UNMASKED_RENDERER_WEBGL
            return getParameter.apply(this, arguments);
        }};
        """

    # ── PORTED FROM CHRONOS ──────────────────────────────────────────────────

    def bypass_cloudflare(self) -> Dict[str, str]:
        """[PORTED FROM CHRONOS] Headers to pass Cloudflare protection."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "TE": "trailers",
        }

    def extract_email_patterns(self, text: str) -> List[str]:
        """[PORTED FROM CHRONOS] Find emails even when obfuscated."""
        emails = []

        # Standard email pattern
        standard = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        emails.extend(standard)

        # "name [at] company [dot] com"
        obfuscated1 = re.findall(r'\b[\w.+-]+\s*\[at\]\s*[\w.-]+\s*\[dot\]\s*\w+\b', text, re.IGNORECASE)
        for email in obfuscated1:
            emails.append(email.replace('[at]', '@').replace('[dot]', '.').replace(' ', ''))

        # "name (at) company (dot) com"
        obfuscated2 = re.findall(r'\b[\w.+-]+\s*\(at\)\s*[\w.-]+\s*\(dot\)\s*\w+\b', text, re.IGNORECASE)
        for email in obfuscated2:
            emails.append(email.replace('(at)', '@').replace('(dot)', '.').replace(' ', ''))

        # "name @ company . com" (with spaces)
        spaced = re.findall(r'\b[\w.+-]+\s*@\s*[\w.-]+\s*\.\s*\w+\b', text)
        for email in spaced:
            emails.append(email.replace(' ', ''))

        return list(set(emails))

    def get_session_cookies(self) -> Dict[str, str]:
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
                delay = backoff_factor ** attempt + random.uniform(0, 0.3 * backoff_factor ** attempt)
                logger.warning(f"Retry {attempt + 1}/{max_retries} failed, retrying in {delay:.1f}s...")
                time.sleep(delay)
        return None


class AntiDetectionTricks:
    """[PORTED FROM CHRONOS] Advanced anti-detection techniques."""

    @staticmethod
    def randomize_request_order(urls: List[str]) -> List[str]:
        """Don't scrape in predictable order."""
        shuffled = urls.copy()
        random.shuffle(shuffled)
        return shuffled

    @staticmethod
    def add_noise_requests(target_urls: List[str], noise_ratio: float = 0.2) -> List[str]:
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
        return [random.uniform(0.5, 1.5), random.uniform(1.0, 2.0), random.uniform(0.3, 0.8)]

    @staticmethod
    def detect_honeypot(html: str) -> bool:
        """Detect if page contains honeypot elements for scrapers."""
        indicators = ["display:none", "visibility:hidden", "position:absolute;left:-9999px", "opacity:0"]
        for indicator in indicators:
            if indicator in html.lower():
                logger.warning("Honeypot detected on page")
                return True
        return False


# Global instance
stealth = StealthScraper()
